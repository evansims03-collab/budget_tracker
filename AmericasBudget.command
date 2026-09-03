#!/bin/bash
# Move to the script's folder
cd "$(dirname "$0")"

# Source conda environment profile
source ~/.zshrc > /dev/null 2>&1
source $(conda info --base 2>/dev/null)/etc/profile.d/conda.sh 2>/dev/null
conda activate base 2>/dev/null

# Launch streamlit in background mode
streamlit run app.py --server.headless=true &

# Give the server a moment to start
sleep 2

# Open in standalone Chrome App window (or fallback to default browser)
if [ -d "/Applications/Google Chrome.app" ]; then
    open -na "Google Chrome" --args --app="http://localhost:8501"
else
    open "http://localhost:8501"
fi