"""
Eyes on Tigers (EoT) Home Page — rich insights from real imputed state-level data.
"""
import streamlit as st
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import (load_census, load_funds, load_human_deaths,
                                load_tiger_deaths, get_national_trend_df,
                                get_state_summary, load_funding_geographical_area_year)
from utils.map_utils import (GLOBAL_CSS, stat_card, section_header, apply_dark_layout,
                              ACCENT, ACCENT_LIGHT, ALERT, PRIMARY, PRIMARY_LIGHT,
                              PRIMARY_DARK, TEXT_COLOR, MUTED_TEXT,
                              BORDER_SUBTLE, BORDER_ACCENT, SUCCESS, INFO, popout_link)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Load data ──
with st.spinner("Loading data..."):
    census   = load_census()
    funds    = load_funds()
    hdeaths  = load_human_deaths()
    tdeaths  = load_tiger_deaths()
    national = get_national_trend_df()
    summary  = get_state_summary()
    agg_df   = load_funding_geographical_area_year()

# ── Key metrics ──
total_2022   = int(agg_df[agg_df["year"] == 2022]["tiger_count"].values[0])
total_2006   = int(agg_df[agg_df["year"] == 2006]["tiger_count"].values[0])
growth_pct   = round(((total_2022 - total_2006) / max(total_2006, 1)) * 100, 1)
total_funds  = agg_df["total_funding"].sum()
total_human  = int(hdeaths["deaths_imputed"].sum())
# Excel has tiger deaths from 2011 to 2025. Filter for 2012-2025 to match the caption "Recorded Deaths (2012-2025)"
total_tiger  = int(agg_df[(agg_df["year"] >= 2012) & (agg_df["year"] <= 2025)]["tiger_deaths"].sum())
states_count = census["state"].nunique()
top_state    = summary.sort_values("pop_2022", ascending=False).iloc[0]["state"]
most_deaths  = summary.sort_values("human_deaths_total", ascending=False).iloc[0]["state"]

# ── Sidebar info ──
with st.sidebar:
    sb = (
        f'<div style="text-align:center;padding:20px 10px 16px 10px;">'
        f'<div style="width:64px;height:64px;margin:0 auto 12px auto;'
        f'background:linear-gradient(135deg,{PRIMARY},{PRIMARY_LIGHT});'
        f'border-radius:16px;display:flex;align-items:center;justify-content:center;'
        f'font-size:2rem;border:1px solid {ACCENT}22;'
        f'box-shadow:0 4px 20px rgba(0,0,0,0.3),0 0 40px {PRIMARY}44;">🐯</div>'
        f'<h1 style="color:{TEXT_COLOR};font-size:1.4rem;margin:0;font-weight:900;'
        f'letter-spacing:3px;">EoT</h1>'
        f'<div style="width:40px;height:2px;background:linear-gradient(90deg,{ACCENT},transparent);'
        f'margin:8px auto;"></div>'
        f'<p style="color:{MUTED_TEXT};font-size:0.62rem;margin:0;'
        f'letter-spacing:1px;line-height:1.6;opacity:0.7;">'
        f'EYES ON TIGERS<br>EFFECTIVENESS MONITORING</p>'
        f'</div>'
        f'<div style="height:1px;margin:8px 16px;'
        f'background:linear-gradient(90deg,transparent,{BORDER_ACCENT},transparent);"></div>'
        f'<div style="padding:12px 8px;">'
        f'<p style="color:{MUTED_TEXT};font-size:0.7rem;line-height:1.7;opacity:0.7;">'
        f'Explore National Overview Maps, Financial Allocations, '
        f'State-Level Profiles, and Conflict Analysis.</p>'
        f'<div style="margin-top:16px;padding:12px;background:rgba(22,43,35,0.4);'
        f'border-radius:10px;border:1px solid {PRIMARY}33;">'
        f'<p style="color:{ACCENT};font-size:0.6rem;letter-spacing:1.5px;'
        f'font-weight:700;margin:0 0 6px 0;">DATA SOURCES</p>'
        f'<p style="color:{TEXT_COLOR};font-size:0.72rem;margin:0;line-height:1.7;">Use links below</p>'
        f'</div></div>'
    )
    st.markdown(sb, unsafe_allow_html=True)
    st.markdown(
        '<a href="https://ntca.gov.in/monitoring/" target="_top" '
        'onclick="window.top.location.href=\'https://ntca.gov.in/monitoring/\'; return false;">NTCA Tiger Monitoring</a>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<a href="https://wii.gov.in/tiger-cell" target="_top" '
        'onclick="window.top.location.href=\'https://wii.gov.in/tiger-cell\'; return false;">WII Tiger Cell</a>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<a href="https://moef.gov.in/" target="_top" '
        'onclick="window.top.location.href=\'https://moef.gov.in/\'; return false;">MoEFCC</a>',
        unsafe_allow_html=True,
    )

