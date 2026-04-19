import sys

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Request

from bus_zeiterfassung.config import settings

_ph = PasswordHasher()
SESSION_KEY = "authed"


class NotAuthenticated(Exception):
    """Raised by the require_login dependency when no valid session exists."""


def verify_pin(pin: str) -> bool:
    try:
        _ph.verify(settings.pin_hash, pin)
    except VerifyMismatchError:
        return False
    return True


def require_login(request: Request) -> None:
    if request.session.get(SESSION_KEY) is not True:
        raise NotAuthenticated


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] != "hash":
        print("Usage: python -m bus_zeiterfassung.auth hash <pin>", file=sys.stderr)
        sys.exit(2)
    print(_ph.hash(sys.argv[2]))


if __name__ == "__main__":
    main()
