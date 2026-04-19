import json
from pathlib import Path

from config import DATA_FILE
from tools import DEFAULT_DATA, validate_data


def setup_db() -> None:
    data_path = Path(DATA_FILE)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    validated_data = validate_data(DEFAULT_DATA)

    with open(data_path, "w", encoding="utf-8") as file:
        json.dump(validated_data, file, indent=2)

    print(f"Mock database created at: {data_path}")


if __name__ == "__main__":
    setup_db()
