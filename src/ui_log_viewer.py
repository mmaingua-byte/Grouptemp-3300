from pathlib import Path

import streamlit as st

from config import APP_NAME, APP_VERSION, LOG_FILE

st.set_page_config(page_title="Voice Agent Logs", layout="wide")
st.title(f"{APP_NAME} Logs")
st.caption(f"Version {APP_VERSION}")

log_path = Path(LOG_FILE)

if log_path.exists():
    log_text = log_path.read_text(encoding="utf-8")
    st.text_area("assistant.log", log_text, height=500)
else:
    st.info("No log file found yet. Run the program first to generate logs.")
