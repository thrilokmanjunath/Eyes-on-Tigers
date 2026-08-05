import streamlit as st
from utils.chatbot_agent import answer_query
from utils.map_utils import GLOBAL_CSS, page_header, divider

import os

# Inject premium design system CSS
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# Render premium header
st.markdown(page_header(
    "Eyes on Tigers (EoT) Conservation Assistant",
    "Query tiger census counts, conservation funding, poaching mortality, and human-wildlife conflict statistics across India.",
    "🤖"
), unsafe_allow_html=True)

# Configure Gemini API key input in the sidebar
with st.sidebar:
    st.markdown("### Bot Configuration")
    api_key_input = st.text_input(
        "Gemini API Key:",
        type="password",
        value=st.session_state.get("gemini_api_key", ""),
        help="Enter your Google Gemini API key to enable advanced NLP logic. If left empty, the chatbot falls back to the rule-based search engine."
    )
    if api_key_input:
        st.session_state["gemini_api_key"] = api_key_input
    
    # Check if a key is active from any source (user input, env, or secrets)
    secrets_key = None
    try:
        secrets_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        secrets_key = None
        
    active_key = st.session_state.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY") or secrets_key
    if active_key:
        st.success("🟢 Gemini AI Engine Active")
    else:
        st.info("ℹ️ Rule-Based Engine Active (Enter API key to unlock Gemini)")

# Initialize chat session history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# List of 3 sample prompts relevant to the project data
sample_prompts = [
    "Which state has the highest tiger population in 2022?",
    "How many tiger deaths were caused by poaching nationally?",
    "How much conservation funding was allocated to Madhya Pradesh?"
]

clicked_prompt = None

# Show suggested prompts when the chat is empty
if len(st.session_state.chat_history) == 0:
    st.markdown("""
        <div style="margin-bottom:12px;">
            <p style="color:#94A3B8;font-size:0.85rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;">
                💡 Suggested Questions to Get Started:
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(3)
    for i, prompt in enumerate(sample_prompts):
        with cols[i]:
            # Styled prompt card button
            if st.button(prompt, key=f"sample_prompt_{i}", use_container_width=True):
                clicked_prompt = prompt

# Render chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Capture user query either from the chat input or from clicked prompt buttons
user_query = st.chat_input("Ask EoT Assistant about the data...")
if clicked_prompt:
    user_query = clicked_prompt

if user_query:
    # Display the user's message immediately
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Generate response from the locally-cached analytics engine
    with st.spinner("Analyzing conservation records..."):
        response = answer_query(user_query, api_key=active_key)
        
    # Display the assistant's response
    with st.chat_message("assistant"):
        st.markdown(response)
        
    # Save to history for persistent view
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()
