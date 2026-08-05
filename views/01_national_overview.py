"""
Page 1 - National Overview
State-level choropleth bars, reserve bubble map, and population trend with CI bands.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import (load_census, get_national_trend_df,
                                get_reserves_with_population,
                                get_imputation_explanation,
                                load_funding_geographical_area_year,
                                get_reserve_core_area_for_year,
                                CENSUS_YEARS)
from utils.map_utils import (GLOBAL_CSS, stat_card, stat_card_mini, section_header,
                              page_header, apply_dark_layout, create_india_map, divider,
                              ACCENT, ACCENT_LIGHT, ALERT, PRIMARY, PRIMARY_LIGHT,
                              PRIMARY_DARK, TEXT_COLOR, MUTED_TEXT, BORDER_SUBTLE,
                              SUCCESS, INFO, popout_link)


st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


with st.spinner("Loading national data..."):
    census = load_census()
    national_trend = get_national_trend_df()
    agg_df = load_funding_geographical_area_year()
    reserves_pop = get_reserves_with_population(2022)

# ── Derived stats ──
total_2022   = int(agg_df[agg_df["year"] == 2022]["tiger_count"].values[0])
total_2006   = int(agg_df[agg_df["year"] == 2006]["tiger_count"].values[0])
growth_pct   = round(((total_2022 - total_2006) / max(total_2006, 1)) * 100, 1)

census_2022 = census[census["year"] == 2022]
state_pop_2022 = census_2022.groupby("state")["population_imputed"].sum().reset_index()
state_pop_2022.columns = ["state", "population"]

top_state = state_pop_2022.sort_values("population", ascending=False).iloc[0]

# Which states had imputed values?
n_imputed = int(census["was_imputed"].sum())
methods_used = census[census["was_imputed"] == True]["imputation_method"].value_counts().to_dict()

# ── Page header ──
st.markdown(page_header(
    "National Overview",
    "State-by-State Tiger Population Analysis · Reserve Distribution Map · Historical Trend",
    "🗺️"
), unsafe_allow_html=True)

# ── Stat cards ──
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(stat_card("Total Tigers (2022)", f"{total_2022:,}",
        "All-India Estimate · NTCA", ACCENT), unsafe_allow_html=True)
with c2:
    st.markdown(stat_card("Growth Since 2006", f"+{growth_pct}%",
        f"{total_2006:,} → {total_2022:,}", SUCCESS), unsafe_allow_html=True)
with c3:
    st.markdown(stat_card("Leading State", top_state["state"],
        f"{int(top_state['population']):,} Tigers in 2022", INFO), unsafe_allow_html=True)
with c4:
    st.markdown(stat_card("Imputed Records", f"{n_imputed:,}",
        "Gaps Filled by Modelling", "#A78BFA"), unsafe_allow_html=True)

st.markdown(divider(), unsafe_allow_html=True)

# ── Tabs: Map | State Bar | Trend | Data Table ──
tab_map, tab_bar, tab_trend, tab_data = st.tabs([
    "🗺️  Reserve Map", "📊  State Rankings", "📈  Population Trend", "📋  Data & Methods"
])

# ── Tab 1: Reserve bubble map ──
with tab_map:
    # Build labeled year options (2006-2026)
    _all_years = list(range(2006, 2027))
    _year_labels = []
    for _y in _all_years:
        if _y in CENSUS_YEARS:
            _year_labels.append(str(_y))
        elif _y < 2022:
            _year_labels.append(f"{_y}  (interpolated)")
        else:
            _year_labels.append(f"{_y}  (extrapolated)")
    _label_to_year = {lbl: yr for yr, lbl in zip(_all_years, _year_labels)}

    col_yr, col_color = st.columns([1, 1])
    with col_yr:
        year_label_sel = st.selectbox(
            "Year",
            options=_year_labels,
            index=_year_labels.index(str(2022)),
            key="map_year",
            help="Census years are official NTCA counts. Intermediate years are PCHIP-interpolated; "
                 "years after 2022 are growth-capped extrapolations."
        )
        year_sel = _label_to_year[year_label_sel]
    with col_color:
        map_color_metric = st.selectbox(
            "Color Map By",
            ["Density (per 100 km²)", "Habitat Fragmentation Score"],
            index=0,
            key="map_color_metric"
        )

    reserves_pop = get_reserves_with_population(year_sel)

    # Calculate NDVI difference for hover display
    reserves_pop["ndvi_change"] = reserves_pop["ndvi_2022"] - reserves_pop["ndvi_2015"]
    reserves_pop["bubble_size"] = reserves_pop["population"].clip(lower=3)
    
    total_core_area = get_reserve_core_area_for_year(year_sel)

    # Determine data type label for header
    if year_sel in CENSUS_YEARS:
        _data_type = "Official NTCA Census"
    elif year_sel <= 2022:
        _data_type = "Interpolated estimate (PCHIP)"
    else:
        _data_type = "Extrapolated projection"

    st.markdown(section_header(
        "India Tiger Reserve Map",
        f"{_data_type} · {year_sel} · Total Core Reserve Area: {total_core_area:,.0f} km²"
    ), unsafe_allow_html=True)

    # ── Map legend / index ──
    if map_color_metric == "Habitat Fragmentation Score":
        legend_html = (
            f'<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;'
            f'background:rgba(10,31,21,0.55);border:1px solid {ACCENT}22;'
            f'border-radius:10px;padding:10px 16px;margin-bottom:6px;font-size:0.78rem;">'
            f'<span style="color:{MUTED_TEXT};font-weight:600;letter-spacing:0.08em;margin-right:4px;">LEGEND &nbsp;·</span>'
            f'<span style="color:{TEXT_COLOR};">⬤ <b>Bubble size</b> = estimated tiger count at reserve</span>'
            f'<span style="color:{MUTED_TEXT};">|</span>'
            f'<span style="color:{SUCCESS};">⬛ 0.0 – 0.29</span> <span style="color:{TEXT_COLOR};margin-right:4px;">Healthy habitat</span>'
            f'<span style="color:{ACCENT};">⬛ 0.30 – 0.49</span> <span style="color:{TEXT_COLOR};margin-right:4px;">Moderate stress</span>'
            f'<span style="color:{ALERT};">⬛ 0.50 – 1.0</span> <span style="color:{TEXT_COLOR};">Critical fragmentation</span>'
            f'</div>'
        )
    else:
        legend_html = (
            f'<div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;'
            f'background:rgba(10,31,21,0.55);border:1px solid {ACCENT}22;'
            f'border-radius:10px;padding:10px 16px;margin-bottom:6px;font-size:0.78rem;">'
            f'<span style="color:{MUTED_TEXT};font-weight:600;letter-spacing:0.08em;margin-right:4px;">LEGEND &nbsp;·</span>'
            f'<span style="color:{TEXT_COLOR};">⬤ <b>Bubble size</b> = estimated tiger count at reserve</span>'
            f'<span style="color:{MUTED_TEXT};">|</span>'
            f'<span style="color:{TEXT_COLOR};">🎨 <b>Colour</b> = tigers per 100 km² of total reserve area</span>'
            f'<span style="color:{MUTED_TEXT};">|</span>'
            f'<span style="color:#2D6A4F;">■ Low density</span>'
            f'<span style="color:#F59E0B;">■ Moderate</span>'
            f'<span style="color:#EF4444;">■ High density</span>'
            f'</div>'
        )
    st.markdown(legend_html, unsafe_allow_html=True)

    if map_color_metric == "Habitat Fragmentation Score":
        color_col = "fragmentation_score"
        # Low fragmentation = green (good), High fragmentation = red (critical)
        color_scale = [[0, SUCCESS], [0.4, ACCENT], [1.0, ALERT]]
        colorbar_title = "Fragmentation<br>Score"
    else:
        color_col = "density_per_100km2"
        color_scale = [[0, "#1B4332"], [0.3, "#2D6A4F"], [0.6, "#F59E0B"], [1.0, "#EF4444"]]
        colorbar_title = "Density<br>/ 100 km²"

    fig_map = create_india_map(
        reserves_pop, size_col="bubble_size", color_col=color_col,
        hover_name="reserve_name",
        hover_data={
            "state": True,
            "population": True,
            "core_area_km2": True,
            "density_per_100km2": ":.2f",
            "fragmentation_score": ":.2f",
            "ndvi_2022": ":.2f",
            "ndvi_change": ":.2f",
            "bubble_size": False,
            "latitude": False,
            "longitude": False
        },
        color_scale=color_scale,
        title="", size_max=38,
    )
    fig_map.update_layout(
        coloraxis_colorbar=dict(
            title=dict(text=colorbar_title, font=dict(size=11)),
            tickfont=dict(size=10), len=0.6, thickness=14
        ),
        height=620,
    )
    popout_link(fig_map, "national_map_popout", "Pop out chart")
    event = st.plotly_chart(fig_map, use_container_width=True,
                             on_select="rerun", key="reserve_map")

    # Click detail
    if event and event.selection and event.selection.points:
        idx = event.selection.points[0].get("point_index")
        if idx is not None and idx < len(reserves_pop):
            sel = reserves_pop.iloc[idx]
            state_census = census[census["state"] == sel["state"]].sort_values("year")

            st.markdown(
                f'<div style="background:linear-gradient(135deg,#0A1F15,{PRIMARY});'
                f'border:1px solid {ACCENT}22;border-radius:16px;padding:24px 28px;'
                f'margin-top:16px;position:relative;overflow:hidden;">'
                f'<div style="position:absolute;top:0;left:0;right:0;height:3px;'
                f'background:linear-gradient(90deg,transparent,{ACCENT}66,transparent);"></div>'
                f'<h2 style="color:{TEXT_COLOR};margin:0 0 4px 0;font-size:1.4rem;font-weight:800;">'
                f'{sel["reserve_name"]} Tiger Reserve</h2>'
                f'<p style="color:{MUTED_TEXT};margin:0 0 18px 0;font-size:0.82rem;">'
                f'{sel["state"]} &bull; {sel["latitude"]:.2f}°N, {sel["longitude"]:.2f}°E'
                f' &bull; Core: {int(sel["core_area_km2"]):,} km² &bull; Buffer: {int(sel["buffer_area_km2"]):,} km²'
                f' &bull; Total Area: {int(sel["total_area_km2"]):,} km²</p>'
                f'</div>',
                unsafe_allow_html=True
            )
            s1, s2, s3, s4, s5 = st.columns(5)
            with s1:
                st.markdown(stat_card_mini("Est. Population", f"~{int(sel['population']):,}", ACCENT), unsafe_allow_html=True)
            with s2:
                st.markdown(stat_card_mini("Core Area", f"{int(sel['core_area_km2']):,} km²", INFO), unsafe_allow_html=True)
            with s3:
                st.markdown(stat_card_mini("Density", f"{sel['density_per_100km2']:.2f} /100km²", PRIMARY_LIGHT), unsafe_allow_html=True)
            with s4:
                frag = sel.get('fragmentation_score')
                if pd.isna(frag):
                    frag_str = "N/A"
                    frag_color = MUTED_TEXT
                else:
                    frag_str = f"{frag:.2f}"
                    frag_color = ALERT if frag >= 0.5 else (ACCENT if frag >= 0.3 else SUCCESS)
                st.markdown(stat_card_mini("Frag. Score", frag_str, frag_color), unsafe_allow_html=True)
            with s5:
                ndvi = sel.get('ndvi_2022')
                ndvi_str = f"{ndvi:.2f}" if pd.notna(ndvi) else "N/A"
                st.markdown(stat_card_mini("NDVI (2022)", ndvi_str, "#A78BFA"), unsafe_allow_html=True)

            with st.expander("ℹ️ How Is This Reserve's Population Estimated?"):
                    st.info(
                        f"**{reserves_pop.iloc[0]['note'] if 'note' in reserves_pop.columns else 'Proportional distribution from state-level census.'}**\n\n"
                        f"The NTCA census provides data at the **state level** ({sel['state']}). "
                        f"To estimate this reserve's population, the state total is distributed "
                        f"proportionally based on each reserve's **core area** as a fraction of the "
                        f"state's total core area.\n\n"
                        f"**Formula:** `reserve_pop = state_pop × (reserve_core_km² / state_total_core_km²)`\n\n"
                        f"This is an approximation. Actual reserve-level figures require individual camera-trap surveys."
                    )
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="text-align:center;padding:20px;margin-top:10px;'
            f'background:rgba(22,43,35,0.25);border:1px dashed {ACCENT}20;border-radius:12px;">'
            f'<p style="color:{MUTED_TEXT};font-size:0.85rem;margin:0;">'
            f'Click any reserve bubble to view detailed stats</p></div>',
            unsafe_allow_html=True
        )

# ── Tab 2: State bar chart ──
with tab_bar:
    # Build labeled year options (2006-2026)
    _bar_years = list(range(2006, 2027))
    _bar_labels = []
    for _y in _bar_years:
        if _y in CENSUS_YEARS:
            _bar_labels.append(str(_y))
        elif _y < 2022:
            _bar_labels.append(f"{_y} (Estimated)")
        else:
            _bar_labels.append(f"{_y} (Extrapolated)")
    _bar_labels.reverse() # Show newest first
    _bar_label_to_year = {lbl: yr for yr, lbl in zip(_bar_years, _bar_labels)}

    yr_col, view_col = st.columns([1, 2])
    with yr_col:
        selected_year_label = st.selectbox("Select Year", _bar_labels, index=_bar_labels.index(str(2022)), key="bar_year")
        selected_year = _bar_label_to_year[selected_year_label]

    # Determine data type and whether we have confidence intervals
    if selected_year in CENSUS_YEARS:
        _bar_data_type = "Official NTCA Census"
        has_ci = True
        year_data = census[census["year"] == selected_year].copy()
        year_data = year_data.groupby("state", as_index=False).agg(
            population=("population_imputed", "sum"),
            ci_lower=("population_ci_lower", "mean"),
            ci_upper=("population_ci_upper", "mean"),
            any_imputed=("was_imputed", "any")
        ).sort_values("population", ascending=False)
    else:
        if selected_year <= 2022:
            _bar_data_type = "Interpolated Estimate"
        else:
            _bar_data_type = "Extrapolated Projection"
        has_ci = False
        
        # Load from projection matrix
        try:
            proj_path = os.path.join(os.path.dirname(__file__), "..", "data", "tiger_population_matrix_2030_projection.csv")
            proj = pd.read_csv(proj_path)
            proj["year"] = proj["year"].astype(int)
            row = proj[proj["year"] == selected_year]
            state_cols = [c for c in proj.columns if c != "year"]
            pop_series = row[state_cols].iloc[0]
            year_data = pd.DataFrame({
                "state": state_cols,
                "population": pop_series.values
            })
            year_data["ci_lower"] = year_data["population"]
            year_data["ci_upper"] = year_data["population"]
            year_data["any_imputed"] = True # Model estimated
            year_data = year_data.sort_values("population", ascending=False)
        except Exception as e:
            st.error(f"Error loading projection data: {e}")
            year_data = pd.DataFrame(columns=["state", "population", "ci_lower", "ci_upper", "any_imputed"])

    with view_col:
        if has_ci:
            show_ci = st.checkbox("Show Confidence Intervals", value=True, key="show_ci")
        else:
            st.checkbox("Show Confidence Intervals", value=False, disabled=True, key="show_ci",
                        help="Confidence intervals are only available for official census years.")
            show_ci = False

    st.markdown(section_header("State-Level Tiger Population",
        f"{_bar_data_type} · {selected_year} · Height = Estimated Population Count"),
        unsafe_allow_html=True)

    # Color imputed states differently
    year_data["bar_color"] = year_data["any_imputed"].apply(
        lambda x: "#A78BFA" if x else ACCENT
    )

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=year_data["state"], y=year_data["population"],
        marker_color=year_data["bar_color"],
        text=[f"{int(v):,}" for v in year_data["population"]],
        textposition="outside",
        textfont=dict(size=10, color=MUTED_TEXT),
        error_y=dict(
            type="data",
            symmetric=False,
            array=(year_data["ci_upper"] - year_data["population"]).clip(lower=0).tolist(),
            arrayminus=(year_data["population"] - year_data["ci_lower"]).clip(lower=0).tolist(),
            color="rgba(255,255,255,0.25)",
            thickness=1.5, width=6,
            visible=show_ci
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Population: <b>%{y:,}</b><br>"
            "<extra></extra>"
        )
    ))
    apply_dark_layout(fig_bar, height=460, showlegend=False,
                      xaxis_title="State", yaxis_title=f"Tiger Count ({selected_year})")
    fig_bar.update_xaxes(tickangle=-40)

    # Legend annotation
    if selected_year in CENSUS_YEARS:
        legend_text = (f"<span style='color:{ACCENT};'>■</span> Direct Count &nbsp;&nbsp;"
                       f"<span style='color:#A78BFA;'>■</span> Includes Imputed Values")
    elif selected_year <= 2022:
        legend_text = f"<span style='color:#A78BFA;'>■</span> PCHIP Interpolated Estimate"
    else:
        legend_text = f"<span style='color:#A78BFA;'>■</span> Extrapolated Projection"

    fig_bar.add_annotation(
        x=0.98, y=0.97, xref="paper", yref="paper",
        text=legend_text,
        showarrow=False, font=dict(size=10, color=MUTED_TEXT),
        align="right", bgcolor="rgba(14,17,23,0.5)", borderpad=6
    )
    popout_link(fig_bar, "national_state_bar_popout", "Pop out chart")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Tab 3: National trend ──
with tab_trend:
    st.markdown(section_header("National Population Trend (1973–2030)",
        "Pre-2006: Pug-Mark Methodology (Overcount). Post-2006: Camera-Trap (Reliable) & Projections."),
        unsafe_allow_html=True)

    hist_mask = national_trend["year"] <= 2022
    proj_mask = national_trend["year"] >= 2022

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=national_trend["year"], y=national_trend["population"],
        mode="none", fill="tozeroy", fillcolor="rgba(245,158,11,0.06)",
        name="", showlegend=False
    ))
    
    # 1. Census Counts line (solid)
    _c_years = {2006, 2010, 2014, 2018, 2022}
    fig_trend.add_trace(go.Scatter(
        x=national_trend[hist_mask]["year"], y=national_trend[hist_mask]["population"],
        mode="lines+markers",
        line=dict(color=ACCENT, width=3, shape="spline"),
        marker=dict(size=10, color=ACCENT, line=dict(width=2.5, color=PRIMARY_DARK)),
        hovertemplate="<b>%{x}</b><br>Population: <b>%{y:,}</b><extra></extra>",
        name="Census Counts"
    ))
    
    # 2. Projected line (dashed)
    fig_trend.add_trace(go.Scatter(
        x=national_trend[proj_mask]["year"], y=national_trend[proj_mask]["population"],
        mode="lines+markers",
        line=dict(color=ACCENT, width=3, dash="dash", shape="spline"),
        marker=dict(size=8, color=ACCENT_LIGHT, line=dict(width=1.5, color=PRIMARY_DARK)),
        hovertemplate="<b>%{x} (Projected)</b><br>Population: <b>%{y:,}</b><extra></extra>",
        name="Projections"
    ))

    # 2006 methodology break
    fig_trend.add_vrect(x0=2005.5, x1=2006.5,
        fillcolor=ALERT, opacity=0.07, line_width=0)
    fig_trend.add_annotation(
        x=2006, y=max(national_trend["population"]) * 0.85,
        text="Methodology Shift → 2006",
        showarrow=True, arrowhead=2, arrowcolor=ALERT,
        arrowwidth=1.5, font=dict(size=10, color=ALERT),
        ax=50, ay=-30
    )

    # Label only census years and pre-2006 points
    for _, row in national_trend.iterrows():
        yr = row["year"]
        if yr < 2006 or yr in _c_years or yr == 2030:
            fig_trend.add_annotation(
                x=yr, y=row["population"],
                text=f"{int(row['population']):,}",
                showarrow=False, yshift=18,
                font=dict(size=9, color=MUTED_TEXT)
            )

    apply_dark_layout(fig_trend, height=430, showlegend=True,
                      xaxis_title="Year", yaxis_title="Tiger Population (All-India)")
    fig_trend.update_xaxes(dtick=5)
    popout_link(fig_trend, "national_trend_popout", "Pop out chart")
    st.plotly_chart(fig_trend, use_container_width=True)

    with st.expander("📚 Methodology Note — Historical Population Estimates"):
        st.markdown("""
