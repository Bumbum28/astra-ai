def normalize_email(email: str) -> str:
    return email.strip().casefold()


def normalize_username(username: str) -> str:
    return username.strip().casefold()
