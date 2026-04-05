import json
from config import DATA_FILE

DEFAULT_DATA = {
    "guests": [
        {
            "guest_id": "G1001",
            "name": "John Doe",
            "phone": "704-555-1001",
            "email": "john.doe@example.com",
            "vip": True
        },
        {
            "guest_id": "G1002",
            "name": "Sarah Lee",
            "phone": "704-555-1002",
            "email": "sarah.lee@example.com",
            "vip": False
        }
    ],
    "reservations": [
        {
            "reservation_id": "R2001",
            "guest_id": "G1001",
            "room_type": "King Suite",
            "status": "Confirmed",
            "check_in": "2026-04-10",
            "check_out": "2026-04-13"
        },
        {
            "reservation_id": "R2002",
            "guest_id": "G1002",
            "room_type": "Double Room",
            "status": "Pending",
            "check_in": "2026-04-12",
            "check_out": "2026-04-14"
        }
    ]
}

def setup_db() -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_DATA, f, indent=2)
    print(f"Mock database created at: {DATA_FILE}")

if __name__ == "__main__":
    setup_db()
