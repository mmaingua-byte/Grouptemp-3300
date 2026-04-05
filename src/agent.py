from tools import (
    check_guest_profile,
    check_reservation_status,
    update_reservation,
    list_all_reservations,
    log_event,
)

HELP_TEXT = """Available commands:
1. guest <guest_id>
   Example: guest G1001

2. reservation <reservation_id>
   Example: reservation R2001

3. update <reservation_id> <new_status>
   Example: update R2002 Confirmed

4. list
   Shows all reservations

5. help
   Shows this help menu

6. exit
   Closes the program
"""

def process_command(user_input: str) -> str:
    parts = user_input.strip().split()

    if not parts:
        return "Please type a command. Type 'help' to see options."

    command = parts[0].lower()

    if command == "help":
        return HELP_TEXT

    if command == "guest":
        if len(parts) < 2:
            return "Usage: guest <guest_id>"
        return check_guest_profile(parts[1])

    if command == "reservation":
        if len(parts) < 2:
            return "Usage: reservation <reservation_id>"
        return check_reservation_status(parts[1])

    if command == "update":
        if len(parts) < 3:
            return "Usage: update <reservation_id> <new_status>"
        reservation_id = parts[1]
        new_status = " ".join(parts[2:])
        return update_reservation(reservation_id, new_status)

    if command == "list":
        return list_all_reservations()

    if command == "exit":
        return "exit"

    return "Unknown command. Type 'help' to see available commands."

def run_agent() -> None:
    print("Hotel AI Voice Agent Started")
    print("Type 'help' to see available commands.")
    log_event("system", "Application started")

    while True:
        user_input = input("\nUser: ").strip()
        log_event("user", user_input)

        response = process_command(user_input)

        if response == "exit":
            print("Assistant: Goodbye.")
            log_event("assistant", "Goodbye.")
            break

        print(f"Assistant: {response}")
        log_event("assistant", response)
