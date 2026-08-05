"""
Page 2 - State Explorer
Deep-dive into any state: census, funding, conflict, and tiger mortality in one pane.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import (load_census, load_funds, load_human_deaths,
                                load_tiger_deaths, get_states, load_reserves,
                                get_imputation_explanation)
from utils.map_utils import (GLOBAL_CSS, stat_card, stat_card_mini, section_header,
                              page_header, apply_dark_layout, divider,
                              ACCENT, ACCENT_LIGHT, ALERT, PRIMARY, PRIMARY_LIGHT,
                              PRIMARY_DARK, TEXT_COLOR, MUTED_TEXT, BORDER_SUBTLE,
                              BORDER_ACCENT, SUCCESS, INFO, popout_link)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


with st.spinner("Loading data..."):
    census  = load_census()
    funds   = load_funds()
    hdeaths = load_human_deaths()
    tdeaths = load_tiger_deaths()
    reserves = load_reserves()
    states  = get_states()

# ── Sidebar state selector ──
st.markdown(
    f'<p style="color:{ACCENT};font-size:0.7rem;font-weight:700;'
    f'letter-spacing:2px;margin:0 0 8px 0;">Select State</p>',
    unsafe_allow_html=True
)
selected_state = st.selectbox("State", states, key="state_sel")

with st.sidebar:
    st.markdown(
        f'<div style="height:1px;margin:12px 0;'
        f'background:linear-gradient(90deg,transparent,{BORDER_ACCENT},transparent);"></div>',
        unsafe_allow_html=True
    )
    # Quick landscape info
    state_landscapes = census[census["state"] == selected_state]["landscape"].dropna().unique()
    for lc in state_landscapes:
        if lc and lc.lower() != "unknown":
            st.markdown(
                f'<div style="background:rgba(22,43,35,0.35);border-left:3px solid {ACCENT}55;'
                f'border-radius:6px;padding:8px 10px;margin-bottom:8px;">'
                f'<p style="color:{MUTED_TEXT};font-size:0.68rem;margin:0;line-height:1.5;">{lc}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

# ── Filter data ──
s_census  = census[census["state"] == selected_state].sort_values("year")
s_funds   = funds[funds["state"] == selected_state].sort_values("year")
s_hdeaths = hdeaths[hdeaths["state"] == selected_state].sort_values("year")
s_tdeaths = tdeaths[tdeaths["state"] == selected_state].sort_values("year")
s_reserves = reserves[reserves["state"] == selected_state]

# ── Compute key metrics ──
pop_2022 = s_census[s_census["year"] == 2022]["population_imputed"].sum()
pop_2006 = s_census[s_census["year"] == 2006]["population_imputed"].sum()
pop_growth = round(((pop_2022 - pop_2006) / max(pop_2006, 1)) * 100, 1)
total_tiger_deaths = int(s_tdeaths["total_deaths_imputed"].sum())
total_human_deaths = int(s_hdeaths["deaths_imputed"].sum())
total_funds = s_funds["funds_best"].sum()
n_reserves = len(s_reserves)
pct_imputed = round(s_census["was_imputed"].mean() * 100, 0)

# ── Page header ──
trend_dir = "▲" if pop_growth >= 0 else "▼"
trend_col = SUCCESS if pop_growth >= 0 else ALERT
st.markdown(page_header(
    f"{selected_state}",
    f"State Tiger Profile · {n_reserves} Reserves · Census 2006–2022",
    "🔍"
), unsafe_allow_html=True)

# ── Stat row ──
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(stat_card("Tigers (2022)", f"{int(pop_2022):,}",
        f"{trend_dir} {abs(pop_growth)}% Since 2006", ACCENT), unsafe_allow_html=True)
with c2:
    st.markdown(stat_card("Tiger Reserves", str(n_reserves),
        "In This State", PRIMARY_LIGHT), unsafe_allow_html=True)
with c3:
    st.markdown(stat_card("Total Funds", f"₹{total_funds:,.0f}L" if total_funds else "N/A",
        "Conservation Allocation", INFO), unsafe_allow_html=True)
with c4:
    st.markdown(stat_card("Tiger Deaths", str(total_tiger_deaths),
        "All Recorded Mortalities", "#F97316"), unsafe_allow_html=True)
with c5:
    st.markdown(stat_card("Human Deaths", str(total_human_deaths),
        "Tiger Attack Fatalities", ALERT), unsafe_allow_html=True)

st.markdown(divider(), unsafe_allow_html=True)

# ── Main tabs ──
tab_pop, tab_funds, tab_mort, tab_reserves, tab_methods = st.tabs([
    "🐯  Population",
    "💰  Funding",
    "⚠️  Mortality & Conflict",
    "🌿  Reserves",
    "🔬  Methodology"
])

# ══════════════════════════════════════════
# TAB 1: Population
# ══════════════════════════════════════════
with tab_pop:
    st.markdown(section_header("Census Population Trend",
        "State-Level Estimates with 95% Confidence Interval Bands"), unsafe_allow_html=True)

    if len(s_census) == 0:
        st.warning(f"No census data available for {selected_state}.")
    else:
        fig = go.Figure()

        # CI band
        ci_df = s_census.dropna(subset=["population_ci_lower", "population_ci_upper"])
        if len(ci_df) > 0:
            x_band = ci_df["year"].tolist() + ci_df["year"].tolist()[::-1]
            y_band = ci_df["population_ci_upper"].tolist() + ci_df["population_ci_lower"].tolist()[::-1]
            fig.add_trace(go.Scatter(
                x=x_band, y=y_band,
                fill="toself",
                fillcolor=f"rgba(245,158,11,0.08)",
                line=dict(color="rgba(0,0,0,0)"),
                name="95% CI", showlegend=True,
                hoverinfo="skip"
            ))

        # Actual vs imputed distinction
        actual = s_census[s_census["was_imputed"] == False]
        imputed = s_census[s_census["was_imputed"] == True]

        fig.add_trace(go.Scatter(
            x=actual["year"], y=actual["population_imputed"],
            mode="lines+markers",
            name="Observed",
            line=dict(color=ACCENT, width=3, shape="spline"),
            marker=dict(size=10, color=ACCENT, line=dict(width=2, color=PRIMARY_DARK)),
            hovertemplate="<b>%{x}</b><br>Observed: <b>%{y:,}</b><extra></extra>"
        ))
        if len(imputed) > 0:
            fig.add_trace(go.Scatter(
                x=imputed["year"], y=imputed["population_imputed"],
                mode="markers",
                name="Imputed",
                marker=dict(size=10, color="#A78BFA", symbol="diamond",
                            line=dict(width=2, color=PRIMARY_DARK)),
                hovertemplate="<b>%{x}</b><br>Imputed: <b>%{y:,}</b><extra></extra>"
            ))

        apply_dark_layout(fig, height=400,
                          xaxis_title="Census Year", yaxis_title="Tiger Population")
        fig.update_xaxes(type="category")
        popout_link(fig, "state_pop_trend_popout", "Pop out chart")
        st.plotly_chart(fig, use_container_width=True)

        # Data table
        with st.expander("View raw census data"):
            show = s_census[["year", "population", "population_imputed", "was_imputed",
                              "imputation_method", "population_ci_lower", "population_ci_upper",
                              "population_ci_method", "landscape"]].copy()
            st.dataframe(show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════
# TAB 2: Funding
# ══════════════════════════════════════════
with tab_funds:
    st.markdown(section_header("Conservation Funding Over Time",
        "Project Tiger Fund (TPF), Central Share, and State Allocation (₹ Lakh)"),
        unsafe_allow_html=True)

    if len(s_funds) == 0:
        st.warning(f"No funding data available for {selected_state}.")
    else:
        fig_f = go.Figure()

        if s_funds["funds_total_including_tpf"].notna().any():
            fig_f.add_trace(go.Bar(
                x=s_funds["year"], y=s_funds["funds_total_including_tpf"],
                name="Total incl. TPF", marker_color=ACCENT,
                hovertemplate="<b>%{x}</b><br>Total (TPF): ₹%{y:,.2f} L<extra></extra>"
            ))
        if s_funds["funds_central_share"].notna().any():
            fig_f.add_trace(go.Bar(
                x=s_funds["year"], y=s_funds["funds_central_share"],
                name="Central Share", marker_color=PRIMARY_LIGHT,
                hovertemplate="<b>%{x}</b><br>Central: ₹%{y:,.2f} L<extra></extra>"
            ))
        if s_funds["funds_state_allocation"].notna().any():
            fig_f.add_trace(go.Bar(
                x=s_funds["year"], y=s_funds["funds_state_allocation"],
                name="State Allocation", marker_color=INFO,
                hovertemplate="<b>%{x}</b><br>State: ₹%{y:,.2f} L<extra></extra>"
            ))

        apply_dark_layout(fig_f, height=400, barmode="group",
                          xaxis_title="Year", yaxis_title="Amount (₹ Lakh)")
        fig_f.update_xaxes(type="category")
        popout_link(fig_f, "state_funding_popout", "Pop out chart")
        st.plotly_chart(fig_f, use_container_width=True)

        # CI for funds
        f_with_ci = s_funds.dropna(subset=["funds_total_including_tpf_ci_lower",
                                            "funds_total_including_tpf_ci_upper"])
        if len(f_with_ci) > 0:
            with st.expander("📊 Funding Confidence Intervals"):
                st.caption("95% CI on the total-including-TPF figure (t-distribution over available years).")
                ci_tbl = f_with_ci[["year", "funds_total_including_tpf",
                                     "funds_total_including_tpf_ci_lower",
                                     "funds_total_including_tpf_ci_upper",
                                     "funds_total_including_tpf_ci_method"]].copy()
                ci_tbl.columns = ["Year", "Total (₹L)", "CI Lower", "CI Upper", "CI Method"]
                st.dataframe(ci_tbl, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════
# TAB 3: Mortality & Conflict
# ══════════════════════════════════════════
with tab_mort:
    m_left, m_right = st.columns(2)

    with m_left:
        st.markdown(section_header("Tiger Mortality", "By Year and Cause"), unsafe_allow_html=True)
        if len(s_tdeaths) == 0:
            st.info("No tiger mortality data for this state.")
        else:
            fig_td = go.Figure()
            if s_tdeaths["deaths_poaching"].notna().any():
                fig_td.add_trace(go.Bar(
                    x=s_tdeaths["year"], y=s_tdeaths["deaths_poaching"],
                    name="Poaching", marker_color=ALERT,
                    hovertemplate="<b>%{x}</b><br>Poaching: %{y:.0f}<extra></extra>"
                ))
            if s_tdeaths["deaths_natural_other"].notna().any():
                fig_td.add_trace(go.Bar(
                    x=s_tdeaths["year"], y=s_tdeaths["deaths_natural_other"],
                    name="Natural / Other", marker_color=PRIMARY_LIGHT,
                    hovertemplate="<b>%{x}</b><br>Natural: %{y:.0f}<extra></extra>"
                ))
            fig_td.add_trace(go.Scatter(
                x=s_tdeaths["year"], y=s_tdeaths["total_deaths_imputed"],
                mode="lines+markers", name="Total Deaths",
                line=dict(color=ACCENT, width=2.5, dash="dot"),
                marker=dict(size=8, color=ACCENT),
                hovertemplate="<b>%{x}</b><br>Total: %{y:.0f}<extra></extra>"
            ))
            apply_dark_layout(fig_td, height=380, barmode="stack",
                              xaxis_title="Year", yaxis_title="Deaths")
            fig_td.update_xaxes(type="category")
            popout_link(fig_td, "state_tiger_mortality_popout", "Pop out chart")
            st.plotly_chart(fig_td, use_container_width=True)

    with m_right:
        st.markdown(section_header("Human Fatalities", "Deaths Due to Tiger Attacks"), unsafe_allow_html=True)
        if len(s_hdeaths) == 0:
            st.info("No human death data for this state.")
        else:
            obs = s_hdeaths[s_hdeaths["was_imputed"] == False]
            imp = s_hdeaths[s_hdeaths["was_imputed"] == True]

            fig_hd = go.Figure()
            if len(obs) > 0:
                fig_hd.add_trace(go.Bar(
                    x=obs["year"], y=obs["deaths_imputed"],
                    name="Observed", marker_color="#F97316",
                    hovertemplate="<b>%{x}</b><br>Deaths (obs): %{y:.0f}<extra></extra>"
                ))
            if len(imp) > 0:
                fig_hd.add_trace(go.Bar(
                    x=imp["year"], y=imp["deaths_imputed"],
                    name="Estimated", marker_color="#FCD34D",
                    hovertemplate="<b>%{x}</b><br>Deaths (est): %{y:.0f}<extra></extra>"
                ))
            apply_dark_layout(fig_hd, height=380, barmode="stack",
                              xaxis_title="Year", yaxis_title="Human Deaths")
            fig_hd.update_xaxes(type="category")
            popout_link(fig_hd, "state_human_deaths_popout", "Pop out chart")
            st.plotly_chart(fig_hd, use_container_width=True)

    # Conflict flag
    has_conflict_years = s_hdeaths[s_hdeaths["has_conflict"] == True]["year"].tolist()
    if has_conflict_years:
        st.warning(
            f"⚠️ **Conflict flagged in years:** {', '.join(str(y) for y in sorted(has_conflict_years))}  \n"
            f"These years had officially recorded human-wildlife conflict incidents."
        )

# ══════════════════════════════════════════
# TAB 4: Reserves
# ══════════════════════════════════════════
with tab_reserves:
    st.markdown(section_header(f"Tiger Reserves in {selected_state}",
        f"{n_reserves} Reserves · Areas from NTCA Official Records"),
        unsafe_allow_html=True)

    if len(s_reserves) == 0:
        st.info("No reserve data available for this state.")
    else:
        for _, row in s_reserves.iterrows():
            total_area = int(row["core_area_km2"] + row["buffer_area_km2"])
            
            # Formatting fragmentation score
            frag = row.get("fragmentation_score")
            if pd.isna(frag):
                frag_html = '<span style="color:#94A3B8;">N/A</span>'
            else:
                frag_color = ALERT if frag >= 0.5 else (ACCENT if frag >= 0.3 else SUCCESS)
                frag_html = f'<span style="color:{frag_color};font-weight:700;">{frag:.2f}</span>'
                
            r_html = (
                f'<div style="background:linear-gradient(135deg,rgba(22,43,35,0.5),rgba(14,17,23,0.7));'
                f'border:1px solid {BORDER_SUBTLE};border-left:3px solid {ACCENT}55;'
                f'border-radius:12px;padding:16px 20px;margin-bottom:10px;'
                f'display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
                f'<div>'
                f'<h3 style="color:{TEXT_COLOR};font-size:1rem;font-weight:700;margin:0 0 4px 0;">'
                f'{row["reserve_name"]}</h3>'
                f'<p style="color:{MUTED_TEXT};font-size:0.75rem;margin:0;">'
                f'{row["latitude"]:.2f}°N, {row["longitude"]:.2f}°E</p>'
                f'</div>'
                f'<div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center;">'
                f'<div style="text-align:center;">'
                f'<p style="color:{ACCENT};font-size:1rem;font-weight:700;margin:0;">{int(row["core_area_km2"]):,}</p>'
                f'<p style="color:{MUTED_TEXT};font-size:0.65rem;margin:0;">Core km²</p></div>'
                f'<div style="text-align:center;">'
                f'<p style="color:{INFO};font-size:1rem;font-weight:700;margin:0;">{int(row["buffer_area_km2"]):,}</p>'
                f'<p style="color:{MUTED_TEXT};font-size:0.65rem;margin:0;">Buffer km²</p></div>'
                f'<div style="text-align:center;">'
                f'<p style="color:{SUCCESS};font-size:1rem;font-weight:700;margin:0;">{total_area:,}</p>'
                f'<p style="color:{MUTED_TEXT};font-size:0.65rem;margin:0;">Total km²</p></div>'
                f'<div style="text-align:center;border-left:1px solid rgba(255,255,255,0.1);padding-left:15px;">'
                f'<p style="font-size:1rem;margin:0;line-height:1;">{frag_html}</p>'
                f'<p style="color:{MUTED_TEXT};font-size:0.65rem;margin:4px 0 0 0;">Frag. Score</p></div>'
                f'</div></div>'
            )
            st.markdown(r_html, unsafe_allow_html=True)

        st.info(
            "💡 **Reserve-level population estimates** are proportionally distributed from "
            "the state census. Visit the **National Overview** page and click a reserve bubble for detail."
        )

# ══════════════════════════════════════════
# TAB 5: Methodology
# ══════════════════════════════════════════
with tab_methods:
    st.markdown(section_header("Estimation & Imputation Methods",
        f"Transparency report for {selected_state}"), unsafe_allow_html=True)

    # Census methods
    census_methods = s_census[s_census["was_imputed"] == True]
    funds_na = s_funds[s_funds["funds_best"].isna()]

    col_a, col_b = st.columns(2)
    with col_a:
        m_badge = (
            f'<div style="background:rgba(22,43,35,0.4);border:1px solid {BORDER_SUBTLE};'
            f'border-radius:12px;padding:20px;margin-bottom:12px;">'
            f'<p style="color:{ACCENT};font-size:0.65rem;letter-spacing:2px;font-weight:700;'
            f'margin:0 0 8px 0;">Census Data</p>'
            f'<p style="color:{TEXT_COLOR};font-size:1.8rem;font-weight:800;margin:0 0 2px 0;">'
            f'{len(s_census)} Records</p>'
            f'<p style="color:{MUTED_TEXT};font-size:0.78rem;margin:0;">'
            f'{len(census_methods)} Imputed ({pct_imputed:.0f}%)</p>'
            f'</div>'
        )
        st.markdown(m_badge, unsafe_allow_html=True)

    with col_b:
        methods_found = s_census["imputation_method"].dropna().unique()
        methods_used = [m for m in methods_found if m.lower() != "none"]
        m_list = ", ".join(m.title() for m in methods_used) if methods_used else "Direct Observation Only"
        m2_badge = (
            f'<div style="background:rgba(22,43,35,0.4);border:1px solid {BORDER_SUBTLE};'
            f'border-radius:12px;padding:20px;margin-bottom:12px;">'
            f'<p style="color:#A78BFA;font-size:0.65rem;letter-spacing:2px;font-weight:700;'
            f'margin:0 0 8px 0;">Methods Used</p>'
            f'<p style="color:{TEXT_COLOR};font-size:0.95rem;font-weight:700;margin:0 0 2px 0;">'
            f'{m_list}</p>'
            f'<p style="color:{MUTED_TEXT};font-size:0.78rem;margin:0;">For Census Imputation</p>'
            f'</div>'
        )
        st.markdown(m2_badge, unsafe_allow_html=True)

    if len(census_methods) > 0:
        st.markdown(f'<div style="height:8px;"></div>', unsafe_allow_html=True)
        for _, row in census_methods.iterrows():
            method = str(row.get("imputation_method", "none"))
            if method.lower() == "none":
                continue
            with st.expander(
                f"Year {int(row['year'])} — {method.title()} Imputation "
                f"(pop: {int(row['population_imputed']):,})"
            ):
                st.markdown(get_imputation_explanation(
                    method,
                    ci_lower=row.get("population_ci_lower"),
                    ci_upper=row.get("population_ci_upper"),
                    ci_method=row.get("population_ci_method")
                ))
                st.markdown(
                    f"**Source file:** `{row.get('source_file', 'N/A')}`  \n"
                    f"**Landscape:** {row.get('landscape', 'N/A')}"
                )
    else:
        st.success(f"✅ All Census Values for {selected_state} Are Directly Observed — No Imputation Required.")