# ── Hero banner ──
hero = (
    f'<div style="background:linear-gradient(135deg,{PRIMARY_DARK} 0%,{PRIMARY} 35%,'
    f'#0D2818 70%,{PRIMARY_DARK} 100%);'
    f'border:1px solid {BORDER_SUBTLE};border-radius:22px;padding:48px 48px 40px 48px;'
    f'margin-bottom:28px;position:relative;overflow:hidden;">'
    f'<div style="position:absolute;inset:0;'
    f'background:radial-gradient(ellipse at 25% 50%,{ACCENT}06,transparent 55%),'
    f'radial-gradient(ellipse at 75% 30%,{PRIMARY_LIGHT}0A,transparent 55%);"></div>'
    f'<div style="position:absolute;top:0;left:0;right:0;height:2px;'
    f'background:linear-gradient(90deg,transparent,{ACCENT}55,transparent);"></div>'
    f'<div style="position:absolute;bottom:0;left:0;right:0;height:1px;'
    f'background:linear-gradient(90deg,transparent,{PRIMARY_LIGHT}33,transparent);"></div>'
    f'<div style="position:absolute;right:40px;top:50%;transform:translateY(-50%);'
    f'font-size:9rem;opacity:0.04;user-select:none;">🐯</div>'
    f'<div style="position:relative;z-index:1;max-width:700px;">'
    f'<div style="display:inline-block;padding:5px 16px;margin-bottom:16px;'
    f'background:{ACCENT}10;border:1px solid {ACCENT}25;border-radius:20px;'
    f'font-size:0.63rem;color:{ACCENT};letter-spacing:2.5px;font-weight:700;">'
    f'PROJECT TIGER · REAL DATA · 2006–2024</div>'
    f'<h1 style="color:{TEXT_COLOR};font-size:3rem;font-weight:900;'
    f'margin:0 0 8px 0;letter-spacing:0.5px;line-height:1.1;">'
    f'Eyes on Tigers (E<span style="color:{ACCENT};">o</span>T)</h1>'
    f'<p style="color:{MUTED_TEXT};font-size:0.82rem;font-weight:500;'
    f'margin:0 0 20px 0;letter-spacing:3.5px;opacity:0.7;">'
    f'TIGER CONSERVATION EFFECTIVENESS ASSESSMENT &amp; MONITORING SYSTEM</p>'
    f'<div style="width:50px;height:2px;margin-bottom:20px;'
    f'background:linear-gradient(90deg,{ACCENT},transparent);"></div>'
    f'<p style="color:{MUTED_TEXT};font-size:0.95rem;line-height:1.85;opacity:0.9;">'
    f'Tracking India\'s tiger conservation across <b style="color:{TEXT_COLOR};">'
    f'{states_count} States</b> using imputed census, mortality, and funding data — '
    f'with Full Transparency on Estimation Methodology.</p>'
    f'</div></div>'
)
st.markdown(hero, unsafe_allow_html=True)

# ── Top stat cards ──
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(stat_card("Total Tigers (2022)", f"{total_2022:,}",
        f"▲ {growth_pct}% Since 2006", ACCENT), unsafe_allow_html=True)
with c2:
    st.markdown(stat_card("States Monitored", str(states_count),
        "Across All Tiger Landscapes", PRIMARY_LIGHT), unsafe_allow_html=True)
with c3:
    st.markdown(stat_card("Human Fatalities", f"{total_human:,}",
        "Tiger Attacks (2015–2024)", ALERT), unsafe_allow_html=True)