**Pre-2006 estimates** were produced using the *pug-mark census method*, where forest 
guards traced tiger footprints across reserves. This method is now considered unreliable 
and led to significant overestimates (population appeared to *decline* when methodology changed).

**2006 onward:** India adopted **camera-trap photographic mark-recapture (PMR)**, developed 
by the Wildlife Institute of India (WII). Individual tigers are identified by unique 
stripe patterns. Combined with occupancy modelling, this gives robust density estimates.

**2022 estimate (3,682)** makes India home to ~75% of the world's wild tigers.

*Sources: NTCA Status of Tigers in India reports (2006, 2010, 2014, 2018, 2022); 
Karanth & Nichols (1998) for PMR methodology.*
        """)

# ── Tab 4: Data table ──
with tab_data:
    st.markdown(section_header("Census Data with Imputation Flags",
        "Full State-Level Dataset — Purple Rows Contain Imputed Values"),
        unsafe_allow_html=True)

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        state_filter = st.multiselect("Filter by State", sorted(census["state"].unique()),
                                       key="data_state_filter")
    with f2:
        year_filter = st.multiselect("Filter by Year", sorted(census["year"].unique()),
                                      key="data_year_filter")
    with f3:
        imputed_only = st.checkbox("Show Imputed Records Only", key="imputed_only")

    display = census.copy()
    if state_filter:
        display = display[display["state"].isin(state_filter)]
    if year_filter:
        display = display[display["year"].isin(year_filter)]
    if imputed_only:
        display = display[display["was_imputed"] == True]

    show_cols = ["state", "year", "landscape", "population", "population_imputed",
                 "was_imputed", "imputation_method", "population_ci_lower",
                 "population_ci_upper", "population_ci_method"]
    st.dataframe(display[show_cols].sort_values(["state", "year"]),
                 use_container_width=True, hide_index=True)

    st.markdown(f'<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.markdown(section_header("Imputation Method Reference", "What Each Method Means for These Estimates"), unsafe_allow_html=True)

    method_list = census[census["was_imputed"] == True]["imputation_method"].dropna().unique()
    for m in method_list:
        with st.expander(f"🔬 {m.title()} Imputation"):
            subset = census[census["imputation_method"] == m].iloc[0]
            st.markdown(get_imputation_explanation(
                m,
                ci_lower=subset.get("population_ci_lower"),
                ci_upper=subset.get("population_ci_upper"),
                ci_method=subset.get("population_ci_method")
            ))
