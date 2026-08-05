#!/bin/bash
# Eyes on Tigers (EoT) - Dashboard Launcher

echo "🐅 Starting Eyes on Tigers (EoT) Dashboard..."

# Check if streamlit is in path, otherwise try anaconda path
STREAMLIT_CMD="streamlit"
if ! command -v streamlit &> /dev/null; then
    if [ -x "/opt/anaconda3/bin/streamlit" ]; then
        STREAMLIT_CMD="/opt/anaconda3/bin/streamlit"
        echo "Found Streamlit in /opt/anaconda3/bin/"
    else
        echo "❌ Error: Streamlit not found. Please ensure your Conda environment is activated."
        exit 1
    fi
fi

# Run the app
$STREAMLIT_CMD run app.py
