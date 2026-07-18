import re

from app.common.exceptions import ValidationException

USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,63}$")


def validate_username(username: str) -> None:
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValidationException(
            "Username may contain lowercase letters, numbers, dots, "
            "underscores, and hyphens."
        )
