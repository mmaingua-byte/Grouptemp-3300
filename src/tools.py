import json
from datetime import datetime
from config import DATA_FILE, LOG_FILE

def _load_data() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"guests": [], "reservations": []}

def _save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def log_event(role: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {role.upper()}: {message}\n")

def check_guest_profile(guest_id: str) -> str:
    data = _load_data()
    for guest in data["guests"]:
        if guest["guest_id"].lower() == guest_id.lower():
            vip_label = "Yes" if guest["vip"] else "No"
            return (
                f"Guest Found\n"
                f"ID: {guest['guest_id']}\n"
                f"Name: {guest['name']}\n"
                f"Phone: {guest['phone']}\n"
                f"Email: {guest['email']}\n"
                f"VIP: {vip_label}"
            )
    return f"No guest found with ID {guest_id}."

def check_reservation_status(reservation_id: str) -> str:
    data = _load_data()
    for reservation in data["reservations"]:
        if reservation["reservation_id"].lower() == reservation_id.lower():
            return (
                f"Reservation Found\n"
                f"Reservation ID: {reservation['reservation_id']}\n"
                f"Guest ID: {reservation['guest_id']}\n"
                f"Room Type: {reservation['room_type']}\n"
                f"Status: {reservation['status']}\n"
                f"Check-In: {reservation['check_in']}\n"
                f"Check-Out: {reservation['check_out']}"
            )
    return f"No reservation found with ID {reservation_id}."

def update_reservation(reservation_id: str, new_status: str) -> str:
    data = _load_data()
    for reservation in data["reservations"]:
        if reservation["reservation_id"].lower() == reservation_id.lower():
            old_status = reservation["status"]
            reservation["status"] = new_status
            _save_data(data)
            return (
                f"Reservation {reservation_id} updated successfully. "
                f"Old Status: {old_status}. New Status: {new_status}."
            )
    return f"Unable to update. No reservation found with ID {reservation_id}."

def list_all_reservations() -> str:
    data = _load_data()
    if not data["reservations"]:
        return "No reservations available."
    lines = ["Reservation List"]
    for reservation in data["reservations"]:
        lines.append(
            f"- {reservation['reservation_id']} | "
            f"Guest {reservation['guest_id']} | "
            f"{reservation['room_type']} | "
            f"{reservation['status']}"
        )
    return "\n".join(lines)
