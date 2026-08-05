"""
Map and chart utility functions for the Eyes on Tigers dashboard.
Premium design system with glassmorphism, micro-animations, and refined aesthetics.
All HTML strings are built as single-line concatenations to avoid Streamlit's
markdown parser treating 4-space-indented lines as code blocks.
"""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from plotly.offline.offline import get_plotlyjs
import re

# ── Color palette ──
PRIMARY = "#1B4332"
PRIMARY_LIGHT = "#2D6A4F"
PRIMARY_DARK = "#0A1F15"
ACCENT = "#F59E0B"
ACCENT_LIGHT = "#FBBF24"
ALERT = "#EF4444"
ALERT_DARK = "#991B1B"
SUCCESS = "#10B981"
INFO = "#3B82F6"
BG_DARK = "#0E1117"
CARD_BG = "rgba(22, 43, 35, 0.65)"
CARD_BG_SOLID = "#162B23"
GLASS_BG = "rgba(22, 43, 35, 0.45)"
TEXT_COLOR = "#F1F5F9"
MUTED_TEXT = "#94A3B8"
BORDER_SUBTLE = "rgba(245, 158, 11, 0.12)"
BORDER_ACCENT = "rgba(245, 158, 11, 0.25)"

# Plotly layout defaults
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_COLOR, family="'Inter', -apple-system, sans-serif", size=13),
    margin=dict(l=50, r=30, t=55, b=45),
    hoverlabel=dict(
        bgcolor="#1B4332",
        font_size=13,
        font_family="'Inter', sans-serif",
        font_color=TEXT_COLOR,
        bordercolor=ACCENT,
    ),
    title_font=dict(size=16, color=TEXT_COLOR, family="'Inter', sans-serif"),
)


def apply_dark_layout(fig, **kwargs):
    """Apply consistent dark theme to any Plotly figure."""
    layout = {**PLOTLY_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        title_font=dict(size=12, color=MUTED_TEXT),
        tickfont=dict(size=11, color=MUTED_TEXT),
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.06)",
        title_font=dict(size=12, color=MUTED_TEXT),
        tickfont=dict(size=11, color=MUTED_TEXT),
    )
    # Ensure title text is always defined (avoid Plotly showing 'undefined' when title font exists)
    fig.update_layout(title_text="")
    return fig


def create_india_map(df, lat_col="latitude", lon_col="longitude",
                     size_col=None, color_col=None, hover_name="reserve_name",
                     hover_data=None, title="", color_scale=None,
                     size_max=30, zoom=4.2):
    """Create a scatter mapbox centered on India using carto-positron tiles."""
    fig = px.scatter_mapbox(
        df, lat=lat_col, lon=lon_col, size=size_col, color=color_col,
        hover_name=hover_name, hover_data=hover_data,
        color_continuous_scale=color_scale or [
            [0, "#1B4332"], [0.3, "#2D6A4F"], [0.6, "#F59E0B"], [1.0, "#EF4444"],
        ],
        size_max=size_max, zoom=zoom,
        center={"lat": 22.5, "lon": 80.0},
        mapbox_style="carto-positron", title=title,
    )
    apply_dark_layout(fig, height=600)
    fig.update_layout(mapbox=dict(style="carto-positron",
                                   center={"lat": 22.5, "lon": 80.0}, zoom=zoom))
    return fig


def stat_card(title, value, subtitle="", color=ACCENT, icon=""):
    """Premium glassmorphic stat card — single-line HTML to avoid markdown code-block rendering."""
    return (
        f'<div class="eot-stat-card" style="background:linear-gradient(160deg,rgba(22,43,35,0.7) 0%,rgba(14,17,23,0.85) 100%);'
        f'backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);'
        f'border:1px solid {color}18;border-radius:16px;padding:24px 20px 20px 20px;'
        f'text-align:center;position:relative;overflow:hidden;'
        f'transition:all 0.35s cubic-bezier(0.4,0,0.2,1);">'
        f'<div style="position:absolute;top:0;left:0;right:0;height:3px;'
        f'background:linear-gradient(90deg,transparent,{color},transparent);opacity:0.7;"></div>'
        f'<div style="position:absolute;top:-40px;right:-40px;width:100px;height:100px;'
        f'background:radial-gradient(circle,{color}08,transparent 70%);border-radius:50%;"></div>'
        f'<p style="color:{MUTED_TEXT};font-size:0.68rem;margin:0 0 10px 0;'
        f'text-transform:uppercase;letter-spacing:1.8px;font-weight:600;">{title}</p>'
        f'<p style="color:{color};font-size:2rem;font-weight:800;margin:0 0 6px 0;'
        f'line-height:1;letter-spacing:-0.5px;text-shadow:0 0 30px {color}22;">{value}</p>'
        f'<p style="color:{MUTED_TEXT};font-size:0.72rem;margin:0;line-height:1.4;opacity:0.8;">{subtitle}</p>'
        f'</div>'
    )


