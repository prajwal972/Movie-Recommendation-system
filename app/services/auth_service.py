"""
Authentication service: registration, login, and password hashing.

Honest scope note (read this before assuming more than is built):
- Passwords are properly hashed with bcrypt — never stored or compared in
  plain text.
- Email and phone number are validated for *format* only. There is no
  email-verification link or SMS/OTP step, because that requires a real
  third-party email/SMS provider (SendGrid, Twilio, etc.) wired up with its
  own account and credentials, which is a deliberate next step, not
  something fakeable from inside this app.
- Streamlit has no built-in persistent session/cookie system. A logged-in
  state lives in `st.session_state`, which survives page navigation and
  reruns within the same browser tab/connection, but a hard refresh or new
  tab starts logged out again. For real "remember me" persistence across
  browser restarts, the standard next step is the `streamlit-authenticator`
  package (signed cookies) — noted in the README roadmap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import bcrypt

import config.settings as config
from database.models import User, create_user, get_user_by_identifier, username_or_email_taken

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


@dataclass
class AuthResult:
    success: bool
    user: Optional[User] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed hash (e.g. corrupted data) — fail closed, not open.
        return False


def validate_registration(
    username: str, email: str, phone_number: str, password: str, confirm_password: str,
) -> List[str]:
    """Return a list of validation error messages (empty list == valid)."""
    errors: List[str] = []

    if not USERNAME_RE.match(username or ""):
        errors.append("Username must be 3-20 characters: letters, numbers, and underscores only.")
    if not EMAIL_RE.match(email or ""):
        errors.append("Enter a valid email address.")
    if not PHONE_RE.match((phone_number or "").replace(" ", "")):
        errors.append("Enter a valid phone number (7-15 digits, optional leading +).")
    if len(password or "") < config.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters.")
    elif not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        errors.append("Password must contain at least one letter and one number.")
    if password != confirm_password:
        errors.append("Passwords do not match.")

    if not errors and username_or_email_taken(username, email):
        errors.append("That username or email is already registered.")

    return errors


def register_user(
    username: str, email: str, phone_number: str, password: str, confirm_password: str,
) -> AuthResult:
    errors = validate_registration(username, email, phone_number, password, confirm_password)
    if errors:
        return AuthResult(success=False, errors=errors)

    user = create_user(
        username=username, email=email, phone_number=phone_number,
        password_hash=hash_password(password),
    )
    return AuthResult(success=True, user=user)


def login_user(identifier: str, password: str) -> AuthResult:
    """``identifier`` may be a username or an email address."""
    if not identifier or not password:
        return AuthResult(success=False, errors=["Enter your username/email and password."])

    user = get_user_by_identifier(identifier)
    if user is None or not verify_password(password, user.password_hash):
        # Same error for "no such user" and "wrong password" — don't leak
        # which one it was, that's a basic account-enumeration precaution.
        return AuthResult(success=False, errors=["Incorrect username/email or password."])

    return AuthResult(success=True, user=user)
