"""
Unit tests for Eyes on Tigers (EoT) data integrity and schema validation
"""
import pytest
import os
import sys
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from utils.data_loader import load_reserves, load_synthetic_patrols, load_tsi_scores

def test_reserves_integrity():
    reserves_df = load_reserves()
    assert not reserves_df.empty, "Reserves dataset must not be empty"
    assert len(reserves_df) >= 50, f"Expected at least 50 Tiger Reserves, got {len(reserves_df)}"
    
    # Check geographical coordinate bounds for Indian subcontinent
    assert reserves_df["latitude"].between(8.0, 35.0).all(), "Latitudes must lie within India bounds (8° - 35° N)"
    assert reserves_df["longitude"].between(68.0, 98.0).all(), "Longitudes must lie within India bounds (68° - 98° E)"
    assert (reserves_df["core_area_km2"] > 0).all(), "Core area must be strictly positive"

def test_synthetic_patrols_bounds():
    patrols_df = load_synthetic_patrols()
    assert not patrols_df.empty, "Synthetic patrols dataset must not be empty"
    assert "patrol_coverage_ratio" in patrols_df.columns, "patrol_coverage_ratio must be present"
    assert patrols_df["patrol_coverage_ratio"].between(0.0, 1.0).all(), "Coverage ratio must be in [0, 1]"
    assert (patrols_df["intervention_latency_mins"] > 0).all(), "Intervention latency must be positive"

def test_tsi_scores_bounds():
    tsi_df = load_tsi_scores()
    assert not tsi_df.empty, "TSI scores dataset must not be empty"
    assert "tsi_score" in tsi_df.columns, "TSI score column must be present"
    assert tsi_df["tsi_score"].between(0.0, 100.0).all(), "TSI scores must be normalized between 0 and 100"
    assert tsi_df["tsi_score"].isnull().sum() == 0, "TSI scores must not contain NaN values"

def test_health_check_module():
    from scripts.health_check import ping_endpoint
    # Test ping with invalid host handles errors gracefully without unhandled exception
    res = ping_endpoint("http://127.0.0.1:59999", timeout=1)
    assert res["status"] in ("UNREACHABLE", "HTTP_ERROR", "EXCEPTION")
    assert "latency_ms" in res
