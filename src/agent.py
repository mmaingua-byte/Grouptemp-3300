from config import ALLOWED_STATUSES, APP_NAME
from tools import (
    DataValidationError,
    check_guest_profile,
    check_reservation_status,
    get_repository,
    list_all_reservations,
    log_event,
    update_reservation,
)

HELP_TEXT = f"""Available commands:
1. guest <guest_id>
   Example: guest G1001
   Purpose: Look up a guest profile.

2. reservation <reservation_id>
   Example: reservation R2001
   Purpose: Check reservation details and current status.

3. update <reservation_id> <new_status>
   Example: update R2002 Confirmed
   Purpose: Change a reservation status.
   Allowed statuses: {", ".join(sorted(ALLOWED_STATUSES))}

4. list
   Purpose: Show all reservations.

5. intro
   Purpose: Show the welcome message again.

6. help
   Purpose: Show this help menu.

7. exit
   Purpose: Close the program.
"""


def get_intro_text() -> str:
    return (
        f"Welcome to {APP_NAME}.\n"
        "I can help you check guest profiles, review reservation details, "
        "update reservation statuses, and list all reservations.\n"
        "Type 'help' to see available commands."
    )


def process_command(user_input: str, repository) -> str:
    parts = user_input.strip().split()

    if not parts:
        return "Please type a command. Type 'help' to see available options."

    command = parts[0].lower()

    if command == "help":
        return HELP_TEXT

    if command == "intro":
        return get_intro_text()

    if command == "guest":
        if len(parts) < 2:
            return "Usage: guest <guest_id>"
        return check_guest_profile(repository, parts[1])

    if command == "reservation":
        if len(parts) < 2:
            return "Usage: reservation <reservation_id>"
        return check_reservation_status(repository, parts[1])

    if command == "update":
        if len(parts) < 3:
            return "Usage: update <reservation_id> <new_status>"
        reservation_id = parts[1]
        new_status = " ".join(parts[2:])
        return update_reservation(repository, reservation_id, new_status)

    if command == "list":
        return list_all_reservations(repository)

    if command == "exit":
        return "exit"

    return "Unknown command. Type 'help' to see available commands."


def run_agent() -> None:
    print(get_intro_text())
    log_event("system", "Application started")

    try:
        repository = get_repository()
        log_event("system", "Data loaded and validated successfully")
    except FileNotFoundError:
        message = "Data file was not found."
        print(f"Assistant: {message}")
        log_event("system", message)
        return
    except DataValidationError as exc:
        message = f"Data validation error: {exc}"
        print(f"Assistant: {message}")
        log_event("system", message)
        return
    except Exception as exc:
        message = f"Unexpected startup error: {exc}"
        print(f"Assistant: {message}")
        log_event("system", message)
        return

    while True:
        try:
            user_input = input("\nUser: ").strip()
        except EOFError:
            print("\nAssistant: Goodbye.")
            log_event("assistant", "Goodbye.")
            break
        except KeyboardInterrupt:
            print("\nAssistant: Goodbye.")
            log_event("assistant", "Goodbye.")
            break

        log_event("user", user_input)
        response = process_command(user_input, repository)

        if response == "exit":
            goodbye_message = "Goodbye. Thank you for using the Hotel AI Voice Agent."
            print(f"Assistant: {goodbye_message}")
            log_event("assistant", goodbye_message)
            break

        print(f"Assistant: {response}")
        log_event("assistant", response)
