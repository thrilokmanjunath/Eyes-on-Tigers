import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys, os

# Add imports for UI consistency
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.map_utils import (GLOBAL_CSS, stat_card, stat_card_mini, section_header,
                              page_header, apply_dark_layout, divider,
                              ACCENT, ACCENT_LIGHT, ALERT, PRIMARY, SUCCESS, INFO, MUTED_TEXT, TEXT_COLOR)
from utils.data_loader import get_reserves_with_population

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.markdown(page_header(
    "Growth & Projections",
    "Analyze tiger population densities, future projections, and state performance.",
    "🐯"
), unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        density_df = pd.read_csv(os.path.join(data_dir, "tiger_density_matrix_separate_final.csv"))
        proj_df = pd.read_csv(os.path.join(data_dir, "tiger_population_matrix_2030_projection.csv"))
        thresholds_df = pd.read_excel(os.path.join(data_dir, "state_density_thresholds.xlsx"))
        return density_df, proj_df, thresholds_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

density_df, proj_df, thresholds_df = load_data()

if not density_df.empty and not proj_df.empty:
    # --- Methodology Section ---
    st.markdown(section_header("Methodology", "How Density and Projections Were Calculated"), unsafe_allow_html=True)
    
    badge = (f'min-width:28px;height:28px;background:{ACCENT}20;border:1px solid {ACCENT}50;'
             f'border-radius:50%;display:flex;align-items:center;justify-content:center;'
             f'color:{ACCENT};font-weight:700;font-size:0.8rem;flex-shrink:0;margin-top:2px;')
    method_html = (
        f'<div style="background:linear-gradient(135deg,rgba(27,67,50,0.7),rgba(10,31,21,0.85));'
        f'border:1px solid {ACCENT}30;border-left:4px solid {ACCENT};border-radius:12px;'
        f'padding:24px 28px;margin:12px 0 8px 0;">'
        f'<p style="color:{MUTED_TEXT};font-size:0.78rem;letter-spacing:0.12em;text-transform:uppercase;margin:0 0 18px 0;">'
        f'📐 Three-Step Process &nbsp;·&nbsp; 2006 – 2030</p>'
        f'<div style="display:flex;flex-direction:column;gap:16px;">'

        # Step 1
        f'<div style="display:flex;align-items:flex-start;gap:14px;">'
        f'<div style="{badge}">1</div>'
        f'<div><p style="margin:0;color:{TEXT_COLOR};font-weight:600;font-size:0.9rem;">National Interpolation</p>'
        f'<p style="margin:4px 0 0 0;color:{MUTED_TEXT};font-size:0.83rem;line-height:1.55;">'
        f'Census anchor points (2006–2022) were smoothed using <strong style="color:{ACCENT};">PCHIP</strong>, '
        f'producing a monotone curve that passes exactly through every known census value.</p></div></div>'

        # Step 2
        f'<div style="display:flex;align-items:flex-start;gap:14px;">'
        f'<div style="{badge}">2</div>'
        f'<div><p style="margin:0;color:{TEXT_COLOR};font-weight:600;font-size:0.9rem;">State Disaggregation</p>'
        f'<p style="margin:4px 0 0 0;color:{MUTED_TEXT};font-size:0.83rem;line-height:1.55;">'
        f'National density <code style="background:rgba(245,158,11,0.12);padding:1px 5px;border-radius:3px;'
        f'font-size:0.8rem;color:{ACCENT_LIGHT};">estimated_count = national_density × state_reserve_area</code> '
        f'A residual error at each census year <code style="background:rgba(245,158,11,0.12);padding:1px 5px;border-radius:3px;'
        f'font-size:0.8rem;color:{ACCENT_LIGHT};">error = actual - estimated</code> '
        f'was <strong style="color:{ACCENT};">PCHIP-interpolated</strong> per state across census years and added back. '
        f'A scaling constraint ensures all states sum to the national total each year.</p></div></div>'

        # Step 3
        f'<div style="display:flex;align-items:flex-start;gap:14px;">'
        f'<div style="{badge}">3</div>'
        f'<div><p style="margin:0;color:{TEXT_COLOR};font-weight:600;font-size:0.9rem;">Post-2022 Projections</p>'
        f'<p style="margin:4px 0 0 0;color:{MUTED_TEXT};font-size:0.83rem;line-height:1.55;">'
        f'Growth is capped at <strong style="color:{SUCCESS};">8% per state per year</strong>. '
        f'National mortality is disaggregated proportionally as a biological dampener, '
        f'keeping projections ecologically bounded.</p></div></div>'

        f'</div></div>'
    )
    st.markdown(method_html, unsafe_allow_html=True)
    st.markdown(divider(), unsafe_allow_html=True)



    # --- State Performance Analysis ---
    st.markdown(section_header("State Performance Analysis (Density)", "Evaluate State Carrying Capacity and Growth Potential"), unsafe_allow_html=True)
    
    states = sorted([c for c in density_df.columns if c.lower() != 'year'])
    selected_state = st.selectbox("Select a State to View Performance", states)
    
    if selected_state:
        latest_year = density_df['year'].max()
        latest_density = density_df[density_df['year'] == latest_year][selected_state].values[0]
        score = int(round(latest_density * 100))
        
        # Get threshold info
        state_info = thresholds_df[thresholds_df['State'] == selected_state]
        category = "Unknown"
        basis = "No data"
        if not state_info.empty:
            category = state_info['Category'].values[0]
            basis = state_info['Reserves Considered / Basis'].values[0]
            
        # Determine actionable insights
        if score < 5:
            perf_text = "Underperforming"
            color = ALERT # Red
            actionable = "Critical: Needs urgent prey base augmentation, habitat restoration, and anti-poaching measures."
        elif score < 10:
            perf_text = "Moderate"
            color = "#FFA07A"
            actionable = "Needs Improvement: Focus on corridor connectivity and reducing human-wildlife conflict."
        elif score < 15:
            perf_text = "Good"
            color = INFO # Blue/Light Green
            actionable = "Stable: Maintain current protection levels and monitor carrying capacity limits."
        else:
            perf_text = "Excellent (Healthy)"
            color = SUCCESS # Green
            actionable = "Optimal: Healthy carrying capacity reached. Potential source population for relocation."

        st.markdown(f"### Performance for {selected_state} in {latest_year}")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(stat_card_mini("Raw Density", f"{latest_density:.4f}", PRIMARY), unsafe_allow_html=True)
        with c2:
            st.markdown(stat_card_mini("Density Score", f"{score} / 100 sqkm", ACCENT), unsafe_allow_html=True)
        with c3:
            st.markdown(stat_card_mini("Forest Category", str(category), INFO), unsafe_allow_html=True)
        with c4:
            st.markdown(stat_card_mini("Status", perf_text, color), unsafe_allow_html=True)
            
        st.markdown(f"""
        <div style="background-color: rgba(255,255,255,0.05); padding: 15px; border-left: 4px solid {color}; border-radius: 4px; margin-top: 10px;">
            <p style="margin:0; color:{TEXT_COLOR};"><strong>Reserves Considered / Basis:</strong> {basis}</p>
            <p style="margin:5px 0 0 0; color:{MUTED_TEXT};"><strong>Recommendation:</strong> {actionable}</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown(divider(), unsafe_allow_html=True)

    # --- Compare states charts ---
    st.markdown(section_header("Comparative Trajectories", "Compare Density and Population Trends Across States"), unsafe_allow_html=True)
    
    comp_states = st.multiselect("Select States to Compare (Max 4)", states, default=[selected_state] if selected_state else states[:2], max_selections=4)
    
    if comp_states:
        tab1, tab2 = st.tabs(["Density Trends (Historical)", "Population Projections"])
        
        with tab1:
            fig_density = go.Figure()
            for s in comp_states:
                fig_density.add_trace(go.Scatter(
                    x=density_df['year'], y=density_df[s],
                    mode='lines+markers', name=s,
                    line=dict(width=3)
                ))
            apply_dark_layout(fig_density, title="Historical Density Comparison", xaxis_title="Year", yaxis_title="Tiger Density")
            st.plotly_chart(fig_density, use_container_width=True)
            
        with tab2:
            _proj_min = int(proj_df['year'].min())
            _proj_max = int(proj_df['year'].max())
            proj_end_year = st.slider(
                "Show projection up to year",
                min_value=_proj_min,
                max_value=_proj_max,
                value=_proj_max,
                step=1,
                key="proj_end_year",
                help="Drag to explore the trajectory up to any year. Years after 2022 are growth-capped extrapolations."
            )
            historical_year = 2022
            fig_proj = go.Figure()
            for s in comp_states:
                # Historical part
                hist_mask = (proj_df['year'] <= historical_year) & (proj_df['year'] <= proj_end_year)
                proj_mask = (proj_df['year'] >= historical_year) & (proj_df['year'] <= proj_end_year)
                fig_proj.add_trace(go.Scatter(
                    x=proj_df[hist_mask]['year'], y=proj_df[hist_mask][s],
                    mode='lines+markers', name=f"{s} (Hist)",
                    line=dict(width=3), legendgroup=s
                ))
                if proj_end_year > historical_year:
                    # Projected part (dashed)
                    fig_proj.add_trace(go.Scatter(
                        x=proj_df[proj_mask]['year'], y=proj_df[proj_mask][s],
                        mode='lines+markers', name=f"{s} (Proj)",
                        line=dict(width=3, dash='dash'), legendgroup=s, showlegend=False
                    ))

            if proj_end_year > historical_year:
                fig_proj.add_vrect(
                    x0=historical_year, x1=proj_end_year,
                    fillcolor=ACCENT, opacity=0.05, line_width=0,
                    annotation_text=f"Projected ({historical_year}–{proj_end_year})",
                    annotation_position="top left"
                )

            apply_dark_layout(fig_proj, title=f"Population Trajectories & Projections (up to {proj_end_year})",
                              xaxis_title="Year", yaxis_title="Estimated Tiger Count")
            st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown(divider(), unsafe_allow_html=True)

    # --- 2026 & 2030 Projection Map Section ---
    st.markdown(section_header(
        "2026 & 2030 Projection Map",
        "Visualizing future population estimates over state carrying capacity categories and tiger concentration hubs."
    ), unsafe_allow_html=True)

    c_yr, c_col = st.columns([1, 1])
    with c_yr:
        proj_year = st.radio("Select Projection Year", [2026, 2030], index=0, horizontal=True, key="map_proj_year")
    with c_col:
        map_view = st.selectbox("Color Map By", ["Forest / Habitat Category", "Tiger Concentration Hubs"], index=0, key="growth_map_color")

    # Load reserve projection population
    reserves_ref = get_reserves_with_population(proj_year)
    
    # Merge with thresholds to get Forest Category
    if not thresholds_df.empty:
        state_cat = thresholds_df.set_index("State")["Category"].to_dict()
        reserves_ref["Forest Category"] = reserves_ref["state"].map(state_cat).fillna("Unknown")
    else:
        reserves_ref["Forest Category"] = "Unknown"

    # Spot tiger concentrated places (density >= 12.0)
    reserves_ref["Concentration Status"] = reserves_ref["density_per_100km2"].apply(
        lambda d: "🔥 High Concentration Hub" if d >= 12.0 else "Standard Density Habitat"
    )

    reserves_ref["bubble_size"] = reserves_ref["population"].clip(lower=4)

    if map_view == "Forest / Habitat Category":
        color_col = "Forest Category"
        color_discrete_map = {
            "High-Prey Hotspot": "#10B981", # green
            "Dry Deciduous": "#F59E0B",     # orange
            "Blended (weighted)": "#3B82F6", # blue
            "Sparse / Low": "#6B7280",      # grey
            "Sparse / Low (exception)": "#9CA3AF",
            "Mangrove (Sparse band reused)": "#8B5CF6", # purple
            "Unknown": "#4B5563"
        }
        legend_title = "Forest Category"
    else:
        color_col = "Concentration Status"
        color_discrete_map = {
            "🔥 High Concentration Hub": "#EF4444", # Red
            "Standard Density Habitat": "#10B981"  # Green
        }
        legend_title = "Concentration Hubs"

    fig_habitat_map = px.scatter_mapbox(
        reserves_ref,
        lat="latitude",
        lon="longitude",
        size="bubble_size",
        color=color_col,
        hover_name="reserve_name",
        hover_data={
            "state": True,
            "population": True,
            "density_per_100km2": ":.2f",
            "Forest Category": False,
            "Concentration Status": True,
            "bubble_size": False,
            "latitude": False,
            "longitude": False
        },
        color_discrete_map=color_discrete_map,
        size_max=32,
        zoom=4.0,
        center={"lat": 22.5, "lon": 80.0},
        mapbox_style="carto-positron"
    )
    apply_dark_layout(fig_habitat_map, height=520)
    fig_habitat_map.update_layout(
        mapbox=dict(style="carto-positron", center={"lat": 22.5, "lon": 80.0}, zoom=4.0),
        legend=dict(
            title=dict(text=legend_title, font=dict(size=11)),
            font=dict(size=10),
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(14,17,23,0.7)"
        )
    )
    
    st.plotly_chart(fig_habitat_map, use_container_width=True)

    st.markdown(divider(), unsafe_allow_html=True)

    # --- Data Insights / Fun Facts ---
    st.markdown(section_header(
        "Data Insights",
        "What the numbers actually tell us — three surprising facts from our database"
    ), unsafe_allow_html=True)

    # Pre-compute values for the fun fact cards
    _dens_2022 = density_df[density_df['year'] == 2022].drop(columns=['year']).iloc[0]
    _dens_2006 = density_df[density_df['year'] == 2006].drop(columns=['year']).iloc[0]
    _pop_2022  = proj_df[proj_df['year'] == 2022].drop(columns=['year']).iloc[0]
    _mp_pop  = int(_pop_2022.get('Madhya Pradesh', 0))
    _uk_pop  = int(_pop_2022.get('Uttarakhand', 0))
    _mp_dens = _dens_2022.get('Madhya Pradesh', 0)
    _uk_dens = _dens_2022.get('Uttarakhand', 0)
    _uk_ratio = round(_uk_dens / _mp_dens, 1) if _mp_dens > 0 else 0
    # Bihar growth
    _bih_06  = _dens_2006.get('Bihar', 0)
    _bih_22  = _dens_2022.get('Bihar', 0)
    _bih_growth_pct = int(round((_bih_22 - _bih_06) / max(_bih_06, 1e-9) * 100))
    # Arunachal facts
    _ar_pop  = int(_pop_2022.get('Arunachal Pradesh', 0))

    insight_cards = [
        {
            "emoji": "🗺️",
            "title": "The Counting Paradox — More Tigers Doesn't Mean Denser Forest",
            "body": (
                f"Madhya Pradesh leads the nation with <b>~{_mp_pop:,} tigers</b> in 2022, "
                f"but Uttarakhand is <b>{_uk_ratio}× denser</b> — {_uk_dens*100:.0f} vs {_mp_dens*100:.0f} tigers "
                f"per 100 km² of reserve area. MP's reserves are a wide blend of Dry Deciduous "
                f"and some High-Prey patches (threshold 6.8–12.9/100 km²), "
                f"while Corbett &amp; Rajaji in Uttarakhand are prime High-Prey Terai habitat. "
                f"Large forests ≠ efficient forests."
            ),
            "color": ACCENT,
        },
        {
            "emoji": "📈",
            "title": "Bihar's Silent Turnaround — +{pct}% Density Since 2006".format(pct=_bih_growth_pct),
            "body": (
                f"Despite hosting just one reserve (Valmiki Tiger Reserve), Bihar achieved "
                f"the <b>highest proportional density growth</b> of any state in our database: "
                f"<b>+{_bih_growth_pct}%</b> between 2006 and 2022. This is what focused protection "
                f"in prime High-Prey Terai habitat looks like — a small, well-managed reserve "
                f"dramatically outperforming states with far more land under protection."
            ),
            "color": SUCCESS,
        },
        {
            "emoji": "🌿",
            "title": "Arunachal Pradesh: Vast Forests, Invisible Tigers",
            "body": (
                f"Arunachal Pradesh has three reserves covering over 3,274 km² of core area "
                f"— more than most individual states — yet our model estimates only <b>~{_ar_pop} tigers</b>. "
                f"Its dense evergreen forests have a naturally low ecological density ceiling "
                f"(2–5 tigers per 100 km²) and camera-trap coverage is among the thinnest in India. "
                f"Many years in this state's timeline are extrapolated, so the true count "
                f"could be meaningfully higher — or lower."
            ),
            "color": INFO,
        },
    ]

    for card in insight_cards:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(10,31,21,0.75),rgba(22,43,35,0.6));'
            f'border:1px solid {card["color"]}30;border-left:4px solid {card["color"]};'
            f'border-radius:12px;padding:20px 24px;margin:10px 0;">'
            f'<p style="font-size:1.1rem;margin:0 0 6px 0;">'
            f'{card["emoji"]} <b style="color:{TEXT_COLOR};">{card["title"]}</b></p>'
            f'<p style="color:{MUTED_TEXT};font-size:0.875rem;line-height:1.65;margin:0;">'
            f'{card["body"]}</p></div>',
            unsafe_allow_html=True
        )

else:
    st.warning("No data available to display.")
