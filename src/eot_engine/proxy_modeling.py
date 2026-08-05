"""
Proxy Modeling & Feature Augmentation Engine for Eyes on Tigers (EoT).
Interpolates continuous yearly tiger population densities from sparse 4-year census data
by training regression models on yearly satellite indicators (NDVI, NDBI, LST) and Prey Density.
"""
import numpy as np
import pandas as pd
from scipy.interpolate import pchip_interpolate

# Set seed for reproducibility
np.random.seed(42)

def generate_reserve_proxies(reserve_name, core_area, growth_profile, years):
    """
    Generate simulated yearly ecological indicators for a reserve.
    These mimic Google Earth Engine (GEE) satellite pulls and prey census estimates.
    """
    records = []
    
    # Establish base indicators based on growth profiles
    if growth_profile in ("strong", "recovery"):
        base_ndvi = 0.65
        ndvi_trend = 0.005 # Greenup over years
        base_ndbi = -0.30
        ndbi_trend = -0.004 # Decreasing human footprint
        base_prey = 35.0
        prey_trend = 1.2
    elif growth_profile == "moderate":
        base_ndvi = 0.60
        ndvi_trend = 0.002
        base_ndbi = -0.20
        ndbi_trend = -0.002
        base_prey = 25.0
        prey_trend = 0.6
    else: # weak, decline, new
        base_ndvi = 0.55
        ndvi_trend = -0.003 # Forest degradation
        base_ndbi = -0.10
        ndbi_trend = 0.006 # Increasing human encroachment
        base_prey = 18.0
        prey_trend = -0.4
        
    for yr in years:
        idx = yr - 2006
        # Add random walks to trends to simulate natural variability
        ndvi = float(np.clip(base_ndvi + ndvi_trend * idx + np.random.normal(0, 0.015), 0.1, 1.0))
        ndbi = float(np.clip(base_ndbi + ndbi_trend * idx + np.random.normal(0, 0.02), -1.0, 1.0))
        # Land Surface Temperature (LST) centered around 300K with seasonal/annual fluctuations
        lst = float(298.15 + 0.1 * idx + np.random.normal(0, 1.5))
        prey_density = float(np.clip(base_prey + prey_trend * idx + np.random.normal(0, 2.0), 2.0, 120.0))
        
        records.append({
            "reserve_name": reserve_name,
            "year": yr,
            "ndvi": round(ndvi, 3),
            "ndbi": round(ndbi, 3),
            "lst_k": round(lst, 2),
            "prey_density_per_km2": round(prey_density, 2)
        })
        
    return records

class TigerProxyRegressor:
    """
    Fits regression mapping [NDVI, NDBI, LST, Prey] -> Tiger Density
    using census years, and estimates densities for non-census years.
    """
    def __init__(self):
        self.weights = None
        self.intercept = 0.0
        
    def fit(self, X, y):
        # Fit a robust linear regression model analytically using ordinary least squares (OLS)
        # X: (N, 4) matrix, y: (N,) vector of densities
        X_design = np.hstack([np.ones((X.shape[0], 1)), X])
        try:
            beta = np.linalg.pinv(X_design.T @ X_design) @ X_design.T @ y
            self.intercept = float(beta[0])
            self.weights = beta[1:]
        except Exception:
            # Fallback weights if matrix singular
            self.weights = np.array([5.0, -2.0, -0.01, 0.1])
            self.intercept = 0.1
            
    def predict(self, X):
        if self.weights is None:
            return np.ones(X.shape[0]) * 0.5
        return np.dot(X, self.weights) + self.intercept

def build_proxy_census_timeline(census_df, reserves_df, reserve_growth_profiles):
    """
    Trains the regressor and generates yearly predictions for all years from 2006 to 2030.
    """
    years_all = list(range(2006, 2031))
    census_years = [2006, 2010, 2014, 2018, 2022]
    
    # 1. Generate all yearly proxies
    all_proxies = []
    for _, r in reserves_df.iterrows():
        name = r["reserve_name"]
        core = r["core_area_km2"]
        profile = reserve_growth_profiles.get(name, "moderate")
        all_proxies.extend(generate_reserve_proxies(name, core, profile, years_all))
        
    proxies_df = pd.DataFrame(all_proxies)
    
    # 2. Extract training data (Census years)
    train_records = []
    for _, row in census_df.iterrows():
        r_name = row["reserve_name"]
        yr = int(row["year"])
        pop = row["population"]
        
        # Get reserve core area
        r_info = reserves_df[reserves_df["reserve_name"] == r_name]
        if r_info.empty:
            continue
        core_area = r_info.iloc[0]["core_area_km2"]
        density = pop / max(core_area, 1.0) * 100.0 # Tigers per 100 km2
        
        proxy_row = proxies_df[(proxies_df["reserve_name"] == r_name) & (proxies_df["year"] == yr)]
        if proxy_row.empty:
            continue
            
        train_records.append({
            "ndvi": proxy_row.iloc[0]["ndvi"],
            "ndbi": proxy_row.iloc[0]["ndbi"],
            "lst_k": proxy_row.iloc[0]["lst_k"],
            "prey_density": proxy_row.iloc[0]["prey_density_per_km2"],
            "density": density
        })
        
    train_df = pd.DataFrame(train_records)
    
    # Fit the regressor
    reg = TigerProxyRegressor()
    if not train_df.empty:
        X_train = train_df[["ndvi", "ndbi", "lst_k", "prey_density"]].values
        y_train = train_df["density"].values
        reg.fit(X_train, y_train)
    
    # 3. Predict densities and populations for all years
    interpolated_records = []
    for _, r in reserves_df.iterrows():
        r_name = r["reserve_name"]
        core_area = r["core_area_km2"]
        
        # Pull yearly proxies
        r_proxies = proxies_df[proxies_df["reserve_name"] == r_name].sort_values("year")
        X_pred = r_proxies[["ndvi", "ndbi", "lst_k", "prey_density_per_km2"]].values
        
        pred_densities = reg.predict(X_pred)
        # Apply lower bounds to prevent negative populations
        pred_densities = np.clip(pred_densities, 0.0, 35.0)
        
        for idx, row in r_proxies.iterrows():
            yr = int(row["year"])
            pred_density = pred_densities[len(interpolated_records) % len(years_all)]
            
            # Census anchor override to match official figures exactly on census years
            anchor_match = census_df[(census_df["reserve_name"] == r_name) & (census_df["year"] == yr)]
            if not anchor_match.empty:
                pop_est = int(anchor_match.iloc[0]["population"])
                density_est = pop_est / max(core_area, 1.0) * 100.0
            else:
                pop_est = int(round(pred_density * core_area / 100.0))
                density_est = pred_density
                
            interpolated_records.append({
                "reserve_name": r_name,
                "year": yr,
                "ndvi": row["ndvi"],
                "ndbi": row["ndbi"],
                "lst_k": row["lst_k"],
                "prey_density_per_km2": row["prey_density_per_km2"],
                "density_per_100km2": round(density_est, 4),
                "population": max(0, pop_est)
            })
            
    return pd.DataFrame(interpolated_records), reg
