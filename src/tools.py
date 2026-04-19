import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from config import ALLOWED_STATUSES, DATA_FILE, LOG_FILE, STATUS_TRANSITIONS


DEFAULT_DATA = {
    "guests": [
        {
            "guest_id": "G1001",
            "name": "John Doe",
            "phone": "704-555-1001",
            "email": "john.doe@example.com",
            "vip": True,
        },
        {
            "guest_id": "G1002",
            "name": "Sarah Lee",
            "phone": "704-555-1002",
            "email": "sarah.lee@example.com",
            "vip": False,
        },
    ],
    "reservations": [
        {
            "reservation_id": "R2001",
            "guest_id": "G1001",
            "room_type": "King Suite",
            "status": "Confirmed",
            "check_in": "2026-04-10",
            "check_out": "2026-04-13",
        },
        {
            "reservation_id": "R2002",
            "guest_id": "G1002",
            "room_type": "Double Room",
            "status": "Pending",
            "check_in": "2026-04-12",
            "check_out": "2026-04-14",
        },
    ],
}


class DataValidationError(Exception):
    pass


def log_event(role, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as file:
        file.write(f"[{timestamp}] {role.upper()}: {message}\n")


def _ensure_data_file_exists():
    data_path = Path(DATA_FILE)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        with open(data_path, "w") as file:
            json.dump(DEFAULT_DATA, file, indent=2)


def _validate_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except:
        raise DataValidationError("Invalid date format. Use YYYY-MM-DD.")


def validate_data(data):
    if not isinstance(data, dict):
        raise DataValidationError("Data must be a JSON object.")

    if "guests" not in data or "reservations" not in data:
        raise DataValidationError("Missing guests or reservations.")

    guest_ids = set()
    for g in data["guests"]:
        if "guest_id" not in g:
            raise DataValidationError("Guest missing ID")
        if g["guest_id"] in guest_ids:
            raise DataValidationError("Duplicate guest ID")
        guest_ids.add(g["guest_id"])

    reservation_ids = set()
    for r in data["reservations"]:
        if "reservation_id" not in r:
            raise DataValidationError("Reservation missing ID")

        if r["reservation_id"] in reservation_ids:
            raise DataValidationError("Duplicate reservation ID")

        if r["guest_id"] not in guest_ids:
            raise DataValidationError("Reservation has invalid guest ID")

        if r["status"] not in ALLOWED_STATUSES:
            raise DataValidationError("Invalid reservation status")

        _validate_date(r["check_in"])
        _validate_date(r["check_out"])

        reservation_ids.add(r["reservation_id"])

    return data


class HotelRepository:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = Path(data_file)
        self.data = {"guests": [], "reservations": []}
        self.guests = {}
        self.reservations = {}
        self.load()

    def load(self):
        _ensure_data_file_exists()

        with open(self.data_file, "r") as file:
            data = json.load(file)

        self.data = validate_data(data)
        self._index()

    def _index(self):
        self.guests = {}
        self.reservations = {}

        for g in self.data["guests"]:
            self.guests[g["guest_id"].lower()] = g

        for r in self.data["reservations"]:
            self.reservations[r["reservation_id"].lower()] = r

    def save(self):
        with open(self.data_file, "w") as file:
            json.dump(self.data, file, indent=2)
        self._index()

    def get_guest(self, guest_id):
        return self.guests.get(guest_id.lower())

    def get_reservation(self, reservation_id):
        return self.reservations.get(reservation_id.lower())

    def list_reservations(self):
        return deepcopy(self.data["reservations"])

    def update_reservation_status(self, reservation_id, new_status):
        reservation = self.get_reservation(reservation_id)

        if not reservation:
            return False, "Reservation not found."

        new_status = new_status.title()

        if new_status not in ALLOWED_STATUSES:
            return False, "Invalid status."

        current = reservation["status"]

        allowed = STATUS_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            return False, f"Cannot change from {current} to {new_status}"

        reservation["status"] = new_status
        self.save()

        return True, f"Updated {reservation_id} to {new_status}"


def get_repository():
    return HotelRepository()


def check_guest_profile(repo, guest_id):
    g = repo.get_guest(guest_id)

    if not g:
        return "Guest not found."

    return (
        f"Guest Found\n"
        f"ID: {g['guest_id']}\n"
        f"Name: {g['name']}\n"
        f"Phone: {g['phone']}\n"
        f"Email: {g['email']}\n"
        f"VIP: {'Yes' if g['vip'] else 'No'}"
    )


def check_reservation_status(repo, res_id):
    r = repo.get_reservation(res_id)

    if not r:
        return "Reservation not found."

    return (
        f"Reservation Found\n"
        f"Reservation ID: {r['reservation_id']}\n"
        f"Guest ID: {r['guest_id']}\n"
        f"Room Type: {r['room_type']}\n"
        f"Status: {r['status']}\n"
        f"Check-In: {r['check_in']}\n"
        f"Check-Out: {r['check_out']}"
    )


def update_reservation(repo, res_id, new_status):
    success, msg = repo.update_reservation_status(res_id, new_status)
    return msg


def list_all_reservations(repo):
    reservations = repo.list_reservations()

    if not reservations:
        return "No reservations found."

    output = "Reservation List\n"
    for r in reservations:
        output += (
            f"- {r['reservation_id']} | Guest {r['guest_id']} | "
            f"{r['room_type']} | {r['status']}\n"
        )

    return output