with c4:
    st.markdown(stat_card("Tiger Mortalities", f"{total_tiger:,}",
        "Recorded Deaths (2012–2025)", "#F97316"), unsafe_allow_html=True)

st.markdown(f'<div style="height:20px;"></div>', unsafe_allow_html=True)

# ── National population trend chart ──
st.markdown(section_header("National Tiger Population Trend & Projections",
    "Combined All-India Census Estimates (1973–2022) and Projections (2023–2030)."),
    unsafe_allow_html=True)

# Split into historical/census and projected
hist_mask = national["year"] <= 2022
proj_mask = national["year"] >= 2022

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=national["year"], y=national["population"],
    mode="none", fill="tozeroy",
    fillcolor="rgba(245,158,11,0.07)", name="", showlegend=False
))

# 1. Historical & Census line (solid)
_c_years = {2006, 2010, 2014, 2018, 2022}
fig.add_trace(go.Scatter(
    x=national[hist_mask]["year"], y=national[hist_mask]["population"],
    mode="lines+markers+text",
    name="Census Counts",
    line=dict(color=ACCENT, width=3, shape="spline"),
    marker=dict(size=10, color=ACCENT, line=dict(width=2.5, color=PRIMARY_DARK), symbol="circle"),
    text=[f"{int(row['population']):,}" if (row['year'] in _c_years or row['year'] < 2006) else "" for _, row in national[hist_mask].iterrows()],
    textposition="top center",
    textfont=dict(size=9, color=MUTED_TEXT),
    hovertemplate="<b>%{x}</b><br>Population: <b>%{y:,}</b><extra></extra>",
))

# 2. Projected line (dashed)
fig.add_trace(go.Scatter(
    x=national[proj_mask]["year"], y=national[proj_mask]["population"],
    mode="lines+markers",
    name="Projections",
    line=dict(color=ACCENT, width=3, dash="dash", shape="spline"),
    marker=dict(size=8, color=ACCENT_LIGHT, line=dict(width=1.5, color=PRIMARY_DARK)),
    hovertemplate="<b>%{x} (Projected)</b><br>Population: <b>%{y:,}</b><extra></extra>",
))

fig.add_vrect(x0=2005.5, x1=2006.5,
    fillcolor=ALERT, opacity=0.08, line_width=0,
    annotation_text="Camera-trap era", annotation_position="top left",
    annotation_font_size=10, annotation_font_color=ALERT)

# Shaded projection area
fig.add_vrect(x0=2022, x1=2030,
    fillcolor=SUCCESS, opacity=0.04, line_width=0,
    annotation_text="Projected Horizon", annotation_position="top left",
    annotation_font_size=10, annotation_font_color=SUCCESS)

apply_dark_layout(fig, height=380, showlegend=True,
                  xaxis_title="Year", yaxis_title="Tiger Population")
fig.update_xaxes(dtick=5, tickmode="linear")
fig.update_yaxes(rangemode="tozero")
popout_link(fig, "home_national_trend_popout", "Pop out chart")
st.plotly_chart(fig, use_container_width=True)

