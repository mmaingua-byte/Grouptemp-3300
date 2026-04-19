from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"

DATA_FILE = SRC_DIR / "data.json"
LOG_FILE = BASE_DIR / "assistant.log"

APP_NAME = "Hotel AI Voice Agent"
APP_VERSION = "2.0"

ALLOWED_STATUSES = {
    "Pending",
    "Confirmed",
    "Checked-In",
    "Checked-Out",
    "Cancelled",
}

STATUS_TRANSITIONS = {
    "Pending": {"Confirmed", "Cancelled"},
    "Confirmed": {"Checked-In", "Cancelled"},
    "Checked-In": {"Checked-Out"},
    "Checked-Out": set(),
    "Cancelled": set(),
}
