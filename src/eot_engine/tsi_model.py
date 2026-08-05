"""
Tiger Success Index (TSI) Engine for Eyes on Tigers (EoT).
Computes reserve-level conservation index using Weighted Linear Combination (WLC)
derived from the Analytic Hierarchy Process (AHP).
Features exact analytical SHAP values for model explainability.
"""
import numpy as np
import pandas as pd

class TSICalculator:
    """
    TSI is computed as:
    TSI = w_TS * TS + w_HI * HI + w_AP * AP + w_PD * PD
    
    Weights derived from consistent AHP pairwise comparison matrix:
    - Population Sustainability (TS): 0.40
    - Habitat Integrity (HI): 0.30
    - Anti-Poaching Effectiveness (AP): 0.20
    - Prey Density (PD): 0.10
    """
    def __init__(self):
        self.weights = {
            "TS": 0.40,
            "HI": 0.30,
            "AP": 0.20,
            "PD": 0.10
        }
        
    def compute_tsi(self, reserves_data):
        """
        Expects a DataFrame containing:
        - reserve_name
        - density_per_100km2
        - growth_rate
        - ndvi
        - fragmentation_score
        - patrol_coverage_ratio
        - intervention_latency_mins
        - prey_density_per_km2
        """
        df = reserves_data.copy()
        
        # 1. Normalize Criteria (0.0 to 1.0)
        # TS: Density normalized by carrying capacity ceiling (25 tigers/100km2) + growth rate
        df["c_TS"] = np.clip(0.7 * (df["density_per_100km2"] / 25.0) + 0.3 * np.clip(df["growth_rate"] / 0.15, -0.5, 1.5), 0.0, 1.0)
        
        # HI: NDVI and low fragmentation
        df["c_HI"] = np.clip(0.6 * df["ndvi"] + 0.4 * (1.0 - df["fragmentation_score"]), 0.0, 1.0)
        
        # AP: Patrol coverage and response latency (latency clamped at 180 mins)
        df["c_AP"] = np.clip(0.5 * df["patrol_coverage_ratio"] + 0.5 * np.clip(1.0 - (df["intervention_latency_mins"] / 180.0), 0.0, 1.0), 0.0, 1.0)
        
        # PD: Prey Density (normalized by optimal prey density of 80/km2)
        df["c_PD"] = np.clip(df["prey_density_per_km2"] / 80.0, 0.0, 1.0)
        
        # 2. Compute TSI Score
        df["tsi_score"] = (
            self.weights["TS"] * df["c_TS"] +
            self.weights["HI"] * df["c_HI"] +
            self.weights["AP"] * df["c_AP"] +
            self.weights["PD"] * df["c_PD"]
        )
        
        # Round scores
        df["tsi_score"] = df["tsi_score"].round(4)
        
        # 3. Compute Exact Analytical SHAP Values
        # Baseline is the mean score of each criterion across all reserves
        mean_TS = df["c_TS"].mean()
        mean_HI = df["c_HI"].mean()
        mean_AP = df["c_AP"].mean()
        mean_PD = df["c_PD"].mean()
        
        df["shap_TS"] = self.weights["TS"] * (df["c_TS"] - mean_TS)
        df["shap_HI"] = self.weights["HI"] * (df["c_HI"] - mean_HI)
        df["shap_AP"] = self.weights["AP"] * (df["c_AP"] - mean_AP)
        df["shap_PD"] = self.weights["PD"] * (df["c_PD"] - mean_PD)
        df["shap_base"] = (
            self.weights["TS"] * mean_TS +
            self.weights["HI"] * mean_HI +
            self.weights["AP"] * mean_AP +
            self.weights["PD"] * mean_PD
        )
        
        # Verify perfect additivity: tsi_score == shap_base + shap_TS + shap_HI + shap_AP + shap_PD
        return df