st.markdown(f'<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Insights grid: top states + funding ──
left, right = st.columns([1.1, 0.9])

with left:
    st.markdown(section_header("Top States by Tiger Count (2022)",
        "Based on State-Level Imputed Census Values"), unsafe_allow_html=True)
    top10 = summary.sort_values("pop_2022", ascending=False).head(10)
    fig2 = go.Figure(go.Bar(
        x=top10["pop_2022"], y=top10["state"],
        orientation="h",
        marker=dict(
            color=top10["pop_2022"],
            colorscale=[[0, PRIMARY_LIGHT], [0.5, ACCENT], [1.0, ACCENT_LIGHT]],
            line=dict(color="rgba(0,0,0,0)", width=0),
        ),
        name="",
        text=[f"{int(v):,}" for v in top10["pop_2022"]],
        textposition="outside",
        textfont=dict(color=MUTED_TEXT, size=11),
        hovertemplate="<b>%{y}</b><br>Tigers: <b>%{x:,}</b><extra></extra>",
    ))
    apply_dark_layout(fig2, height=370, showlegend=False,
                      xaxis_title="Tigers (2022)", yaxis_title="")
    fig2.update_yaxes(autorange="reversed")
    popout_link(fig2, "home_top_states_popout", "Pop out chart")
    st.plotly_chart(fig2, use_container_width=True)

with right:
    st.markdown(section_header("Funding vs. Tiger Count",
        "Total Conservation Funds (₹ Lakh) vs. Population by State"), unsafe_allow_html=True)

    scatter_df = summary[(summary["pop_2022"] > 0) & (summary["total_funds_lakh"] > 0)].copy()
    # Ensure label column is safe for Plotly text/hover (avoid undefined)
    scatter_df["state"] = scatter_df["state"].fillna("").astype(str)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=scatter_df["total_funds_lakh"],
        y=scatter_df["pop_2022"],
        mode="markers+text",
        text=scatter_df["state"],
        textposition="top center",
        textfont=dict(size=9, color=MUTED_TEXT),
        marker=dict(
            size=scatter_df["human_deaths_total"].clip(lower=1) * 1.5 + 8,
            color=scatter_df["tiger_deaths_total"],
            colorscale=[[0, SUCCESS], [0.5, ACCENT], [1, ALERT]],
            showscale=True,
            colorbar=dict(title=dict(text="Tiger<br>Deaths", font=dict(size=10)),
                          thickness=12, len=0.7, tickfont=dict(size=9)),
            line=dict(color=PRIMARY_DARK, width=1),
            opacity=0.85
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Funds: ₹%{x:,.0f} L<br>"
            "Tigers (2022): %{y:,}<extra></extra>"
        )
    ))
    apply_dark_layout(fig3, height=370, showlegend=False,
                      xaxis_title="Total Funds (₹ Lakh)", yaxis_title="Tiger Count (2022)")
    popout_link(fig3, "home_funding_vs_tigers_popout", "Pop out chart")
    st.plotly_chart(fig3, use_container_width=True)

