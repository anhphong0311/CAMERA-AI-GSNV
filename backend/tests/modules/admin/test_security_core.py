"""Unit test — Security core (password policy + JWT tokens)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from app.modules.admin.security.password_policy import (
    PasswordPolicy,
    is_password_expired,
    validate_password,
)
from app.modules.admin.security.tokens import create_token_pair, verify_token


def test_strong_password_passes():
    result = validate_password("Str0ng@Pass", PasswordPolicy())
    assert result.valid
    assert result.errors == []


@pytest.mark.parametrize(
    "pwd",
    ["short", "alllowercase1!", "NOLOWER1!", "NoDigits!!", "NoSpecial123", "password"],
)
def test_weak_passwords_fail(pwd):
    result = validate_password(pwd, PasswordPolicy())
    assert not result.valid
    assert result.errors


def test_password_expiration():
    policy = PasswordPolicy(max_age_days=30)
    old = datetime.now(timezone.utc) - timedelta(days=31)
    fresh = datetime.now(timezone.utc) - timedelta(days=1)
    assert is_password_expired(old, policy)
    assert not is_password_expired(fresh, policy)
    assert not is_password_expired(old, PasswordPolicy(max_age_days=0))


def test_policy_roundtrip():
    p = PasswordPolicy(min_length=12, require_special=False)
    assert PasswordPolicy.from_dict(p.to_dict()) == p


def test_token_pair_and_verify():
    pair = create_token_pair("user-1", "admin", ["users:read"], remember=False)
    access = verify_token(pair.access_token, "access")
    refresh = verify_token(pair.refresh_token, "refresh")
    assert access["sub"] == "user-1"
    assert access["role"] == "admin"
    assert "users:read" in access["permissions"]
    assert refresh["jti"] == pair.refresh_jti
    assert access["jti"] != refresh["jti"]


def test_token_wrong_type_rejected():
    pair = create_token_pair("u", "viewer", [], remember=False)
    with pytest.raises(JWTError):
        verify_token(pair.access_token, "refresh")


def test_remember_extends_refresh():
    normal = create_token_pair("u", "viewer", [], remember=False)
    remembered = create_token_pair("u", "viewer", [], remember=True)
    assert remembered.refresh_expires_in > normal.refresh_expires_in