def stat_card_mini(title, value, color=ACCENT):
    """Compact stat card for dense layouts — single-line HTML."""
    return (
        f'<div style="background:linear-gradient(145deg,rgba(22,43,35,0.5),rgba(14,17,23,0.7));'
        f'border:1px solid {color}15;border-left:3px solid {color};'
        f'border-radius:10px;padding:14px 16px;backdrop-filter:blur(8px);">'
        f'<p style="color:{MUTED_TEXT};font-size:0.65rem;margin:0 0 4px 0;'
        f'text-transform:uppercase;letter-spacing:1.5px;font-weight:600;">{title}</p>'
        f'<p style="color:{color};font-size:1.3rem;font-weight:700;margin:0;line-height:1.1;">{value}</p>'
        f'</div>'
    )


def status_badge(status):
    """Polished status badge with glow effect — single-line HTML."""
    colors = {
        "Healthy": ("#10B981", "#065F46", "#10B98120"),
        "At Risk": ("#F59E0B", "#78350F", "#F59E0B20"),
        "Underperforming": ("#EF4444", "#7F1D1D", "#EF444420"),
    }
    text_c, bg, glow = colors.get(status, ("#888", "#333", "#88888820"))
    return (
        f'<span style="background:{bg};color:{text_c};padding:8px 22px;'
        f'border-radius:24px;font-weight:700;font-size:0.82rem;letter-spacing:0.8px;'
        f'border:1px solid {text_c}33;'
        f'box-shadow:0 0 20px {glow},inset 0 1px 0 rgba(255,255,255,0.05);'
        f'text-transform:uppercase;">{status}</span>'
    )


def section_header(title, subtitle=""):
    """Elegant section header with accent line — single-line HTML."""
    return (
        f'<div style="margin:8px 0 22px 0;position:relative;">'
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">'
        f'<div style="width:4px;height:28px;background:linear-gradient(180deg,{ACCENT},{PRIMARY_LIGHT});border-radius:2px;"></div>'
        f'<h2 style="color:{TEXT_COLOR};margin:0;font-weight:700;font-size:1.25rem;letter-spacing:-0.2px;">{title}</h2>'
        f'</div>'
        f'<p style="color:{MUTED_TEXT};font-size:0.82rem;margin:0 0 0 16px;opacity:0.75;">{subtitle}</p>'
        f'</div>'
    )


def page_header(title, subtitle="", icon=""):
    """Full-width page header with gradient background — single-line HTML."""
    return (
        f'<div style="background:linear-gradient(135deg,{PRIMARY_DARK} 0%,{PRIMARY} 50%,{PRIMARY_DARK} 100%);'
        f'border:1px solid {BORDER_SUBTLE};border-radius:18px;padding:32px 36px;'
        f'margin-bottom:28px;position:relative;overflow:hidden;">'
        f'<div style="position:absolute;top:-60px;right:-30px;font-size:8rem;'
        f'opacity:0.03;transform:rotate(-10deg);">{icon}</div>'
        f'<div style="position:absolute;bottom:0;left:0;right:0;height:2px;'
        f'background:linear-gradient(90deg,transparent,{ACCENT}44,transparent);"></div>'
        f'<h1 style="color:{TEXT_COLOR};font-size:1.75rem;font-weight:800;'
        f'margin:0 0 6px 0;letter-spacing:-0.3px;">{title}</h1>'
        f'<p style="color:{MUTED_TEXT};font-size:0.88rem;margin:0;opacity:0.8;line-height:1.5;">{subtitle}</p>'
        f'</div>'
    )


