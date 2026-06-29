"""
Reusable movie card component.

Accepts either a `services.recommendation_service.Recommendation` or a
pandas Series (the shape returned by MovieRecommender.get_trending() /
get_top_rated() / etc.) — both get normalized to a plain dict internally so
the rendering code below doesn't care which one it got.
"""

from __future__ import annotations

from typing import Any, Optional, Union

import pandas as pd
import streamlit as st

from database import models as db
from i18n.translator import t
from services.recommendation_service import Recommendation
from services.tmdb_service import fetch_poster
from utils.formatting import format_rating, format_runtime, format_year
from utils.session import current_user_id, is_authenticated, queue_movie_details_bridge


def _normalize(movie: Union[Recommendation, pd.Series, dict]) -> dict:
    if isinstance(movie, Recommendation):
        return {
            "movie_id": movie.movie_id, "title": movie.title, "genres": movie.genres,
            "release_year": movie.release_year, "vote_average": movie.vote_average,
            "popularity": movie.popularity, "runtime": movie.runtime,
            "overview": movie.overview, "similarity_score": movie.similarity_score,
        }
    if isinstance(movie, pd.Series):
        d = movie.to_dict()
        d.setdefault("similarity_score", None)
        return d
    return movie


def render_movie_card(
    movie: Union[Recommendation, pd.Series, dict],
    *,
    key_prefix: str,
    show_match_score: bool = False,
    compact: bool = False,
) -> None:
    """Render one movie card. ``key_prefix`` must be unique per card on the
    page (e.g. f"trending_{movie_id}") since several cards render the same
    widgets."""
    m = _normalize(movie)
    movie_id = int(m["movie_id"])

    st.markdown('<div class="cm-movie-card cm-fade-in">', unsafe_allow_html=True)
    st.image(fetch_poster(movie_id), width="stretch")

    st.markdown('<div class="cm-movie-card-body">', unsafe_allow_html=True)
    st.markdown(f'<div class="cm-movie-title">{m["title"]}</div>', unsafe_allow_html=True)

    genres = m.get("genres") or []
    meta_bits = [format_year(m.get("release_year"))]
    if m.get("runtime"):
        meta_bits.append(format_runtime(m["runtime"]))
    st.markdown(f'<div class="cm-movie-meta">{" · ".join(meta_bits)}</div>', unsafe_allow_html=True)

    if genres:
        chips = "".join(f'<span class="cm-genre-chip">{g}</span>' for g in genres[:3])
        st.markdown(chips, unsafe_allow_html=True)

    if not compact and m.get("overview"):
        st.markdown(f'<div class="cm-movie-overview">{m["overview"]}</div>', unsafe_allow_html=True)

    badge_bits = [
        f'<span class="cm-badge amber">{format_rating(m.get("vote_average"))}</span>',
    ]
    if show_match_score and m.get("similarity_score") is not None:
        badge_bits.append(
            f'<span class="cm-badge">{t("movie_card.match_score")} {m["similarity_score"]:.0f}%</span>'
        )
    st.markdown(" ".join(badge_bits), unsafe_allow_html=True)
    st.write("")

    _render_actions(movie_id, m["title"], key_prefix)

    st.markdown("</div></div>", unsafe_allow_html=True)


def _render_actions(movie_id: int, title: str, key_prefix: str) -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="cm-icon-btn cm-btn-outline">', unsafe_allow_html=True)
        if st.button(t("common.view_details"), key=f"{key_prefix}_details", width="stretch"):
            queue_movie_details_bridge(title)
            st.switch_page("pages/1_Recommendations.py")
        st.markdown("</div>", unsafe_allow_html=True)

    if is_authenticated():
        user_id = current_user_id()
        is_fav = db.is_favorite(user_id, movie_id)
        is_watch = db.is_in_watchlist(user_id, movie_id)

        with col2:
            fav_label = t("common.remove_from_favorites") if is_fav else t("common.add_to_favorites")
            active_class = "active" if is_fav else ""
            st.markdown(f'<div class="cm-icon-btn {active_class}">', unsafe_allow_html=True)
            if st.button(fav_label, key=f"{key_prefix}_fav", width="stretch"):
                if is_fav:
                    db.remove_favorite(user_id, movie_id)
                else:
                    db.add_favorite(user_id, movie_id, title)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            watch_label = t("common.remove_from_watchlist") if is_watch else t("common.add_to_watchlist")
            active_class = "active" if is_watch else ""
            st.markdown(f'<div class="cm-icon-btn {active_class}">', unsafe_allow_html=True)
            if st.button(watch_label, key=f"{key_prefix}_watch", width="stretch"):
                if is_watch:
                    db.remove_from_watchlist(user_id, movie_id)
                else:
                    db.add_to_watchlist(user_id, movie_id, title)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        with col2:
            st.markdown('<div class="cm-icon-btn cm-btn-outline">', unsafe_allow_html=True)
            if st.button(t("common.add_to_favorites"), key=f"{key_prefix}_fav_guest", width="stretch"):
                st.toast(t("common.sign_in_to_continue"))
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="cm-icon-btn cm-btn-outline">', unsafe_allow_html=True)
            if st.button(t("common.add_to_watchlist"), key=f"{key_prefix}_watch_guest", width="stretch"):
                st.toast(t("common.sign_in_to_continue"))
            st.markdown("</div>", unsafe_allow_html=True)
