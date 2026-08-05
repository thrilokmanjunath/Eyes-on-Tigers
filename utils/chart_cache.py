import streamlit as st

@st.cache_resource
def get_chart_cache():
    """Returns a globally shared dictionary for caching figures for popouts."""
    return {}
