from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "src" / "data.json"
LOG_FILE = BASE_DIR / "assistant.log"
APP_NAME = "Hotel AI Voice Agent"
