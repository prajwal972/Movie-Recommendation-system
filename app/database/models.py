"""
Typed CRUD functions over the SQLite schema in database/db.py.

Every function opens its own short-lived connection via get_connection() —
simple and safe for Streamlit's per-script-rerun execution model, and cheap
enough for SQLite at this scale. If this ever needs to handle real
concurrent load, swap get_connection() for a pooled PostgreSQL connection
here and nothing above this module has to change.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from database.db import get_connection


@dataclass
class User:
    id: int
    username: str
    email: str
    phone_number: str
    password_hash: str
    created_at: str


@dataclass
class MovieRef:
    """A lightweight (movie_id, title, timestamp) row — shape shared by
    favorites/watchlist/history so the UI layer can treat them uniformly."""

    movie_id: int
    movie_title: str
    timestamp: str


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def create_user(username: str, email: str, phone_number: str, password_hash: str) -> User:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, email, phone_number, password_hash) "
            "VALUES (?, ?, ?, ?)",
            (username.strip(), email.strip().lower(), phone_number.strip(), password_hash),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        conn.execute(
            "INSERT OR IGNORE INTO preferences (user_id) VALUES (?)", (cursor.lastrowid,)
        )
        return _row_to_user(row)


def get_user_by_identifier(identifier: str) -> Optional[User]:
    """Look up a user by username OR email — login accepts either."""
    identifier = identifier.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE lower(username) = ? OR lower(email) = ?",
            (identifier, identifier),
        ).fetchone()
        return _row_to_user(row) if row else None


def username_or_email_taken(username: str, email: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE lower(username) = ? OR lower(email) = ?",
            (username.strip().lower(), email.strip().lower()),
        ).fetchone()
        return row is not None


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"], username=row["username"], email=row["email"],
        phone_number=row["phone_number"], password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------
def add_favorite(user_id: int, movie_id: int, movie_title: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO favorites (user_id, movie_id, movie_title) VALUES (?, ?, ?)",
            (user_id, movie_id, movie_title),
        )


def remove_favorite(user_id: int, movie_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM favorites WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))


def is_favorite(user_id: int, movie_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND movie_id = ?", (user_id, movie_id)
        ).fetchone()
        return row is not None


def list_favorites(user_id: int) -> List[MovieRef]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT movie_id, movie_title, added_at FROM favorites "
            "WHERE user_id = ? ORDER BY added_at DESC", (user_id,),
        ).fetchall()
        return [MovieRef(r["movie_id"], r["movie_title"], r["added_at"]) for r in rows]


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------
def add_to_watchlist(user_id: int, movie_id: int, movie_title: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, movie_id, movie_title) VALUES (?, ?, ?)",
            (user_id, movie_id, movie_title),
        )


def remove_from_watchlist(user_id: int, movie_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))


def is_in_watchlist(user_id: int, movie_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id)
        ).fetchone()
        return row is not None


def list_watchlist(user_id: int) -> List[MovieRef]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT movie_id, movie_title, added_at FROM watchlist "
            "WHERE user_id = ? ORDER BY added_at DESC", (user_id,),
        ).fetchall()
        return [MovieRef(r["movie_id"], r["movie_title"], r["added_at"]) for r in rows]


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
def add_history(user_id: int, movie_id: int, movie_title: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO history (user_id, movie_id, movie_title, viewed_at) VALUES (?, ?, ?, ?)",
            (user_id, movie_id, movie_title, datetime.now(timezone.utc).isoformat()),
        )


def list_history(user_id: int, limit: int = 50) -> List[MovieRef]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT movie_id, movie_title, viewed_at FROM history "
            "WHERE user_id = ? ORDER BY viewed_at DESC LIMIT ?", (user_id, limit),
        ).fetchall()
        return [MovieRef(r["movie_id"], r["movie_title"], r["viewed_at"]) for r in rows]


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------
def set_rating(user_id: int, movie_id: int, movie_title: str, rating: int) -> None:
    if not 1 <= rating <= 5:
        raise ValueError("rating must be between 1 and 5")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ratings (user_id, movie_id, movie_title, rating) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, movie_id) DO UPDATE SET rating = excluded.rating, "
            "rated_at = CURRENT_TIMESTAMP",
            (user_id, movie_id, movie_title, rating),
        )


def get_rating(user_id: int, movie_id: int) -> Optional[int]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT rating FROM ratings WHERE user_id = ? AND movie_id = ?", (user_id, movie_id)
        ).fetchone()
        return row["rating"] if row else None


# ---------------------------------------------------------------------------
# Preferences (language + preferred genres)
# ---------------------------------------------------------------------------
def get_language(user_id: int) -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT language FROM preferences WHERE user_id = ?", (user_id,)).fetchone()
        return row["language"] if row else "en"


def set_language(user_id: int, language: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO preferences (user_id, language) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET language = excluded.language, "
            "updated_at = CURRENT_TIMESTAMP",
            (user_id, language),
        )


def get_preferred_genres(user_id: int) -> List[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT preferred_genres FROM preferences WHERE user_id = ?", (user_id,)
        ).fetchone()
        return json.loads(row["preferred_genres"]) if row else []


def set_preferred_genres(user_id: int, genres: List[str]) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO preferences (user_id, preferred_genres) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET preferred_genres = excluded.preferred_genres, "
            "updated_at = CURRENT_TIMESTAMP",
            (user_id, json.dumps(genres)),
        )
