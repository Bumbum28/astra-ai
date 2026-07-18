from uuid import uuid4

import pytest

from app.common.exceptions import AuthenticationException, ValidationException
from app.core.config import AppConfig
from app.domains.auth.security import PasswordHasher, TokenService


def test_password_hash_and_verify() -> None:
    hasher = PasswordHasher(rounds=10, minimum_length=8)
    password_hash = hasher.hash("correct horse battery staple")
    assert password_hash != "correct horse battery staple"
    assert hasher.verify("correct horse battery staple", password_hash)
    assert not hasher.verify("wrong password", password_hash)


def test_password_rejects_more_than_72_bytes() -> None:
    hasher = PasswordHasher(rounds=10, minimum_length=8)
    with pytest.raises(ValidationException):
        hasher.hash("á" * 40)


def test_access_token_cannot_be_used_as_refresh_token() -> None:
    token_service = TokenService(AppConfig())
    token = token_service.create_access_token(uuid4())
    with pytest.raises(AuthenticationException):
        token_service.decode(token, expected_type="refresh")
