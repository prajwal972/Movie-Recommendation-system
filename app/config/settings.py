"""
Centralized configuration for CineMatch AI.

All paths, API settings, theme constants, and feature config live here so
the rest of the app never hard-codes a magic string. Secrets (TMDB API key,
the session signing secret) are read from environment variables / a local
.env file and are never committed.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# This file lives at app/config/settings.py, so we go up two levels for the
# app/ root and three for the repo root.
CONFIG_DIR: Path = Path(__file__).resolve().parent
APP_DIR: Path = CONFIG_DIR.parent
ROOT_DIR: Path = APP_DIR.parent

MODELS_DIR: Path = ROOT_DIR / "models"
DATA_DIR: Path = ROOT_DIR / "data"

MOVIES_PKL: Path = MODELS_DIR / "movies.pkl"
SIMILARITY_PKL: Path = MODELS_DIR / "similarity.pkl"

ASSETS_DIR: Path = APP_DIR / "assets"
STYLES_DIR: Path = APP_DIR / "styles"
THEME_CSS: Path = STYLES_DIR / "theme.css"
BANNER_SVG: Path = ASSETS_DIR / "banner.svg"

I18N_DIR: Path = APP_DIR / "i18n"
LOCALES_DIR: Path = I18N_DIR / "locales"

DATABASE_DIR: Path = ROOT_DIR / "database"
DATABASE_PATH: Path = DATABASE_DIR / "cinematch.db"

# ---------------------------------------------------------------------------
# TMDB API (poster artwork + trailers)
# ---------------------------------------------------------------------------
# Get a free key at https://www.themoviedb.org/settings/api and put it in a
# local .env file as TMDB_API_KEY=xxxxxxxx  (see .env.example).
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"
TMDB_REQUEST_TIMEOUT: int = 6  # seconds

PLACEHOLDER_POSTER_URL: str = "https://placehold.co/500x750/151821/8B5CF6?text=No+Poster"
YOUTUBE_SEARCH_BASE_URL: str = "https://www.youtube.com/results?search_query="

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
APP_NAME: str = "CineMatch AI"
APP_TAGLINE: str = "Movies, matched to your taste."
DEVELOPER_NAME: str = "Prajwal"
GITHUB_URL: str = "https://github.com/prajwal972"
LINKEDIN_URL: str = "https://www.linkedin.com/in/prajwal972"

DEFAULT_TOP_N: int = 10
TRENDING_VOTE_COUNT_THRESHOLD: int = 200  # min votes to qualify for "Trending"/"Top Rated"

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
MIN_PASSWORD_LENGTH: int = 8
BCRYPT_ROUNDS: int = 12
SESSION_COOKIE_NAME: str = "cinematch_session"

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
DEFAULT_LANGUAGE: str = "en"
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "mr": "मराठी",
    "es": "Español",
    "ja": "日本語",
}

# ---------------------------------------------------------------------------
# Theme (kept in sync with styles/theme.css — used by Plotly figures so
# charts match the app's dark/glass aesthetic instead of default styling)
# ---------------------------------------------------------------------------
THEME = {
    "bg": "#0A0C12",
    "surface": "#13161F",
    "surface_alt": "#191D29",
    "border": "#262B38",
    "text": "#ECEEF2",
    "text_muted": "#9AA1B1",
    "accent_violet": "#8B5CF6",
    "accent_cyan": "#22D3EE",
    "accent_amber": "#FBBF24",
    "accent_rose": "#FB7185",
    "gradient": "linear-gradient(135deg, #8B5CF6 0%, #22D3EE 100%)",
}

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_COLORWAY = [
    THEME["accent_violet"], THEME["accent_cyan"], THEME["accent_amber"],
    THEME["accent_rose"], "#34D399", "#F472B6",
]
