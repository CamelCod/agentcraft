"""Unit tests for JWT and password hashing."""
import pytest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, decode_token,
)


def test_password_round_trip():
    plain = "SecureP@ssw0rd!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_wrong_password_rejected():
    hashed = hash_password("correct_password")
    assert not verify_password("wrong_password", hashed)


def test_jwt_round_trip():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_jwt_tampered_rejected():
    from jose import JWTError
    token = create_access_token("user-123")
    bad_token = token[:-4] + "xxxx"
    with pytest.raises(JWTError):
        decode_token(bad_token)
