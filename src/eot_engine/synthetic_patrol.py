"""
Synthetic Patrol Log Generator for Eyes on Tigers (EoT).
Simulates ranger patrol trajectories, threat hotspots, and intervention latencies
using spatial inhomogeneous Poisson Point Processes (PPP) to bypass government data classification constraints.
"""
import numpy as np
import pandas as pd

np.random.seed(42)

def simulate_reserve_patrols(reserve_name, center_lat, center_lon, num_camps=3, num_patrols=20):
    """
    Simulate patrol trajectories and intervention latencies for a reserve.
    - Patrol camps are placed around the reserve center.
    - Poaching threats are generated using an inhomogeneous Poisson Point Process, 
      peaking at the reserve boundary (outer ring).
    - Patrols are generated as biased random walks from camps.
    """
    # 1. Establish ranger camps (lat, lon)
    camp_offsets = np.random.uniform(-0.06, 0.06, size=(num_camps, 2))
    camps = np.array([center_lat, center_lon]) + camp_offsets
    
    # 2. Inhomogeneous Poisson Point Process for threat locations (poaching risk)
    # The intensity lambda(x, y) peaks at an outer boundary ring (radius r ~ 0.08 degrees)
    r_boundary = 0.08
    sigma_boundary = 0.015
    
    # Generate potential threat points and filter them using rejection sampling
    candidate_points = np.random.uniform(-0.12, 0.12, size=(500, 2)) + np.array([center_lat, center_lon])
    threats = []
    
    for pt in candidate_points:
        dist_to_center = np.linalg.norm(pt - np.array([center_lat, center_lon]))
        # Inhomogeneous intensity function
        intensity = np.exp(-((dist_to_center - r_boundary) ** 2) / (2 * (sigma_boundary ** 2)))
        # Rejection sampling
        if np.random.rand() < intensity:
            threats.append(pt)
            
    threats = np.array(threats)
    if len(threats) == 0: # Fallback
        threats = np.array([[center_lat + 0.08, center_lon + 0.08]])
        
    # 3. Simulate ranger patrols
    patrol_logs = []
    
    for i in range(num_patrols):
        camp_idx = i % num_camps
        start_point = camps[camp_idx]
        
        # Biased random walk (10 steps) wandering towards the boundary and back
        trajectory = [start_point]
        curr_point = start_point
        for step in range(10):
            # Biased walk towards the center or border
            step_dir = np.random.uniform(-0.02, 0.02, size=2)
            curr_point = curr_point + step_dir
            trajectory.append(curr_point)
            
        trajectory = np.array(trajectory)
        
        # 4. Compute Intervention Latency for a random threat coordinate near this patrol
        # Draw a threat coordinate
        threat_pt = threats[np.random.choice(len(threats))]
        # Distance in km approx (1 degree lat/lon is ~111 km)
        dist_km = np.linalg.norm(threat_pt - start_point) * 111.0
        # Ranger response model: 5 km/hr patrol speed + random dispatch delay
        response_speed = 5.0 # km/hr
        dispatch_delay = np.random.uniform(10.0, 45.0) # minutes
        latency_mins = (dist_km / response_speed) * 60.0 + dispatch_delay
        
        # Patrol stats
        indicators_found = np.random.choice([0, 1, 2], p=[0.75, 0.20, 0.05])
        coverage_fraction = np.clip(0.3 + 0.1 * indicators_found + np.random.normal(0, 0.08), 0.1, 0.95)
        
        patrol_logs.append({
            "patrol_id": f"PAT-{reserve_name[:3].upper()}-{2026}-{i:03d}",
            "reserve_name": reserve_name,
            "camp_id": f"CAMP-{camp_idx + 1}",
            "camp_latitude": start_point[0],
            "camp_longitude": start_point[1],
            "threat_latitude": threat_pt[0],
            "threat_longitude": threat_pt[1],
            "trajectory_points": trajectory.tolist(), # List of [lat, lon]
            "intervention_latency_mins": round(latency_mins, 1),
            "patrol_coverage_ratio": round(coverage_fraction, 3),
            "poaching_indicators_detected": int(indicators_found)
        })
        
    return pd.DataFrame(patrol_logs)

def generate_national_synthetic_patrols(reserves_df, num_patrols_per_reserve=15):
    """
    Generate synthetic patrol data for all reserves in the dataset.
    """
    all_logs = []
    for _, r in reserves_df.iterrows():
        name = r["reserve_name"]
        lat = r["latitude"]
        lon = r["longitude"]
        all_logs.append(simulate_reserve_patrols(name, lat, lon, num_patrols=num_patrols_per_reserve))
        
    return pd.concat(all_logs, ignore_index=True)
