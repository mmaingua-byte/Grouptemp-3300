import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

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
    """Raised when the data file is malformed or contains invalid values."""


def log_event(role: str, message: str) -> None:
    """Append a timestamped message to the application log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {role.upper()}: {message}\n")


def _ensure_data_file_exists() -> None:
    """Create the data file with defaults if it does not exist."""
    data_path = Path(DATA_FILE)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        with open(data_path, "w", encoding="utf-8") as file:
            json.dump(DEFAULT_DATA, file, indent=2)


def _validate_date(date_text: str, field_name: str) -> None:
    """Validate that the string uses YYYY-MM-DD format."""
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError as exc:
        raise DataValidationError(
            f"Invalid date format for '{field_name}'. Use YYYY-MM-DD."
        ) from exc


def _validate_guest(guest: Any, seen_guest_ids: set[str]) -> None:
    """Validate one guest record."""
    if not isinstance(guest, dict):
        raise DataValidationError("Each guest entry must be an object.")

    required_fields = {
        "guest_id": str,
        "name": str,
        "phone": str,
        "email": str,
        "vip": bool,
    }

    for field, expected_type in required_fields.items():
        if field not in guest:
            raise DataValidationError(f"Guest record missing required field '{field}'.")
        if not isinstance(guest[field], expected_type):
            raise DataValidationError(
                f"Guest field '{field}' must be of type {expected_type.__name__}."
            )

    guest_id = guest["guest_id"].strip()
    if not guest_id:
        raise DataValidationError("Guest ID cannot be empty.")
    if guest_id in seen_guest_ids:
        raise DataValidationError(f"Duplicate guest ID found: {guest_id}")
    seen_guest_ids.add(guest_id)


def _validate_reservation(
    reservation: Any,
    seen_reservation_ids: set[str],
    valid_guest_ids: set[str],
) -> None:
    """Validate one reservation record."""
    if not isinstance(reservation, dict):
        raise DataValidationError("Each reservation entry must be an object.")

    required_fields = {
        "reservation_id": str,
        "guest_id": str,
        "room_type": str,
        "status": str,
        "check_in": str,
        "check_out": str,
    }

    for field, expected_type in required_fields.items():
        if field not in reservation:
            raise DataValidationError(
                f"Reservation record missing required field '{field}'."
            )
        if not isinstance(reservation[field], expected_type):
            raise DataValidationError(
                f"Reservation field '{field}' must be of type {expected_type.__name__}."
            )

    reservation_id = reservation["reservation_id"].strip()
    if not reservation_id:
        raise DataValidationError("Reservation ID cannot be empty.")
    if reservation_id in seen_reservation_ids:
        raise DataValidationError(f"Duplicate reservation ID found: {reservation_id}")
    seen_reservation_ids.add(reservation_id)

    guest_id = reservation["guest_id"].strip()
    if guest_id not in valid_guest_ids:
        raise DataValidationError(
            f"Reservation '{reservation_id}' references unknown guest ID '{guest_id}'."
        )

    status = reservation["status"].strip()
    if status not in ALLOWED_STATUSES:
        raise DataValidationError(
            f"Reservation '{reservation_id}' has invalid status '{status}'."
        )

    _validate_date(reservation["check_in"], "check_in")
    _validate_date(reservation["check_out"], "check_out")

    check_in_date = datetime.strptime(reservation["check_in"], "%Y-%m-%d")
    check_out_date = datetime.strptime(reservation["check_out"], "%Y-%m-%d")
    if check_out_date <= check_in_date:
        raise DataValidationError(
            f"Reservation '{reservation_id}' must have check_out after check_in."
        )


def validate_data(data: Any) -> dict[str, list[dict[str, Any]]]:
    """Validate the full data structure and return it if valid."""
    if not isinstance(data, dict):
        raise DataValidationError("Data file must contain a JSON object.")

    if "guests" not in data or "reservations" not in data:
        raise DataValidationError(
            "Data file must contain both 'guests' and 'reservations' keys."
        )

    guests = data["guests"]
    reservations = data["reservations"]

    if not isinstance(guests, list) or not isinstance(reservations, list):
        raise DataValidationError("'guests' and 'reservations' must both be lists.")

    seen_guest_ids: set[str] = set()
    for guest in guests:
        _validate_guest(guest, seen_guest_ids)

    seen_reservation_ids: set[str] = set()
    for reservation in reservations:
        _validate_reservation(reservation, seen_reservation_ids, seen_guest_ids)

    return data


class HotelRepository:
    """Loads, validates, indexes, and updates hotel data."""

    def __init__(self, data_file: Path | str = DATA_FILE) -> None:
        self.data_file = Path(data_file)
        self.data: dict[str, list[dict[str, Any]]] = {"guests": [], "reservations": []}
        self.guests_by_id: dict[str, dict[str, Any]] = {}
        self.reservations_by_id: dict[str, dict[str, Any]] = {}
        self.reload()

    def reload(self) -> None:
        """Load and validate data from disk once."""
        _ensure_data_file_exists()

        with open(self.data_file, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        self.data = validate_data(raw_data)
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        """Create fast dictionary lookups for guests and reservations."""
        self.guests_by_id = {
            guest["guest_id"].lower(): guest for guest in self.data["guests"]
        }
        self.reservations_by_id = {
            reservation["reservation_id"].lower(): reservation
            for reservation in self.data["reservations"]
        }

    def save(self) -> None:
        """Persist current validated data to disk."""
        validate_data(self.data)
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2)
        self._rebuild_indexes()

    def get_guest(self, guest_id: str) -> dict[str, Any] | None:
        """Return one guest record by ID."""
        return self.guests_by_id.get(guest_id.strip().lower())

    def get_reservation(self, reservation_id: str) -> dict[str, Any] | None:
        """Return one reservation record by ID."""
        return self.reservations_by_id.get(reservation_id.strip().lower())

    def list_reservations(self) -> list[dict[str, Any]]:
        """Return a copy of all reservation records."""
        return deepcopy(self.data["reservations"])

    def update_reservation_status(
        self, reservation_id: str, new_status: str
    ) -> tuple[bool, str]:
        """Update a reservation status if allowed by business rules."""
        cleaned_id = reservation_id.strip().lower()
        normalized_status = new_status.strip().title()

        if normalized_status not in ALLOWED_STATUSES:
            allowed = ", ".join(sorted(ALLOWED_STATUSES))
            return False, f"Invalid status. Allowed values are: {allowed}."

        reservation = self.reservations_by_id.get(cleaned_id)
        if reservation is None:
            return False, f"No reservation found with ID {reservation_id}."

        current_status = reservation["status"]
        if current_status == normalized_status:
            return (
                False,
                f"Reservation {reservation['reservation_id']} is already marked as {current_status}.",
            )

        allowed_next_statuses = STATUS_TRANSITIONS.get(current_status, set())
        if normalized_status not in allowed_next_statuses:
            allowed_text = ", ".join(sorted(allowed_next_statuses)) or "no further changes"
            return (
                False,
                f"Cannot change reservation {reservation['reservation_id']} from "
                f"{current_status} to {normalized_status}. Allowed next status: {allowed_text}.",
            )

        reservation["status"] = normalized_status
        self.save()
        return (
            True,
            f"Reservation {reservation['reservation_id']} updated successfully. "
            f"Old Status: {current_status}. New Status: {normalized_status}.",
        )


def get_repository() -> HotelRepository:
    """Create and return a validated repository instance."""
    return HotelRepository()


def check_guest_profile(repository: HotelRepository, guest_id: str) -> str:
    """Return formatted guest profile details."""
    guest = repository.get_guest(guest_id)
    if guest is None:
        return (
            f"I could not find a guest with ID {guest_id}. "
            "Please check the ID and try again."
        )

    vip_label = "Yes" if guest["vip"] else "No"
    return (
        "Guest Found\n"
        f"ID: {guest['guest_id']}\n"
        f"Name: {guest['name']}\n"
        f"Phone: {guest['phone']}\n"
        f"Email: {guest['email']}\n"
        f"VIP: {vip_label}"
    )


def check_reservation_status(repository: HotelRepository, reservation_id: str) -> str:
    """Return formatted reservation details."""
    reservation = repository.get_reservation(reservation_id)
    if reservation is None:
        return (
            f"I could not find a reservation with ID {reservation_id}. "
            "Please check the ID and try again."
        )

    return (
        "Reservation Found\n"
        f"Reservation ID: {reservation['reservation_id']}\n"
        f"Guest ID: {reservation['guest_id']}\n"
        f"Room Type: {reservation['room_type']}\n"
        f"Status: {reservation['status']}\n"
        f"Check-In: {reservation['check_in']}\n"
        f"Check-Out: {reservation['check_out']}"
    )


def update_reservation(
    repository: HotelRepository, reservation_id: str, new_status: str
) -> str:
    """Update reservation status and return a user-friendly message."""
    success, message = repository.update_reservation_status(reservation_id, new_status)
    return message


def list_all_reservations(repository: HotelRepository) -> str:
    """Return a formatted list of reservations."""
    reservations = repository.list_reservations()
    if not reservations:
        return "No reservations are available right now."

    lines = ["Reservation List"]
    for reservation in reservations:
        lines.append(
            f"- {reservation['reservation_id']} | "
            f"Guest {reservation['guest_id']} | "
            f"{reservation['room_type']} | "
            f"{reservation['status']} | "
            f"{reservation['check_in']} to {reservation['check_out']}"
        )
    return "\n".join(lines)
