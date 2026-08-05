"""
Page 4 - Mortality & Conflict
Tiger mortality (by cause) and human death (conflict) analysis across all states.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import (load_tiger_deaths, load_human_deaths,
                                get_imputation_explanation, load_funding_geographical_area_year)
from utils.map_utils import (GLOBAL_CSS, stat_card, stat_card_mini, section_header,
                              page_header, apply_dark_layout, divider,
                              ACCENT, ACCENT_LIGHT, ALERT, PRIMARY, PRIMARY_LIGHT,
                              PRIMARY_DARK, TEXT_COLOR, MUTED_TEXT, BORDER_SUBTLE,
                              SUCCESS, INFO, popout_link)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


with st.spinner("Loading mortality data..."):
    tdeaths = load_tiger_deaths()
    hdeaths = load_human_deaths()
    agg_df = load_funding_geographical_area_year()

# ── Derived stats ──
# Excel has tiger deaths from 2011 to 2025. Filter for 2012-2025 to match the caption "Recorded Deaths (2012-2025)"
total_tiger  = int(agg_df[(agg_df["year"] >= 2012) & (agg_df["year"] <= 2025)]["tiger_deaths"].sum())
total_human  = int(hdeaths["deaths_imputed"].sum())
total_poach  = int(tdeaths["deaths_poaching"].sum())
total_nat    = int(tdeaths["deaths_natural_other"].sum())
worst_state_h = (hdeaths.groupby("state")["deaths_imputed"].sum().idxmax())
worst_state_t = (tdeaths.groupby("state")["total_deaths_imputed"].sum().idxmax())
n_conflict   = int(hdeaths["has_conflict"].sum())
n_imputed_td = int(tdeaths["was_imputed"].sum())
n_imputed_hd = int(hdeaths["was_imputed"].sum())

# ── Page header ──
st.markdown(page_header(
    "Mortality & Conflict",
    "Tiger Deaths by Cause · Human Fatalities from Attacks · State-Level Hotspot Analysis",
    "⚠️"
), unsafe_allow_html=True)

# ── Stat cards ──
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(stat_card("Total Tiger Deaths", f"{total_tiger:,}",
        "All Recorded (2012–2025)", "#F97316"), unsafe_allow_html=True)
with c2:
    st.markdown(stat_card("Poaching Deaths", f"{total_poach:,}",
        f"{round(total_poach/max(total_tiger,1)*100)}% of Total", ALERT), unsafe_allow_html=True)
with c3:
    st.markdown(stat_card("Natural Deaths", f"{total_nat:,}",
        "Natural & Other Causes", PRIMARY_LIGHT), unsafe_allow_html=True)
with c4:
    st.markdown(stat_card("Human Fatalities", f"{total_human:,}",
        "Tiger-Attack Deaths (2015–2024)", "#DC2626"), unsafe_allow_html=True)
with c5:
    st.markdown(stat_card("Conflict Years", f"{n_conflict:,}",
        "State-Year Pairs with Conflict Flag", "#F59E0B"), unsafe_allow_html=True)

st.markdown(divider(), unsafe_allow_html=True)

# ── Tabs ──
tab_tiger, tab_human, tab_compare, tab_methods = st.tabs([
    "🐅  Tiger Mortality",
    "🏚️  Human Conflict",
    "📊  Side-by-Side",
    "🔬  Methodology"
])

# ══════════════════════════════════════════
# TAB 1: Tiger Mortality
# ══════════════════════════════════════════
with tab_tiger:
    st.markdown(section_header("Tiger deaths per year",
        "Stacked by Cause: Poaching, Natural, Unnatural (Non-Poaching), Seizures, Under Scrutiny"),
        unsafe_allow_html=True)

    # Year range filter
    yr_min, yr_max = int(tdeaths["year"].min()), int(tdeaths["year"].max())
    yr_range = st.slider("Year Range", yr_min, yr_max, (yr_min, yr_max), key="td_yr")
    td_filtered = tdeaths[(tdeaths["year"] >= yr_range[0]) & (tdeaths["year"] <= yr_range[1])]

    # National annual total by cause
    annual_td = td_filtered.groupby("year", as_index=False).agg(
        total=("total_deaths_imputed", "sum"),
        poaching=("deaths_poaching", "sum"),
        natural=("deaths_natural_other", "sum"),
        unnatural_np=("deaths_unnatural_nonp", "sum"),
        scrutiny=("deaths_scrutiny", "sum"),
    )

    # Merge with Excel for more accurate national total line
    try:
        annual_td = annual_td.merge(agg_df[["year", "tiger_deaths"]], on="year", how="left")
        annual_td["plot_total"] = annual_td["tiger_deaths"].fillna(annual_td["total"])
    except Exception:
        annual_td["plot_total"] = annual_td["total"]

    fig_td_nat = go.Figure()
    fig_td_nat.add_trace(go.Bar(
        x=annual_td["year"], y=annual_td["poaching"].fillna(0),
        name="Poaching", marker_color=ALERT,
        hovertemplate="<b>%{x}</b><br>Poaching: %{y:.0f}<extra></extra>"
    ))
    fig_td_nat.add_trace(go.Bar(
        x=annual_td["year"], y=annual_td["natural"].fillna(0),
        name="Natural / Other", marker_color=PRIMARY_LIGHT,
        hovertemplate="<b>%{x}</b><br>Natural: %{y:.0f}<extra></extra>"
    ))
    fig_td_nat.add_trace(go.Bar(
        x=annual_td["year"], y=annual_td["unnatural_np"].fillna(0),
        name="Unnatural (Non-Poaching)", marker_color="#F97316",
        hovertemplate="<b>%{x}</b><br>Unnatural (NP): %{y:.0f}<extra></extra>"
    ))
    fig_td_nat.add_trace(go.Bar(
        x=annual_td["year"], y=annual_td["scrutiny"].fillna(0),
        name="Under Scrutiny", marker_color="#FBBF24",
        hovertemplate="<b>%{x}</b><br>Scrutiny: %{y:.0f}<extra></extra>"
    ))
    fig_td_nat.add_trace(go.Scatter(
        x=annual_td["year"], y=annual_td["plot_total"],
        mode="lines+markers", name="Total (Official)",
        line=dict(color=TEXT_COLOR, width=2.5, dash="dot"),
        marker=dict(size=8, color=TEXT_COLOR),
        hovertemplate="<b>%{x}</b><br>Total (Official): %{y:.0f}<extra></extra>"
    ))
    apply_dark_layout(fig_td_nat, height=420, barmode="stack",
                      xaxis_title="Year", yaxis_title="Tiger Deaths")
    fig_td_nat.update_xaxes(type="category")
    popout_link(fig_td_nat, "mortality_tiger_yearly_popout", "Pop out chart")
    st.plotly_chart(fig_td_nat, use_container_width=True)

    st.markdown(section_header("Tiger Deaths by State",
        "Heatmap — Darker Indicates Higher Mortality"), unsafe_allow_html=True)

    state_yr = (td_filtered.groupby(["state", "year"], as_index=False)
                ["total_deaths_imputed"].sum())
    pivot = state_yr.pivot(index="state", columns="year", values="total_deaths_imputed").fillna(0)
    # Sort by total descending
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig_hm = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0, PRIMARY_DARK], [0.2, PRIMARY], [0.6, "#F97316"], [1, ALERT]],
        hovertemplate="<b>%{y}</b> · %{x}<br>Deaths: <b>%{z:.0f}</b><extra></extra>",
        name="",
        showscale=True,
        colorbar=dict(title=dict(text="Deaths", font=dict(size=10)),
                      thickness=14, len=0.8, tickfont=dict(size=9))
    ))
    apply_dark_layout(fig_hm, height=480, showlegend=False)
    fig_hm.update_xaxes(tickangle=-45, tickfont=dict(size=9))
    popout_link(fig_hm, "mortality_tiger_heatmap_popout", "Pop out chart")
    st.plotly_chart(fig_hm, use_container_width=True)

    # National seizures overlay
    seizure_states = tdeaths[tdeaths["national_seizures"].notna()]
    if len(seizure_states) > 0:
        st.markdown(section_header("National Wildlife Seizures (Reported Years)",
            "Number of Wildlife Seizure Operations Reported Nationally"), unsafe_allow_html=True)
        seiz_annual = (seizure_states.groupby("year")["national_seizures"]
                       .first().reset_index())
        seiz_annual["national_seizures"] = seiz_annual["national_seizures"].fillna(0)
        fig_seiz = go.Figure(go.Bar(
            x=seiz_annual["year"], y=seiz_annual["national_seizures"],
            marker_color=ACCENT,
            name="",
            text=[f"{int(v):,}" for v in seiz_annual["national_seizures"]],
            textposition="outside", textfont=dict(size=10, color=MUTED_TEXT),
            hovertemplate="<b>%{x}</b><br>Seizures: %{y:.0f}<extra></extra>"
        ))
        apply_dark_layout(fig_seiz, height=280, showlegend=False,
                          xaxis_title="Year", yaxis_title="Seizure Count")
        fig_seiz.update_xaxes(type="category")
        popout_link(fig_seiz, "mortality_seizure_popout", "Pop out chart")
        st.plotly_chart(fig_seiz, use_container_width=True)

# ══════════════════════════════════════════
# TAB 2: Human Conflict
# ══════════════════════════════════════════
with tab_human:
    st.markdown(section_header("Human Deaths from Tiger Attacks",
        "By State and Year · Orange = Observed, Yellow = Estimated"),
        unsafe_allow_html=True)

    yr_min_h = int(hdeaths["year"].min())
    yr_max_h = int(hdeaths["year"].max())
    yr_range_h = st.slider("Year Range", yr_min_h, yr_max_h, (yr_min_h, yr_max_h), key="hd_yr")
    hd_f = hdeaths[(hdeaths["year"] >= yr_range_h[0]) & (hdeaths["year"] <= yr_range_h[1])]

    # National annual totals
    hd_annual = hd_f.groupby("year", as_index=False).agg(
        total=("deaths_imputed", "sum"),
        obs=("deaths", "sum"),
    )

    fig_hd_nat = go.Figure()
    fig_hd_nat.add_trace(go.Scatter(
        x=hd_annual["year"], y=hd_annual["total"],
        mode="none", fill="tozeroy", fillcolor="rgba(239,68,68,0.07)",
        name="", showlegend=False
    ))
    fig_hd_nat.add_trace(go.Scatter(
        x=hd_annual["year"], y=hd_annual["total"],
        mode="lines+markers",
        name="Total (Including Estimated)",
        line=dict(color=ALERT, width=3, shape="spline"),
        marker=dict(size=9, color=ALERT, line=dict(width=2, color=PRIMARY_DARK)),
        hovertemplate="<b>%{x}</b><br>Deaths: <b>%{y:.0f}</b><extra></extra>"
    ))
    apply_dark_layout(fig_hd_nat, height=350,
                      xaxis_title="Year", yaxis_title="Human Deaths")
    fig_hd_nat.update_xaxes(type="category")
    popout_link(fig_hd_nat, "mortality_human_trend_popout", "Pop out chart")
    st.plotly_chart(fig_hd_nat, use_container_width=True)

    # State-level stacked bar
    st.markdown(section_header("Per-State Breakdown",
        "Top States by Total Human Fatalities"), unsafe_allow_html=True)

    state_hd = (hd_f.groupby("state", as_index=False)["deaths_imputed"].sum()
                .sort_values("deaths_imputed", ascending=False).head(12))
    state_hd["deaths_imputed"] = state_hd["deaths_imputed"].fillna(0)
    fig_sbar = go.Figure(go.Bar(
        x=state_hd["state"], y=state_hd["deaths_imputed"],
        marker=dict(
            color=state_hd["deaths_imputed"],
            colorscale=[[0, PRIMARY], [0.4, ACCENT], [0.7, "#F97316"], [1, ALERT]],
            showscale=False, line=dict(color=PRIMARY_DARK, width=0.5)
        ),
        name="",
        text=[f"{int(v):,}" for v in state_hd["deaths_imputed"]],
        textposition="outside", textfont=dict(size=10, color=MUTED_TEXT),
        hovertemplate="<b>%{x}</b><br>Deaths: %{y:.0f}<extra></extra>"
    ))
    apply_dark_layout(fig_sbar, height=380, showlegend=False,
                      xaxis_title="State", yaxis_title="Human Deaths")
    fig_sbar.update_xaxes(tickangle=-35)
    popout_link(fig_sbar, "mortality_state_bar_popout", "Pop out chart")
    st.plotly_chart(fig_sbar, use_container_width=True)

    # Conflict heatmap
    st.markdown(section_header("Conflict Heatmap",
        "State × Year · Shading = Deaths, Red Border = Conflict Flagged"), unsafe_allow_html=True)
    hd_pivot = hd_f.pivot_table(index="state", columns="year",
                                  values="deaths_imputed", aggfunc="sum").fillna(0)
    hd_pivot = hd_pivot.loc[hd_pivot.sum(axis=1).sort_values(ascending=False).index]

    fig_hm2 = go.Figure(go.Heatmap(
        z=hd_pivot.values,
        x=[str(c) for c in hd_pivot.columns],
        y=hd_pivot.index.tolist(),
        colorscale=[[0, PRIMARY_DARK], [0.3, PRIMARY], [0.7, ACCENT], [1, ALERT]],
        hovertemplate="<b>%{y}</b> · %{x}<br>Deaths: <b>%{z:.0f}</b><extra></extra>",
        name="",
        showscale=True,
        colorbar=dict(thickness=14, len=0.8, tickfont=dict(size=9))
    ))
    apply_dark_layout(fig_hm2, height=420, showlegend=False)
    fig_hm2.update_xaxes(tickangle=-45, tickfont=dict(size=9))
    popout_link(fig_hm2, "mortality_conflict_heatmap_popout", "Pop out chart")
    st.plotly_chart(fig_hm2, use_container_width=True)

# ══════════════════════════════════════════
# TAB 3: Side-by-Side
# ══════════════════════════════════════════
with tab_compare:
    st.markdown(section_header("Tiger vs. Human Deaths — Side by Side",
        "Annual Totals for Both Metrics Overlaid"), unsafe_allow_html=True)

    td_ann = tdeaths.groupby("year")["total_deaths_imputed"].sum().reset_index()
    hd_ann = hdeaths.groupby("year")["deaths_imputed"].sum().reset_index()
    merged = td_ann.merge(hd_ann, on="year", how="outer").sort_values("year")
    merged.columns = ["year", "tiger_deaths", "human_deaths"]

    fig_dual = go.Figure()
    fig_dual.add_trace(go.Bar(
        x=merged["year"], y=merged["tiger_deaths"].fillna(0),
        name="Tiger Deaths", marker_color="#F97316", opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Tiger Deaths: %{y:.0f}<extra></extra>"
    ))
    fig_dual.add_trace(go.Scatter(
        x=merged["year"], y=merged["human_deaths"].fillna(0),
        mode="lines+markers", name="Human Deaths",
        line=dict(color=ALERT, width=2.5), marker=dict(size=8, color=ALERT),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Human Deaths: %{y:.0f}<extra></extra>"
    ))
    apply_dark_layout(fig_dual, height=450, barmode="group",
                      xaxis_title="Year", yaxis_title="Tiger Deaths")
    fig_dual.update_layout(
        yaxis2=dict(
            title="Human Deaths", overlaying="y", side="right",
            gridcolor="rgba(255,255,255,0.03)",
            tickfont=dict(size=11, color=MUTED_TEXT),
            title_font=dict(size=12, color=MUTED_TEXT)
        )
    )
    fig_dual.update_xaxes(type="category")
    popout_link(fig_dual, "mortality_dual_popout", "Pop out chart")
    st.plotly_chart(fig_dual, use_container_width=True)

    # Correlation by state
    st.markdown(section_header("State-Level Correlation",
        "Do States with More Tiger Deaths Also Have More Human Deaths?"),
        unsafe_allow_html=True)
    td_st = tdeaths.groupby("state")["total_deaths_imputed"].sum().reset_index()
    hd_st = hdeaths.groupby("state")["deaths_imputed"].sum().reset_index()
    corr_df = td_st.merge(hd_st, on="state", how="inner")
    corr_df.columns = ["state", "tiger_deaths", "human_deaths"]
    # Ensure state labels are strings to avoid Plotly showing 'undefined'
    corr_df["state"] = corr_df["state"].fillna("").astype(str)

    fig_cor = px.scatter(
        corr_df, x="tiger_deaths", y="human_deaths", text="state",
        trendline="ols",
        color_discrete_sequence=[ACCENT]
    )
    fig_cor.update_traces(
        textposition="top center",
        textfont=dict(size=9, color=MUTED_TEXT),
        marker=dict(size=10, color=ACCENT, line=dict(color=PRIMARY_DARK, width=1),
                    opacity=0.85),
        hovertemplate="<b>%{text}</b><br>Tiger Deaths: %{x:,.0f}<br>Human Deaths: %{y:,.0f}<extra></extra>",
        selector=dict(mode="markers+text")
    )
    # Style trendline and set its hover template
    for trace in fig_cor.data:
        if hasattr(trace, 'mode') and trace.mode == "lines":  # OLS trendline
            trace.line = dict(color=ALERT, width=1.5, dash="dash")
            trace.hovertemplate = "OLS Trend<extra></extra>"
    apply_dark_layout(fig_cor, height=400,
                      xaxis_title="Tiger Deaths (Total)", yaxis_title="Human Deaths (Total)")
    popout_link(fig_cor, "mortality_correlation_popout", "Pop out chart")
    st.plotly_chart(fig_cor, use_container_width=True)

# ══════════════════════════════════════════
# TAB 4: Methodology
# ══════════════════════════════════════════
with tab_methods:
    st.markdown(section_header("Estimation Methods — Mortality Data",
        "How Gaps in Mortality Records Were Filled"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        td_imp = int(tdeaths["was_imputed"].sum())
        td_tot = len(tdeaths)
        badge1 = (
            f'<div style="background:rgba(22,43,35,0.4);border:1px solid {BORDER_SUBTLE};'
            f'border-radius:12px;padding:20px;margin-bottom:12px;">'
            f'<p style="color:#F97316;font-size:0.65rem;letter-spacing:2px;font-weight:700;margin:0 0 8px 0;">Tiger Deaths</p>'
            f'<p style="color:{TEXT_COLOR};font-size:1.8rem;font-weight:800;margin:0 0 2px 0;">{td_tot} Records</p>'
            f'<p style="color:{MUTED_TEXT};font-size:0.78rem;margin:0;">{td_imp} Imputed ({round(td_imp/max(td_tot,1)*100)}%)</p>'
            f'</div>'
        )
        st.markdown(badge1, unsafe_allow_html=True)
    with col2:
        hd_imp = int(hdeaths["was_imputed"].sum())
        hd_tot = len(hdeaths)
        badge2 = (
            f'<div style="background:rgba(22,43,35,0.4);border:1px solid {BORDER_SUBTLE};'
            f'border-radius:12px;padding:20px;margin-bottom:12px;">'
            f'<p style="color:{ALERT};font-size:0.65rem;letter-spacing:2px;font-weight:700;margin:0 0 8px 0;">Human Deaths</p>'
            f'<p style="color:{TEXT_COLOR};font-size:1.8rem;font-weight:800;margin:0 0 2px 0;">{hd_tot} Records</p>'
            f'<p style="color:{MUTED_TEXT};font-size:0.78rem;margin:0;">{hd_imp} Imputed ({round(hd_imp/max(hd_tot,1)*100)}%)</p>'
            f'</div>'
        )
        st.markdown(badge2, unsafe_allow_html=True)

    with st.expander("🔬 Tiger Mortality — Imputation Approach"):
        st.markdown(get_imputation_explanation("linear"))
        st.markdown("""
