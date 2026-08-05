"""
Eyes on Tigers (EoT) - Tiger Conservation & Effectiveness Monitoring System
Navigation controller — all pages are file-based for reliable path resolution.
"""
import streamlit as st

# Check if this is a popout request for a fullscreen chart
popout_key = st.query_params.get("popout")
if popout_key:
    from utils.chart_cache import get_chart_cache
    
    st.set_page_config(
        page_title="EoT Chart Viewer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    # Inject styling to hide all Streamlit structural chrome (header, sidebar, padding)
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stDecoration"] { display: none !important; }
            .main .block-container { padding: 20px !important; max-width: 100vw !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Retrieve the figure from the globally shared cache
    fig = get_chart_cache().get(popout_key)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Chart session expired. Please go back to the main dashboard and click 'Open chart' again.")
    st.stop()

st.set_page_config(
    page_title="Eyes on Tigers - Tiger Conservation Dashboard",
    page_icon="🐯",
    layout="wide",
    initial_sidebar_state="expanded",
)

home_page     = st.Page("views/home_page.py",            title="Home Page",            default=True)
national_page = st.Page("views/01_national_overview.py", title="National Overview")
state_page    = st.Page("views/02_state_explorer.py",    title="State Explorer")
finance_page  = st.Page("views/03_financial_analysis.py", title="Financial Analysis")
mortality_page= st.Page("views/04_mortality_conflict.py", title="Mortality & Conflict")
growth_page   = st.Page("views/05_growth_analysis.py",    title="Growth & Projections")
explorer_page = st.Page("views/06_cv_patrol_explorer.py", title="Patrol & CV Explorer")
bot_page      = st.Page("views/05_eot_bot.py",           title="EoT Chatbot")

pg = st.navigation({
    "Eyes on Tigers": [home_page, national_page, state_page, finance_page, mortality_page, growth_page, explorer_page, bot_page]
})


pg.run()

