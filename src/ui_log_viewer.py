import streamlit as st
from pathlib import Path
from config import LOG_FILE

st.set_page_config(page_title="Voice Agent Logs", layout="wide")
st.title("Hotel AI Voice Agent Logs")

log_path = Path(LOG_FILE)

if log_path.exists():
    log_text = log_path.read_text(encoding="utf-8")
    st.text_area("assistant.log", log_text, height=500)
else:
    st.info("No log file found yet. Run the program first to generate logs.")
