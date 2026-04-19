PROJECT: AI VOICE AGENT
TEAM: GROUP TEMP

OVERVIEW
This project is a hotel-style AI voice agent prototype that can:
- check guest profiles
- check reservation status
- update reservation details
- save interactions to a log file
- display logs in a Streamlit viewer

TECH STACK
- Python
- Streamlit
- JSON-based mock database

HOW TO RUN

1. Install dependencies:
pip install -r requirements.txt

2. Seed the mock database:
python src/db_setup.py

3. Run the command-line agent:
python src/main.py

4. Optional log viewer:
streamlit run src/ui_log_viewer.py

PROJECT FILES
- src/main.py: starts the program
- src/agent.py: handles user interaction
- src/tools.py: core system functions
- src/config.py: app configuration
- src/db_setup.py: creates starter data
- src/ui_log_viewer.py: Streamlit log viewer
- src/data.json: mock guest and reservation data
- assistant.log: generated after program runs