st.markdown(f'<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── Conflict heatmap row ──
st.markdown(section_header("Human Conflict & Tiger Mortality Overview",
    "Annual Trends Across All States — Darker Indicates Higher Incidents"), unsafe_allow_html=True)

hcol, tcol = st.columns(2)
with hcol:
    st.markdown(
        '<div style="font-size:0.96rem;font-weight:700;color:' + TEXT_COLOR + ';'
        'margin-bottom:10px;letter-spacing:0.4px;">Human deaths</div>',
        unsafe_allow_html=True,
    )
    hd_pivot = (hdeaths.groupby(["year", "state"])["deaths_imputed"].sum().reset_index())
    top_conflict = (hd_pivot.groupby("state")["deaths_imputed"].sum().nlargest(10).index.tolist())
    hd_top = hd_pivot[hd_pivot["state"].isin(top_conflict)]
    hd_matrix = hd_top.pivot(index="state", columns="year", values="deaths_imputed").fillna(0)
    fig4 = go.Figure(go.Heatmap(
        z=hd_matrix.values,
        x=[str(c) for c in hd_matrix.columns],
        y=hd_matrix.index.tolist(),
        colorscale=[[0, PRIMARY_DARK], [0.3, PRIMARY], [0.7, ACCENT], [1, ALERT]],
        hovertemplate="<b>%{y}</b> · %{x}<br>Deaths: <b>%{z:.0f}</b><extra></extra>",
        name="",
        showscale=True,
        colorbar=dict(thickness=12, len=0.8, tickfont=dict(size=9)),
    ))
    apply_dark_layout(fig4, height=310, showlegend=False,
                      title="Human Deaths by Tiger Attacks (Top 10 States)")
    fig4.update_xaxes(tickangle=-45, tickfont=dict(size=9))
    popout_link(fig4, "home_human_heatmap_popout", "Pop out chart")
    st.plotly_chart(fig4, use_container_width=True)

with tcol:
    st.markdown(
        '<div style="font-size:0.96rem;font-weight:700;color:' + TEXT_COLOR + ';'
        'margin-bottom:10px;letter-spacing:0.4px;">Tiger deaths</div>',
        unsafe_allow_html=True,
    )
    td_pivot = (tdeaths.groupby(["year", "state"])["total_deaths_imputed"].sum().reset_index())
    top_td = (td_pivot.groupby("state")["total_deaths_imputed"].sum().nlargest(10).index.tolist())
    td_top = td_pivot[td_pivot["state"].isin(top_td)]
    td_matrix = td_top.pivot(index="state", columns="year", values="total_deaths_imputed").fillna(0)
    fig5 = go.Figure(go.Heatmap(
        z=td_matrix.values,
        x=[str(c) for c in td_matrix.columns],
        y=td_matrix.index.tolist(),
        colorscale=[[0, PRIMARY_DARK], [0.3, PRIMARY], [0.7, "#F97316"], [1, ALERT]],
        hovertemplate="<b>%{y}</b> · %{x}<br>Deaths: <b>%{z:.0f}</b><extra></extra>",
        name="",
        showscale=True,
        colorbar=dict(thickness=12, len=0.8, tickfont=dict(size=9)),
    ))
    apply_dark_layout(fig5, height=310, showlegend=False,
                      title="Tiger Mortality by State (Top 10 States)")
    fig5.update_xaxes(tickangle=-45, tickfont=dict(size=9))
    popout_link(fig5, "home_tiger_heatmap_popout", "Pop out chart")
    st.plotly_chart(fig5, use_container_width=True)

# ── Quick nav cards ──
st.markdown(f'<div style="height:8px;"></div>', unsafe_allow_html=True)
st.markdown(section_header("Dashboard Modules",
    "Navigate to Any Module for Deeper Analysis"), unsafe_allow_html=True)

nav_pages = [
    ("01", "National Overview",    "State-Level Population Map, Census Trend Analysis, and Reserve Distribution Across India's Tiger Landscapes.", "🗺️", ACCENT),
    ("02", "State Explorer",       "Deep-Dive Into Any State — Census, Funding, Conflict, and Mortality in One Pane, with Imputation Transparency.", "🔍", PRIMARY_LIGHT),
    ("03", "Financial Analysis",   "Conservation Fund Allocation Trends — Central vs. State Share, TPF Contributions, and Year-on-Year Comparisons.", "💰", INFO),
    ("04", "Mortality & Conflict", "Human Fatalities from Tiger Attacks and Tiger Mortality by Cause — Poaching, Natural, Unnatural — Across All States.", "⚠️", ALERT),
]
cols = st.columns(4)
for i, (num, title, desc, icon, color) in enumerate(nav_pages):
    with cols[i]:
        card = (
            f'<div style="background:linear-gradient(160deg,rgba(22,43,35,0.55) 0%,rgba(14,17,23,0.75) 100%);'
            f'border:1px solid {color}18;border-top:2px solid {color}55;'
            f'border-radius:16px;padding:22px 18px;min-height:180px;'
            f'margin-bottom:10px;backdrop-filter:blur(8px);position:relative;overflow:hidden;">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
            f'<span style="font-size:1.6rem;">{icon}</span>'
            f'<div>'
            f'<p style="color:{color};font-size:0.6rem;font-weight:700;letter-spacing:2px;margin:0;opacity:0.85;">PAGE {num}</p>'
            f'<h3 style="color:{TEXT_COLOR};font-size:0.98rem;font-weight:700;margin:0;">{title}</h3>'
            f'</div></div>'
            f'<p style="color:{MUTED_TEXT};font-size:0.76rem;line-height:1.65;margin:0;opacity:0.8;">{desc}</p>'
            f'</div>'
        )
        st.markdown(card, unsafe_allow_html=True)

# ── Footer ──
footer = (
    f'<div style="text-align:center;padding:32px 0 12px 0;margin-top:24px;">'
    f'<div style="height:1px;margin-bottom:20px;'
    f'background:linear-gradient(90deg,transparent,{BORDER_ACCENT},transparent);"></div>'
    f'<p style="color:{MUTED_TEXT};font-size:0.67rem;opacity:0.45;letter-spacing:0.5px;line-height:1.8;">'
    f'Eyes on Tigers (EoT) Dashboard — Tiger Conservation Analytics &mdash; Data: NTCA, WII, Project Tiger Fund<br>'
    f'Imputation methods: Kalman filtering, spline interpolation, linear interpolation, t-distribution CI</p>'
    f'</div>'
)
st.markdown(footer, unsafe_allow_html=True)
