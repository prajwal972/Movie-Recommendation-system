"""
TMDB integration: poster artwork and trailer links.

Both functions degrade gracefully with no API key configured or on any
network/API error — they never raise, so a missing key never breaks a page,
it just means placeholder art / a YouTube search link instead of the exact
official trailer.
"""

from __future__ import annotations

import logging

import requests
import streamlit as st

import config.settings as config

logger = logging.getLogger("cinematch")


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def fetch_poster(movie_id: int) -> str:
    """Return a poster image URL for ``movie_id`` via the TMDB API."""
    if not config.TMDB_API_KEY:
        return config.PLACEHOLDER_POSTER_URL

    url = f"{config.TMDB_BASE_URL}/movie/{movie_id}"
    params = {"api_key": config.TMDB_API_KEY, "language": "en-US"}

    try:
        response = requests.get(url, params=params, timeout=config.TMDB_REQUEST_TIMEOUT)
        response.raise_for_status()
        poster_path = response.json().get("poster_path")
        return f"{config.TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else config.PLACEHOLDER_POSTER_URL
    except requests.exceptions.RequestException as exc:
        logger.warning("TMDB poster fetch failed for movie_id=%s: %s", movie_id, exc)
        return config.PLACEHOLDER_POSTER_URL


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def fetch_trailer_url(movie_id: int, movie_title: str) -> tuple[str, bool]:
    """Return (url, is_official).

    Tries TMDB's /videos endpoint for an official YouTube trailer first.
    Falls back to a YouTube *search* link (not a guaranteed trailer) if no
    API key is set or no official trailer is listed — ``is_official`` tells
    the UI which case it got, so it can label the button honestly
    ("Watch Trailer" vs "Search for Trailer").
    """
    fallback_query = f"{movie_title} official trailer".replace(" ", "+")
    fallback_url = f"{config.YOUTUBE_SEARCH_BASE_URL}{fallback_query}"

    if not config.TMDB_API_KEY:
        return fallback_url, False

    url = f"{config.TMDB_BASE_URL}/movie/{movie_id}/videos"
    params = {"api_key": config.TMDB_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=config.TMDB_REQUEST_TIMEOUT)
        response.raise_for_status()
        results = response.json().get("results", [])
        trailers = [
            v for v in results
            if v.get("site") == "YouTube" and v.get("type") == "Trailer"
        ]
        if trailers:
            official = next((v for v in trailers if v.get("official")), trailers[0])
            return f"https://www.youtube.com/watch?v={official['key']}", True
        return fallback_url, False
    except requests.exceptions.RequestException as exc:
        logger.warning("TMDB trailer fetch failed for movie_id=%s: %s", movie_id, exc)
        return fallback_url, False
