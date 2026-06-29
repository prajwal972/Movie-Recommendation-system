"""
SQLite connection handling and schema initialization.

Uses the standard library's sqlite3 — no extra dependency, and the schema
below is written in plain, portable SQL so migrating to PostgreSQL later
(swap the connection factory + a couple of type tweaks: AUTOINCREMENT ->
SERIAL, TEXT timestamps -> TIMESTAMP) is a small, contained change rather
than a rewrite.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from config import settings as config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    phone_number  TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS favorites (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL,
    movie_title TEXT NOT NULL,
    added_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

CREATE TABLE IF NOT EXISTS watchlist (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL,
    movie_title TEXT NOT NULL,
    added_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

CREATE TABLE IF NOT EXISTS history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL,
    movie_title TEXT NOT NULL,
    viewed_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ratings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL,
    movie_title TEXT NOT NULL,
    rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

CREATE TABLE IF NOT EXISTS preferences (
    user_id          INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    language         TEXT NOT NULL DEFAULT 'en',
    preferred_genres TEXT NOT NULL DEFAULT '[]',
    updated_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id);
CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings(user_id);
"""


def _ensure_db_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def init_db(db_path: Path = config.DATABASE_PATH) -> None:
    """Create the database file and all tables if they don't already exist.

    Safe to call on every app startup — CREATE TABLE IF NOT EXISTS never
    touches existing data.
    """
    _ensure_db_dir(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_connection(db_path: Path = config.DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    """Context-managed connection with foreign keys + row access by column name."""
    _ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
