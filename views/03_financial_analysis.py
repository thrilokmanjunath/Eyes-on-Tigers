"""
Page 3 - Financial Analysis
Conservation fund allocation — central share, TPF, and state contributions over time.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import load_funds, get_imputation_explanation, load_funding_geographical_area_year
from utils.map_utils import (GLOBAL_CSS, stat_card, stat_card_mini, section_header,
                              page_header, apply_dark_layout, divider,
                              ACCENT, ACCENT_LIGHT, ALERT, PRIMARY, PRIMARY_LIGHT,
                              PRIMARY_DARK, TEXT_COLOR, MUTED_TEXT, BORDER_SUBTLE,
                              SUCCESS, INFO, popout_link)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


with st.spinner("Loading funding data..."):
    funds = load_funds()
    agg_df = load_funding_geographical_area_year()

# ── Derived stats ──
total_funds     = agg_df["total_funding"].sum()
total_central   = funds["funds_central_share"].sum()
total_tpf       = funds["funds_total_including_tpf"].sum()
total_state_all = funds["funds_state_allocation"].sum()
n_states        = funds["state"].nunique()
top_funded_state = (funds.groupby("state")["funds_best"].sum()
                    .idxmax() if funds["funds_best"].sum() > 0 else "N/A")
avg_annual      = agg_df["total_funding"].mean()

# ── Page header ──
st.markdown(page_header(
    "Financial Analysis",
    "Conservation Funding Trends · Project Tiger Fund · Central & State Allocations",
    "💰"
), unsafe_allow_html=True)

# ── Stat cards ──
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(stat_card("Total Funds (All Years)", f"₹{total_funds:,.0f}L",
        "Best Available Estimate", ACCENT), unsafe_allow_html=True)
with c2:
    st.markdown(stat_card("States Covered", str(n_states),
        "With Funding Records", PRIMARY_LIGHT), unsafe_allow_html=True)
with c3:
    st.markdown(stat_card("Top Funded State", top_funded_state,
        "Highest Cumulative Allocation", INFO), unsafe_allow_html=True)
with c4:
    st.markdown(stat_card("Avg. Annual Total", f"₹{avg_annual:,.0f}L",
        "Across All States per Year", SUCCESS), unsafe_allow_html=True)

st.markdown(divider(), unsafe_allow_html=True)

# ── Tabs ──
tab_overview, tab_state, tab_trend, tab_data = st.tabs([
    "📊  All-State Overview",
    "🔍  Per-State Deep-Dive",
    "📈  Annual Trends",
    "📋  Raw Data"
])

# ══════════════════════════════════════════
# TAB 1: All-State Overview
# ══════════════════════════════════════════
with tab_overview:
    st.markdown(section_header("Total Funding per State",
        "Cumulative Funds Across All Recorded Years — All Sources Combined"),
        unsafe_allow_html=True)

    state_total = (funds.groupby("state", as_index=False)
                   .agg(
                       total=("funds_best", "sum"),
                       central=("funds_central_share", "sum"),
                       tpf=("funds_total_including_tpf", "sum"),
                       state_alloc=("funds_state_allocation", "sum"),
                   )
                   .sort_values("total", ascending=True))

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        y=state_total["state"], x=state_total["tpf"].fillna(0),
        name="Total incl. TPF", orientation="h",
        marker_color=ACCENT, opacity=0.9,
        hovertemplate="<b>%{y}</b><br>TPF Total: ₹%{x:,.0f} L<extra></extra>"
    ))
    fig1.add_trace(go.Bar(
        y=state_total["state"], x=state_total["central"].fillna(0),
        name="Central Share", orientation="h",
        marker_color=PRIMARY_LIGHT,
        hovertemplate="<b>%{y}</b><br>Central: ₹%{x:,.0f} L<extra></extra>"
    ))
    fig1.add_trace(go.Bar(
        y=state_total["state"], x=state_total["state_alloc"].fillna(0),
        name="State Allocation", orientation="h",
        marker_color=INFO,
        hovertemplate="<b>%{y}</b><br>State: ₹%{x:,.0f} L<extra></extra>"
    ))

    apply_dark_layout(fig1, height=520, barmode="overlay",
                      xaxis_title="Amount (₹ Lakh)", yaxis_title="")
    popout_link(fig1, "finance_all_state_popout", "Pop out chart")
    st.plotly_chart(fig1, use_container_width=True)

    # Bubble chart: funding vs tiger count proxy
    st.markdown(section_header("Funding Concentration",
        "Bubble Size = Number of Years with Data; Color = Average Annual Funding"),
        unsafe_allow_html=True)
    state_agg = (funds.groupby("state", as_index=False)
                 .agg(avg_annual=("funds_best", "mean"),
                      n_years=("year", "count"),
                      total=("funds_best", "sum")))

    _bubble_df = state_agg.dropna(subset=["avg_annual"]).copy()
    # Ensure state label is present for Plotly `text` and hover
    _bubble_df["state"] = _bubble_df["state"].fillna("").astype(str)
    fig_b = px.scatter(
        _bubble_df,
        x="total", y="avg_annual",
        size="n_years", color="avg_annual",
        text="state",
        custom_data=["n_years"],
        color_continuous_scale=[[0, PRIMARY], [0.5, ACCENT], [1, ACCENT_LIGHT]],
        hover_data={"n_years": False, "total": False, "avg_annual": False},
    )
    fig_b.update_traces(
        textposition="top center",
        textfont=dict(size=9, color=MUTED_TEXT),
        marker=dict(line=dict(color=PRIMARY_DARK, width=1), opacity=0.85),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Total: ₹%{x:,.0f} L<br>"
            "Avg/Year: ₹%{y:,.0f} L<br>"
            "Years of Data: %{customdata[0]:.0f}<extra></extra>"
        )
    )
    apply_dark_layout(fig_b, height=420, showlegend=False,
                      xaxis_title="Total Funds (₹ Lakh)", yaxis_title="Avg Annual (₹ Lakh)")
    fig_b.update_coloraxes(showscale=False)
    popout_link(fig_b, "finance_bubble_popout", "Pop out chart")
    st.plotly_chart(fig_b, use_container_width=True)

# ══════════════════════════════════════════
# TAB 2: Per-State Deep-Dive
# ══════════════════════════════════════════
with tab_state:
    all_states = sorted(funds["state"].unique().tolist())
    sel_state = st.selectbox("Select State", all_states, key="fund_state")
    st.markdown(section_header(f"Funding History — {sel_state}", "Year-by-Year Breakdown"),
        unsafe_allow_html=True)

    s_funds = funds[funds["state"] == sel_state].sort_values("year")

    if len(s_funds) == 0:
        st.warning(f"No funding records for {sel_state}.")
    else:
        # Summary mini-cards
        sm1, sm2, sm3 = st.columns(3)
        with sm1:
            st.markdown(stat_card_mini("Total Recorded", f"₹{s_funds['funds_best'].sum():,.0f} L", ACCENT),
                        unsafe_allow_html=True)
        with sm2:
            st.markdown(stat_card_mini("Best Year", str(int(s_funds.loc[s_funds["funds_best"].idxmax(), "year"]))
                                       if s_funds["funds_best"].notna().any() else "N/A", SUCCESS),
                        unsafe_allow_html=True)
        with sm3:
            st.markdown(stat_card_mini("Avg / Year", f"₹{s_funds['funds_best'].mean():,.0f} L", INFO),
                        unsafe_allow_html=True)

        st.markdown(f'<div style="height:12px;"></div>', unsafe_allow_html=True)

        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=s_funds["year"], y=s_funds["funds_total_including_tpf"],
            name="Total incl. TPF", marker_color=ACCENT, opacity=0.85,
            hovertemplate="<b>%{x}</b><br>TPF Total: ₹%{y:,.2f} L<extra></extra>"
        ))
        fig_s.add_trace(go.Bar(
            x=s_funds["year"], y=s_funds["funds_central_share"],
            name="Central Share", marker_color=PRIMARY_LIGHT,
            hovertemplate="<b>%{x}</b><br>Central: ₹%{y:,.2f} L<extra></extra>"
        ))
        fig_s.add_trace(go.Bar(
            x=s_funds["year"], y=s_funds["funds_state_allocation"],
            name="State Alloc.", marker_color=INFO,
            hovertemplate="<b>%{x}</b><br>State: ₹%{y:,.2f} L<extra></extra>"
        ))

        # CI band on best figure
        ci_df = s_funds.dropna(subset=["funds_total_including_tpf_ci_lower",
                                        "funds_total_including_tpf_ci_upper"])
        if len(ci_df) > 0:
            fig_s.add_trace(go.Scatter(
                x=ci_df["year"].tolist() + ci_df["year"].tolist()[::-1],
                y=ci_df["funds_total_including_tpf_ci_upper"].tolist()
                  + ci_df["funds_total_including_tpf_ci_lower"].tolist()[::-1],
                fill="toself", fillcolor="rgba(245,158,11,0.06)",
                line=dict(color="rgba(0,0,0,0)"),
                name="95% CI", hoverinfo="skip"
            ))

        apply_dark_layout(fig_s, height=420, barmode="group",
                          xaxis_title="Year", yaxis_title="Amount (₹ Lakh)")
        fig_s.update_xaxes(type="category")
        popout_link(fig_s, "finance_state_detail_popout", "Pop out chart")
        st.plotly_chart(fig_s, use_container_width=True)

# ══════════════════════════════════════════
# TAB 3: Annual Trends
# ══════════════════════════════════════════
with tab_trend:
    st.markdown(section_header("National Funding Trend",
        "Total Conservation Funds Released Across All States per Year"),
        unsafe_allow_html=True)

    annual_csv = funds.groupby("year", as_index=False).agg(
        central=("funds_central_share", "sum"),
        tpf=("funds_total_including_tpf", "sum"),
    ).sort_values("year")

    agg_df_sorted = agg_df.sort_values("year")

    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(
        x=agg_df_sorted["year"], y=agg_df_sorted["total_funding"],
        mode="lines+markers+text",
        name="Total Funding (Official)", line=dict(color=ACCENT, width=3, shape="spline"),
        marker=dict(size=9, color=ACCENT, line=dict(width=2, color=PRIMARY_DARK)),
        text=[f"\u20b9{int(v):,}" if (pd.notna(v) and i % 3 == 0) else "" for i, v in enumerate(agg_df_sorted["total_funding"])],
        textposition="top center", textfont=dict(size=9, color=MUTED_TEXT),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.05)",
        hovertemplate="<b>%{x}</b><br>Total: \u20b9%{y:,.0f} L<extra></extra>"
    ))
    fig_t.add_trace(go.Scatter(
        x=annual_csv["year"], y=annual_csv["central"].fillna(0),
        mode="lines+markers", name="Central Share",
        line=dict(color=PRIMARY_LIGHT, width=2, dash="dash"),
        marker=dict(size=7, color=PRIMARY_LIGHT),
        hovertemplate="<b>%{x}</b><br>Central: ₹%{y:,.0f} L<extra></extra>"
    ))

    apply_dark_layout(fig_t, height=420,
                      xaxis_title="Year", yaxis_title="Amount (₹ Lakh)")
    fig_t.update_xaxes(type="category")
    popout_link(fig_t, "finance_national_trend_popout", "Pop out chart")
    st.plotly_chart(fig_t, use_container_width=True)

    # Year-on-year change
    st.markdown(section_header("Year-on-Year Change",
        "Absolute Change in Total Funding Versus Prior Year"), unsafe_allow_html=True)
    agg_df_sorted["yoy_change"] = agg_df_sorted["total_funding"].diff()
    annual_yoy = agg_df_sorted.dropna(subset=["yoy_change"])

    fig_yoy = go.Figure(go.Bar(
        x=annual_yoy["year"],
        y=annual_yoy["yoy_change"],
        marker_color=[SUCCESS if v >= 0 else ALERT for v in annual_yoy["yoy_change"]],
        name="",
        hovertemplate="<b>%{x}</b><br>Change: ₹%{y:+,.0f} L<extra></extra>",
        text=[f"₹{int(v):+,}" for v in annual_yoy["yoy_change"]],
        textposition="outside",
        textfont=dict(size=9, color=MUTED_TEXT)
    ))
    apply_dark_layout(fig_yoy, height=300, showlegend=False,
                      xaxis_title="Year", yaxis_title="ΔFunds (₹ Lakh)")
    fig_yoy.update_xaxes(type="category")
    fig_yoy.add_hline(y=0, line_color="rgba(255,255,255,0.15)", line_width=1)
    popout_link(fig_yoy, "finance_yoy_popout", "Pop out chart")
    st.plotly_chart(fig_yoy, use_container_width=True)

# ══════════════════════════════════════════
# TAB 4: Raw Data
# ══════════════════════════════════════════
with tab_data:
    st.markdown(section_header("Raw Funding Data", "Full Dataset With CI Bounds"),
        unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    with f1:
        state_filter = st.multiselect("State", sorted(funds["state"].unique()), key="raw_state")
    with f2:
        year_filter = st.multiselect("Year", sorted(funds["year"].unique()), key="raw_year")

    display = funds.copy()
    if state_filter:
        display = display[display["state"].isin(state_filter)]
    if year_filter:
        display = display[display["year"].isin(year_filter)]

    st.dataframe(display.sort_values(["state", "year"]),
                 use_container_width=True, hide_index=True)

    with st.expander("📚 Understanding the Funding Data"):
        st.markdown("""
**Funding sources in this dataset:**

| Column | Description |
|--------|-------------|
| `funds_central_share` | Central government allocation under Project Tiger (₹ Lakh) |
| `funds_release_amount` | Amount actually released to states (may differ from allocation) |
| `funds_state_allocation` | State government's own contribution |
| `funds_total_including_tpf` | Total funds including Tiger Protection Fund (preferred figure) |
| `funds_best` | Best available value: TPF total → Central share (in that priority) |

**Confidence Intervals** are computed using a t-distribution over the available annual observations per state.

*Sources: Annual Reports of Project Tiger (NTCA), Ministry of Environment, Forest and Climate Change (MoEFCC).*
        """)
