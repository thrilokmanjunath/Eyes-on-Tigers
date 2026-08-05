import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.map_utils import (GLOBAL_CSS, stat_card, stat_card_mini, section_header,
                              page_header, apply_dark_layout, divider,
                              ACCENT, ACCENT_LIGHT, ALERT, PRIMARY, SUCCESS, INFO, MUTED_TEXT, TEXT_COLOR)
from utils.data_loader import (load_reserves, load_synthetic_patrols, load_tsi_scores, load_yearly_proxies)

# Apply global premium styling
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.markdown(page_header(
    "Ecosystem Integrity & Patrol Explorer",
    "Interact with simulated Computer Vision feeds, analyze Poisson simulated anti-poaching patrols, and explore AHP-derived TSI scores.",
    "🛡️"
), unsafe_allow_html=True)

reserves_df = load_reserves()
patrols_df = load_synthetic_patrols()
tsi_df = load_tsi_scores()
proxies_df = load_yearly_proxies()

if not reserves_df.empty and not patrols_df.empty and not tsi_df.empty:
    tab_cv, tab_patrol, tab_tsi = st.tabs([
        "📸  Module A: Computer Vision", 
        "🛰️  Module C: Patrol Optimization", 
        "📊  Module D: TSI & SHAP Explainability"
    ])
    
    # ── TAB 1: COMPUTER VISION ──
    with tab_cv:
        st.markdown(section_header("Module A: Camera-Trap Vision Systems", 
            "Dual-Pipeline Testing on Labeled Tigers in the Wild (LTW) & Snapshot Serengeti Benchmarks"), 
            unsafe_allow_html=True)
            
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.markdown("""
            ### Image Classification & Re-Identification Pipeline
            To protect classified NTCA core-zone coordinates, our system evaluates computer vision models on open-source datasets:
            - **Labeled Tigers in the Wild (LTW):** Used for individual re-identification by matching unique stripe patterns.
            - **Snapshot Serengeti:** Used to train multi-species detection models (Tigers, Leopards, Prey species) to handle high-occlusion environments.
            """)
            
            sel_res = st.selectbox("Select Reserve to Test Feed", reserves_df["reserve_name"].tolist(), key="cv_res")
            mock_cams = [f"CAM-{sel_res[:3].upper()}-01", f"CAM-{sel_res[:3].upper()}-02", f"CAM-{sel_res[:3].upper()}-03"]
            sel_cam = st.selectbox("Select Active Camera Trap", mock_cams)
            
            run_cv = st.button("Trigger AI Inference Pipeline", use_container_width=True)
            
        with c_right:
            st.markdown("### Active Camera Frame Diagnostics")
            if run_cv:
                # Deterministic details based on camera name
                np.random.seed(hash(sel_cam) % 1000)
                detection = np.random.choice(["Tiger (Panthera tigris)", "Leopard (Panthera pardus)", "Sambar Deer (Rusa unicolor)", "No Animal Detected"], p=[0.5, 0.15, 0.25, 0.10])
                confidence = np.random.uniform(92.4, 99.8) if detection != "No Animal Detected" else 0.0
                
                if "Tiger" in detection:
                    individual_id = f"T-104_{np.random.choice(['Male', 'Female'])}"
                    match_score = np.random.uniform(95.0, 99.5)
                    alert_class = ALERT
                    status_text = f"🔥 ALERT: Critical match found! Individual {individual_id} identified."
                elif "Leopard" in detection or "Deer" in detection:
                    individual_id = "N/A (Species Level Only)"
                    match_score = 0.0
                    alert_class = INFO
                    status_text = "🟢 Status: Standard ecological wildlife logging."
                else:
                    individual_id = "N/A"
                    match_score = 0.0
                    alert_class = MUTED_TEXT
                    status_text = "⚪ Status: Idle frame."
                
                # Mock bounding box visualization using HTML/CSS
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #0f172a, #1e293b); border:1px solid {alert_class}33; border-radius:12px; padding:20px; position:relative;">
                    <div style="width:100%; height:200px; background:rgba(0,0,0,0.3); border-radius:8px; display:flex; align-items:center; justify-content:center; position:relative; overflow:hidden; border:2px dashed {alert_class}44;">
                        <span style="font-size:4rem; opacity:0.15;">🐯</span>
                        {f'<div style="position:absolute; border:2px solid {alert_class}; top:30px; left:60px; width:150px; height:120px; box-shadow:0 0 10px {alert_class}55; display:flex; flex-direction:column; justify-content:space-between; padding:4px;">'
                         f'<span style="background:{alert_class}; color:#ffffff; font-size:0.6rem; font-weight:700; padding:1px 4px; align-self:flex-start; border-radius:2px;">{detection} {confidence:.1f}%</span>'
                         f'</div>' if confidence > 0 else ''}
                    </div>
                    <div style="margin-top:16px;">
                        <p style="margin:0; font-size:0.9rem; color:{TEXT_COLOR};"><strong>Match Diagnostics:</strong></p>
                        <p style="margin:4px 0 0 0; font-size:0.82rem; color:{MUTED_TEXT};">{status_text}</p>
                        <ul style="margin:8px 0 0 0; padding-left:20px; font-size:0.8rem; color:{MUTED_TEXT};">
                            <li><strong>Detected Class:</strong> {detection}</li>
                            <li><strong>AI Confidence:</strong> {f"{confidence:.2f}%" if confidence > 0 else "N/A"}</li>
                            <li><strong>Stripe Match ID:</strong> {individual_id}</li>
                            {f"<li><strong>Stripe Pattern Score:</strong> {match_score:.1f}%</li>" if match_score > 0 else ""}
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Select a camera trap and click 'Trigger AI Inference Pipeline' to run wildlife identification.")

    # ── TAB 2: PATROL OPTIMIZATION ──
    with tab_patrol:
        st.markdown(section_header("Module C: Anti-Poaching Patrol Simulator", 
            "Spatial Poisson Point Process Threat Hotspots and Ranger Trajectory Overlay"), 
            unsafe_allow_html=True)
            
        p_res = st.selectbox("Select Target Tiger Reserve", reserves_df["reserve_name"].tolist(), key="patrol_res")
        
        # Filter patrols for this reserve
        res_patrols = patrols_df[patrols_df["reserve_name"] == p_res]
        
        if not res_patrols.empty:
            # Stats for this reserve
            avg_latency = res_patrols["intervention_latency_mins"].mean()
            avg_coverage = res_patrols["patrol_coverage_ratio"].mean() * 100.0
            total_indicators = res_patrols["poaching_indicators_detected"].sum()
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(stat_card_mini("Avg Intervention Latency", f"{avg_latency:.1f} mins", ALERT if avg_latency > 90 else SUCCESS), unsafe_allow_html=True)
            with c2:
                st.markdown(stat_card_mini("Avg Patrol Coverage", f"{avg_coverage:.1f}%", SUCCESS if avg_coverage > 60 else INFO), unsafe_allow_html=True)
            with c3:
                st.markdown(stat_card_mini("Poaching Snares Found", f"{total_indicators} Snares", INFO if total_indicators < 5 else ALERT), unsafe_allow_html=True)
                
            st.markdown(f'<div style="height:10px;"></div>', unsafe_allow_html=True)
            
            # Patrol Selector
            patrol_ids = res_patrols["patrol_id"].tolist()
            sel_patrol_id = st.selectbox("Select Simulated Patrol Path to View", patrol_ids)
            pat_row = res_patrols[res_patrols["patrol_id"] == sel_patrol_id].iloc[0]
            
            # Mapbox plots
            # Build threats points
            threats_data = []
            for idx, r in res_patrols.iterrows():
                threats_data.append({
                    "latitude": r["threat_latitude"],
                    "longitude": r["threat_longitude"],
                    "type": "Poaching Threat Hotspot (PPP Simulated)",
                    "color": "#EF4444",
                    "size": 8
                })
            
            # Build camp points
            camps_data = []
            unique_camps = res_patrols.drop_duplicates(subset=["camp_id"])
            for idx, r in unique_camps.iterrows():
                camps_data.append({
                    "latitude": r["camp_latitude"],
                    "longitude": r["camp_longitude"],
                    "type": f"Ranger Camp ({r['camp_id']})",
                    "color": "#3B82F6",
                    "size": 14
                })
                
            map_pts = pd.DataFrame(threats_data + camps_data)
            
            # Build patrol route
            route = pat_row["trajectory_points"]
            route_lats = [pt[0] for pt in route]
            route_lons = [pt[1] for pt in route]
            
            # Base Plotly Mapbox
            fig = go.Figure()
            
            # Plot Threat points
            fig.add_trace(go.Scattermapbox(
                lat=map_pts[map_pts["type"].str.contains("Threat")]["latitude"],
                lon=map_pts[map_pts["type"].str.contains("Threat")]["longitude"],
                mode="markers",
                marker=go.scattermapbox.Marker(size=8, color="#EF4444", opacity=0.7),
                name="Poaching Threats (Simulated PPP)",
                hoverinfo="text",
                text=map_pts[map_pts["type"].str.contains("Threat")]["type"]
            ))
            
            # Plot Camp points
            fig.add_trace(go.Scattermapbox(
                lat=map_pts[map_pts["type"].str.contains("Camp")]["latitude"],
                lon=map_pts[map_pts["type"].str.contains("Camp")]["longitude"],
                mode="markers",
                marker=go.scattermapbox.Marker(size=14, color="#3B82F6"),
                name="Ranger Camps",
                hoverinfo="text",
                text=map_pts[map_pts["type"].str.contains("Camp")]["type"]
            ))
            
            # Plot selected patrol route path
            fig.add_trace(go.Scattermapbox(
                lat=route_lats,
                lon=route_lons,
                mode="lines+markers",
                line=go.scattermapbox.Line(width=3, color="#10B981"),
                marker=go.scattermapbox.Marker(size=6, color="#10B981"),
                name=f"Patrol Path ({sel_patrol_id})",
                hoverinfo="text",
                text=[f"Patrol checkpoint {j+1}" for j in range(len(route_lats))]
            ))
            
            center_lat = res_patrols["camp_latitude"].mean()
            center_lon = res_patrols["camp_longitude"].mean()
            
            apply_dark_layout(fig, height=450)
            fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    center={"lat": center_lat, "lon": center_lon},
                    zoom=11.5
                ),
                legend=dict(
                    bgcolor="rgba(14,17,23,0.75)",
                    font=dict(size=10)
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed patrol logs table
            st.markdown("### Patrol Records Database")
            log_table = res_patrols[["patrol_id", "camp_id", "patrol_coverage_ratio", "intervention_latency_mins", "poaching_indicators_detected"]].copy()
            log_table.columns = ["Patrol ID", "Ranger Camp", "Patrol Coverage %", "Intervention Latency (mins)", "Snares/Threats Detected"]
            log_table["Patrol Coverage %"] = (log_table["Patrol Coverage %"] * 100.0).round(1)
            st.dataframe(log_table, use_container_width=True, hide_index=True)
            
        else:
            st.warning("No patrol data available for this reserve.")

    # ── TAB 3: TSI & SHAP EXPLAINABILITY ──
    with tab_tsi:
        st.markdown(section_header("Module D: Tiger Success Index & Explanations", 
            "Analytic Hierarchy Process Weighting and Additive Shapley Value Decomposition"), 
            unsafe_allow_html=True)
            
        st.markdown(r"""
        ### Multi-Criteria Composite Scoring Math
        Criteria weights are derived from a consistent AHP pairwise comparison matrix, ensuring mathematical objectivity:
        - **Population Sustainability ($TS$):** Weight $0.40$
        - **Habitat Integrity ($HI$):** Weight $0.30$
        - **Anti-Poaching Effectiveness ($AP$):** Weight $0.20$
        - **Prey Density ($PD$):** Weight $0.10$
        
        The final index score is computed as:
        $$TSI = 0.40 \cdot TS + 0.30 \cdot HI + 0.20 \cdot AP + 0.10 \cdot PD$$
        """)
        
        t_res = st.selectbox("Select Reserve for TSI SHAP Decomposition", tsi_df["reserve_name"].tolist(), key="tsi_res")
        res_row = tsi_df[tsi_df["reserve_name"] == t_res].iloc[0]
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(stat_card_mini("TSI Score", f"{float(res_row['tsi_score']):.4f}", SUCCESS if res_row['tsi_score'] > 0.65 else ALERT if res_row['tsi_score'] < 0.40 else INFO), unsafe_allow_html=True)
        with c2:
            st.markdown(stat_card_mini("TS Metric", f"{float(res_row['c_TS']):.2f}", PRIMARY), unsafe_allow_html=True)
        with c3:
            st.markdown(stat_card_mini("HI Metric", f"{float(res_row['c_HI']):.2f}", PRIMARY), unsafe_allow_html=True)
        with c4:
            st.markdown(stat_card_mini("AP Metric", f"{float(res_row['c_AP']):.2f}", PRIMARY), unsafe_allow_html=True)
        with c5:
            st.markdown(stat_card_mini("PD Metric", f"{float(res_row['c_PD']):.2f}", PRIMARY), unsafe_allow_html=True)
            
        # Draw SHAP waterfall/bar chart
        shap_base = float(res_row["shap_base"])
        shap_values = {
            "TS (Population)": float(res_row["shap_TS"]),
            "HI (Habitat)": float(res_row["shap_HI"]),
            "AP (Anti-Poaching)": float(res_row["shap_AP"]),
            "PD (Prey Density)": float(res_row["shap_PD"])
        }
        
        st.markdown(f"### SHAP Explanation: How Features Pushed Score Away From National Baseline ({shap_base:.4f})")
        
        categories = list(shap_values.keys())
        values = list(shap_values.values())
        colors = ["#EF4444" if val < 0 else "#10B981" for val in values]
        
        fig_shap = go.Figure(go.Bar(
            x=values,
            y=categories,
            orientation="h",
            marker=dict(color=colors),
            text=[f"{v:+.4f}" for v in values],
            textposition="outside",
            textfont=dict(color=MUTED_TEXT, size=11),
            hovertemplate="<b>%{y}</b><br>SHAP Contribution: <b>%{x:+.4f}</b><extra></extra>"
        ))
        
        # Add a baseline vertical line
        fig_shap.add_vline(x=0, line_dash="dash", line_color=MUTED_TEXT, opacity=0.7)
        
        apply_dark_layout(fig_shap, height=300, showlegend=False, 
                          xaxis_title="SHAP Value (Marginal Contribution)", yaxis_title="")
        
        st.plotly_chart(fig_shap, use_container_width=True)
        
        st.markdown("""
        > [!NOTE]
        > **SHAP Explainability Insight:** Positive SHAP values indicate that the reserve outperforms the national average for that component, raising its composite TSI. Negative values represent constraints where active intervention (e.g. anti-poaching patrol augmentation or habitat restoration) is required.
        """)

else:
    st.warning("Please regenerate all CSV database files first.")
