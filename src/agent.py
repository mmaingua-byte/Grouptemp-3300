from config import ALLOWED_STATUSES, APP_NAME
from tools import (
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

You can also talk naturally, for example:
- hello
- show reservations
- find guest G1001
- check in R2001
- check out reservation R2001
- cancel reservation R2002
- confirm reservation R2002
- tell me a joke
- fun fact
- riddle
"""


conversation_state = {
    "offer_pending": None,
    "last_fun_item": None,
}


def get_intro_text():
    return (
        f"Welcome to {APP_NAME}.\n"
        "I can help with guest profiles, reservations, check-in, check-out, "
        "status updates, and quick lookups.\n"
        "You can use commands or just talk to me like a person.\n"
        "For example, try:\n"
        "- show reservations\n"
        "- find guest G1001\n"
        "- check in reservation R2001\n"
        "- confirm reservation R2002\n"
        "- tell me a joke\n"
        "I promise to be more helpful than a hotel lobby printer."
    )


def get_goodbye_text():
    return (
        "Signing off. Thanks for stopping by — may your reservations be confirmed, "
        "your guests be happy, and your bugs stay far away."
    )


def _extract_id(text, prefix):
    words = text.replace(",", " ").replace(".", " ").replace("?", " ").split()
    for word in words:
        cleaned = word.strip().upper()
        if cleaned.startswith(prefix) and len(cleaned) >= 2:
            return cleaned
    return None


def _normalize_text(text):
    typo_fixes = {
        "reservtions": "reservations",
        "resrvations": "reservations",
        "resevations": "reservations",
        "gest": "guest",
        "huest": "guest",
        "guset": "guest",
        "chek in": "check in",
        "chek out": "check out",
        "cnfirm": "confirm",
        "cnacel": "cancel",
    }

    cleaned = text.lower().strip()
    for wrong, right in typo_fixes.items():
        cleaned = cleaned.replace(wrong, right)
    return cleaned


def _friendly_not_understood():
    return (
        "I’m not totally sure what you meant there, but I’m still rooting for us. "
        "Try 'help', or say something like 'show reservations' or 'check in R2001'."
    )


def _greeting_response():
    return (
        "Hello there. I’m ready to help with reservations, guests, and check-ins. "
        "Also, I occasionally come with jokes and suspicious confidence."
    )


def _thanks_response():
    return (
        "You’re welcome. I do not accept tips, but I do enjoy being appreciated."
    )


def _missing_reservation_for_action(action_word):
    return (
        f"I can help with {action_word}, but I need a reservation ID first. "
        f"Try something like '{action_word} R2001'."
    )


def _set_offer(kind):
    conversation_state["offer_pending"] = kind


def _clear_offer():
    conversation_state["offer_pending"] = None


def _tell_joke():
    conversation_state["last_fun_item"] = "joke"
    return (
        "Here’s a joke: Why did the hotel guest bring a ladder?\n"
        "Because they heard the room service was on another level."
    )


def _tell_fun_fact():
    conversation_state["last_fun_item"] = "fun_fact"
    return (
        "Fun fact: The first modern hotel in the United States is often credited to "
        "the Tremont House in Boston, opened in 1829, and it helped popularize "
        "features like indoor plumbing and a reception desk."
    )


def _tell_riddle():
    conversation_state["last_fun_item"] = "riddle"
    return (
        "Here’s a riddle: What has many keys but cannot open a single door?\n"
        "A piano."
    )


def _handle_yes_response():
    pending = conversation_state.get("offer_pending")

    if pending == "joke":
        _clear_offer()
        return _tell_joke()

    if pending == "fun_fact":
        _clear_offer()
        return _tell_fun_fact()

    if pending == "riddle":
        _clear_offer()
        return _tell_riddle()

    if pending == "fun_menu":
        _clear_offer()
        return (
            "Nice. Pick one: joke, fun fact, or riddle."
        )

    return None


def _handle_no_response():
    pending = conversation_state.get("offer_pending")
    if pending is not None:
        _clear_offer()
        return "No problem. I’ll save my comedy career for later."
    return None


def _match_small_talk(text):
    greetings = {
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening"
    }
    thanks_words = {
        "thanks", "thank you", "thx", "ty"
    }
    intro_words = {
        "who are you", "what can you do", "intro"
    }
    yes_words = {
        "yes", "yeah", "yep", "sure", "okay", "ok", "of course"
    }
    no_words = {
        "no", "nope", "not now"
    }

    if text in greetings:
        return _greeting_response()

    if text in thanks_words:
        return _thanks_response()

    if text in intro_words:
        return get_intro_text()

    if text in yes_words:
        return _handle_yes_response()

    if text in no_words:
        return _handle_no_response()

    if text in {"bye", "goodbye", "exit", "quit"}:
        return "exit"

    return None


def _match_fun_responses(text):
    if "want to hear a joke" in text or "hear a joke" in text:
        _set_offer("joke")
        return "Always. Want to hear a joke?"

    if "want to hear a fun fact" in text or "hear a fun fact" in text:
        _set_offer("fun_fact")
        return "I’ve got one ready. Want to hear a fun fact?"

    if "want to hear a riddle" in text or "hear a riddle" in text:
        _set_offer("riddle")
        return "Excellent choice. Want to hear a riddle?"

    if text in {"tell me a joke", "joke", "say a joke"}:
        return _tell_joke()

    if text in {"tell me a fun fact", "fun fact", "say a fun fact"}:
        return _tell_fun_fact()

    if text in {"tell me a riddle", "riddle", "say a riddle"}:
        return _tell_riddle()

    if "something fun" in text or "make me laugh" in text:
        _set_offer("fun_menu")
        return "I can do that. Want a joke, a fun fact, or a riddle?"

    if "that's funny" in text or "thats funny" in text or "that was funny" in text:
        return "HAHAHA, I know. I'm the birthday!"

    if "that was good" in text or "good one" in text:
        return "Thank you, thank you. I’ll be here all runtime."

    return None


def _match_natural_language(user_input, repo):
    text = _normalize_text(user_input)

    if not text:
        return "Please type something. Even a tiny clue helps."

    small_talk = _match_small_talk(text)
    if small_talk is not None:
        return small_talk

    fun_response = _match_fun_responses(text)
    if fun_response is not None:
        return fun_response

    if "help" == text or text == "menu":
        return HELP_TEXT

    if "show reservations" in text or "all reservations" in text or "list reservations" in text:
        return list_all_reservations(repo)

    if text == "list":
        return list_all_reservations(repo)

    if "find guest" in text or "show guest" in text or "guest" in text:
        guest_id = _extract_id(text, "G")
        if guest_id:
            return check_guest_profile(repo, guest_id)

    if "find reservation" in text or "show reservation" in text or "reservation" in text:
        reservation_id = _extract_id(text, "R")
        if reservation_id and "check in" not in text and "check out" not in text and "cancel" not in text and "confirm" not in text:
            return check_reservation_status(repo, reservation_id)

    if "check in" in text:
        reservation_id = _extract_id(text, "R")
        if reservation_id:
            result = update_reservation(repo, reservation_id, "Checked-In")
            if "Updated" in result or "updated successfully" in result:
                return f"{result} The front desk energy is immaculate."
            return result
        return _missing_reservation_for_action("check in")

    if "check out" in text:
        reservation_id = _extract_id(text, "R")
        if reservation_id:
            result = update_reservation(repo, reservation_id, "Checked-Out")
            if "Updated" in result or "updated successfully" in result:
                return f"{result} Another smooth departure. Love to see it."
            return result
        return _missing_reservation_for_action("check out")

    if "cancel" in text and "reservation" in text:
        reservation_id = _extract_id(text, "R")
        if reservation_id:
            result = update_reservation(repo, reservation_id, "Cancelled")
            if "Updated" in result or "updated successfully" in result:
                return f"{result} Not the ending we wanted, but at least the system is honest."
            return result
        return (
            "I can cancel a reservation, but I need the reservation ID first. "
            "Try 'cancel reservation R2002'."
        )

    if "confirm" in text and "reservation" in text:
        reservation_id = _extract_id(text, "R")
        if reservation_id:
            result = update_reservation(repo, reservation_id, "Confirmed")
            if "Updated" in result or "updated successfully" in result:
                return f"{result} Nice. We love a confirmed plan."
            return result
        return (
            "I can confirm a reservation, but I need the reservation ID first. "
            "Try 'confirm reservation R2002'."
        )

    if text in {"what are the options", "what can i say", "commands"}:
        return HELP_TEXT

    return None


def process_command(user_input, repo):
    natural_response = _match_natural_language(user_input, repo)
    if natural_response is not None:
        return natural_response

    parts = user_input.strip().split()

    if not parts:
        return "Please type a command. I left my mind-reading badge at home."

    command = parts[0].lower()

    typo_map = {
        "huest": "guest",
        "gesut": "guest",
        "guset": "guest",
        "resrvation": "reservation",
        "resevation": "reservation",
        "udpate": "update",
        "updat": "update",
        "hep": "help",
        "hlep": "help",
        "lst": "list",
        "intr0": "intro",
    }
    command = typo_map.get(command, command)

    if command == "help":
        return HELP_TEXT

    if command == "intro":
        return get_intro_text()

    if command == "guest":
        if len(parts) < 2:
            return "Usage: guest <guest_id>  |  Example: guest G1001"
        return check_guest_profile(repo, parts[1])

    if command == "reservation":
        if len(parts) < 2:
            return "Usage: reservation <reservation_id>  |  Example: reservation R2001"
        return check_reservation_status(repo, parts[1])

    if command == "update":
        if len(parts) < 3:
            return "Usage: update <reservation_id> <new_status>  |  Example: update R2002 Confirmed"
        reservation_id = parts[1]
        new_status = " ".join(parts[2:])
        result = update_reservation(repo, reservation_id, new_status)
        if "Updated" in result or "updated successfully" in result:
            return f"{result} Administrative excellence achieved."
        return result

    if command == "list":
        return list_all_reservations(repo)

    if command == "exit":
        return "exit"

    return _friendly_not_understood()


def run_agent():
    repo = get_repository()

    intro = get_intro_text()
    print(intro)
    log_event("assistant", intro)

    while True:
        user_input = input("\nUser: ").strip()
        log_event("user", user_input)

        response = process_command(user_input, repo)

        if response == "exit":
            goodbye = get_goodbye_text()
            print("Assistant:", goodbye)
            log_event("assistant", goodbye)
            break

        print("Assistant:", response)
        log_event("assistant", response)