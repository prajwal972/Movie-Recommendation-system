"""
Session-state helpers: search history, recently-viewed, and the
authentication state machine (login/logout/current user).

Auth state lives in st.session_state, scoped to the current browser
connection — see services/auth_service.py's module docstring for exactly
what that does and doesn't persist across refreshes.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from database.models import User


def init_session_state() -> None:
    defaults = {
        "search_history": [],
        "recently_viewed": [],
        "recommendation_count": 0,
        "search_count": 0,
        "auth_user": None,  # dict snapshot of the logged-in User, or None
        "language": "en",
        "prefill_movie": None,
        "auto_recommend": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Auth state
# ---------------------------------------------------------------------------
def login_session(user: User) -> None:
    st.session_state["auth_user"] = {
        "id": user.id, "username": user.username, "email": user.email,
    }


def logout_session() -> None:
    st.session_state["auth_user"] = None


def is_authenticated() -> bool:
    init_session_state()
    return st.session_state.get("auth_user") is not None


def current_user_id() -> Optional[int]:
    init_session_state()
    user = st.session_state.get("auth_user")
    return user["id"] if user else None


def current_username() -> Optional[str]:
    init_session_state()
    user = st.session_state.get("auth_user")
    return user["username"] if user else None


# ---------------------------------------------------------------------------
# Search history / recently viewed (guest-friendly, session-only)
# ---------------------------------------------------------------------------
def add_to_search_history(query: str, max_items: int = 15) -> None:
    init_session_state()
    history = st.session_state["search_history"]
    if query in history:
        history.remove(query)
    history.insert(0, query)
    st.session_state["search_history"] = history[:max_items]
    st.session_state["search_count"] += 1


def add_to_recently_viewed(title: str, max_items: int = 10) -> None:
    init_session_state()
    viewed = st.session_state["recently_viewed"]
    if title in viewed:
        viewed.remove(title)
    viewed.insert(0, title)
    st.session_state["recently_viewed"] = viewed[:max_items]


def increment_recommendation_count() -> None:
    init_session_state()
    st.session_state["recommendation_count"] += 1


def queue_movie_details_bridge(movie_title: str) -> None:
    """Used by 'View Details' on a movie card: stash the title and jump to
    the Recommendations page, which reads this on load to pre-fill + auto-run
    the search instead of landing on an empty search box."""
    st.session_state["prefill_movie"] = movie_title
    st.session_state["auto_recommend"] = True