def divider():
    """Subtle gradient divider."""
    return (
        f'<div style="height:1px;margin:28px 0;'
        f'background:linear-gradient(90deg,transparent,{BORDER_ACCENT},transparent);"></div>'
    )


def popout_link(fig, key, label="Full screen chart"):
    """Store the figure in the global in-memory cache and link to it via query parameters."""
    safe_key = re.sub(r"[^a-zA-Z0-9_-]+", "_", key).strip("_")
    
    # Store figure in the global in-memory cache
    from utils.chart_cache import get_chart_cache
    get_chart_cache()[safe_key] = fig
    
    # Build a URL relative to the current Streamlit base path using query parameters.
    base = (st.get_option("server.baseUrlPath") or "").strip("/")
    base_prefix = f"/{base}" if base else ""
    chart_url = f"{base_prefix}/?popout={safe_key}"
    st.markdown(
        f'<a class="eot-popout-link" href="{chart_url}" target="_blank" rel="noopener noreferrer">'
        f'Open chart: {label}</a>',
        unsafe_allow_html=True,
    )


# ── Global CSS injection ──
GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #060D09 0%, #0A1810 40%, #0E1117 100%) !important;
        border-right: 1px solid rgba(27, 67, 50, 0.2);
    }

    /* ── Main content ── */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1300px;
    }

    /* ── Card hover effects ── */
    .eot-stat-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
    }

    /* ── Selectbox ── */
    .stSelectbox > div > div {
        background-color: rgba(22, 43, 35, 0.6) !important;
        border: 1px solid rgba(27, 67, 50, 0.4) !important;
        border-radius: 10px !important;
    }
    .stSelectbox > div > div:hover {
        border-color: rgba(245, 158, 11, 0.4) !important;
    }

    /* ── Slider ── */
    .stSlider [data-baseweb="slider"] > div > div {
        background-color: #1B4332 !important;
    }
    .stSlider [data-baseweb="slider"] > div > div > div {
        background-color: #F59E0B !important;
    }
    .stSlider [data-baseweb="thumb"] {
        background-color: #F59E0B !important;
        border: 2px solid #0E1117 !important;
        box-shadow: 0 0 12px rgba(245,158,11,0.3) !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(14, 17, 23, 0.5);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        border: none;
        color: #94A3B8;
        font-weight: 500;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(27, 67, 50, 0.6) !important;
        color: #F59E0B !important;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: rgba(22, 43, 35, 0.3) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(27, 67, 50, 0.3) !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: rgba(245, 158, 11, 0.3) !important;
        color: #F1F5F9 !important;
    }

    /* ── DataFrame ── */
    .stDataFrame {
        border-radius: 14px !important;
        overflow: hidden;
        border: 1px solid rgba(27, 67, 50, 0.25) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: #F59E0B !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(27, 67, 50, 0.5);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(245, 158, 11, 0.5); }

    /* ── Plotly chart containers ── */
    .stPlotlyChart {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(27, 67, 50, 0.15);
        background: rgba(14, 17, 23, 0.3);
    }

    /* ── Button styling ── */
    .stButton > button {
        background: linear-gradient(135deg, #1B4332, #2D6A4F) !important;
        border: 1px solid rgba(245, 158, 11, 0.2) !important;
        border-radius: 10px !important;
        color: #F1F5F9 !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        border-color: rgba(245, 158, 11, 0.5) !important;
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.15) !important;
        transform: translateY(-1px);
    }

    /* ── Hide Streamlit branding ── */
    .eot-popout-link {
        display: inline-flex;
        align-items: center;
        margin: -8px 0 8px 0;
        color: #F59E0B !important;
        font-size: 0.78rem;
        font-weight: 700;
        text-decoration: none !important;
        letter-spacing: 0.2px;
    }
    .eot-popout-link:hover {
        color: #FBBF24 !important;
        text-decoration: underline !important;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] {
        background: rgba(14, 17, 23, 0.8) !important;
        backdrop-filter: blur(12px);
    }
</style>
"""
