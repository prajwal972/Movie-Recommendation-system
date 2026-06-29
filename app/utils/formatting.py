"""Display formatting helpers — pure functions, no Streamlit dependency."""

from __future__ import annotations

from typing import Optional


def format_runtime(minutes: Optional[float]) -> str:
    """e.g. 142.0 -> '2h 22m'"""
    if not minutes or minutes <= 0:
        return "Unknown"
    minutes = int(minutes)
    hours, remainder = divmod(minutes, 60)
    return f"{hours}h {remainder}m" if hours else f"{remainder}m"


def format_year(year: Optional[float]) -> str:
    if year is None:
        return "—"
    try:
        return str(int(year))
    except (ValueError, TypeError):
        return "—"


def format_rating(vote_average: Optional[float]) -> str:
    if vote_average is None:
        return "N/A"
    return f"{vote_average:.1f} / 10"


def confidence_label(similarity_pct: float) -> str:
    """Human-readable confidence band for a similarity percentage."""
    if similarity_pct >= 40:
        return "Very strong match"
    if similarity_pct >= 25:
        return "Strong match"
    if similarity_pct >= 12:
        return "Moderate match"
    return "Loose match"