**Tiger mortality data** is drawn from multiple overlapping source files:
- `mortality_14-15`, `tigerdeaths_16-18`, `mortality_19-21`, `tigerdeaths_20-22`
- `tigerdeaths_unnaturalcauses` (for unnatural non-poaching deaths)

Where years are entirely absent for a state (e.g., 2015–2018 for some smaller states), 
the imputed value is held at the **mean of surrounding observed years** using linear interpolation.

The `was_imputed = True` flag marks these rows explicitly so they can be filtered out in analyses.
        """)

    with st.expander("🔬 Human Deaths — Imputation Approach"):
        st.markdown(get_imputation_explanation("none"))
        st.markdown("""
**Human death data** comes from:
- `tigerattacks_onhumans_15-18` — direct field records
- `tigerattacks_18-22`, `tigerattacks_20-22` — NTCA attack logs
- `humandeaths_19-23`, `humandeaths_20-24` — extended conflict logs
- `sundarbans_18-23` — Sundarbans-specific records (West Bengal / "Sundarbans" region)

Missing year-end records are imputed forward using a **constant-hold** strategy, 
or flagged as partial-year (`is_partial_year = True`). Confidence intervals use 
a t-distribution over the available state-level mean.
        """)

    with st.expander("📚 Source References"):
        st.markdown("""
| Source | Description |
|--------|-------------|
| NTCA Status of Tigers reports | Official camera-trap PMR census (2006, 2010, 2014, 2018, 2022) |
| WII mortality database | Wildlife Institute of India — cause-of-death classification |
| MoEFCC annual reports | Ministry of Environment — Project Tiger financial data |
| Sundarbans Tiger Reserve records | Special conflict monitoring (West Bengal Forest Dept.) |
| `pct_adult_tiger_deaths` | % adult tigers among total deaths (from WII scrutiny reports) |
        """)
