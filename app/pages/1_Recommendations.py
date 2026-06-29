"""CineMatch AI — Recommendations page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.movie_card import render_movie_card
from i18n.translator import t
from services.recommendation_service import load_recommender
from utils.session import (
    add_to_recently_viewed, add_to_search_history, current_user_id, increment_recommendation_count,
    init_session_state, is_authenticated,
)
from database.models import add_history

init_session_state()


@st.cache_resource(show_spinner=False)
def get_recommender():
    return load_recommender()


try:
    recommender = get_recommender()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

st.markdown(
    f"""
    <div class="cm-hero cm-fade-in" style="padding:1.8rem 2rem;">
        <div class="cm-hero-title" style="font-size:1.9rem;">{t('nav.recommendations')}</div>
        <div class="cm-hero-sub">{t('home.hero_subtitle')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Search box with live fuzzy suggestions
# ---------------------------------------------------------------------------
# Bridge from a "View Details" click elsewhere in the app — must set the
# session_state value BEFORE the widget below is instantiated; Streamlit
# does not allow writing to a widget's key after it's created in the same run.
bridge_triggered = False
if st.session_state.get("auto_recommend") and st.session_state.get("prefill_movie"):
    st.session_state["rec_search_box"] = st.session_state["prefill_movie"]
    bridge_triggered = True
    st.session_state["auto_recommend"] = False
    st.session_state["prefill_movie"] = None

# ---------------------------------------------------------------------------
# Search box with live fuzzy suggestions
# ---------------------------------------------------------------------------
search_col, button_col, n_col = st.columns([3, 1, 1])

with search_col:
    query = st.text_input(
        t("common.search_placeholder"), placeholder=t("common.search_placeholder"),
        label_visibility="collapsed", key="rec_search_box",
    )
with n_col:
    top_n = st.selectbox("Results", options=[5, 10, 15, 20], index=1, label_visibility="collapsed")
with button_col:
    recommend_clicked = st.button(t("common.submit"), width="stretch")

if bridge_triggered:
    recommend_clicked = True

selected_title = query

if query and not recommend_clicked:
    suggestions = recommender.search_movie(query, limit=6)
    if suggestions and query not in suggestions:
        sug_cols = st.columns(len(suggestions))
        for i, s in enumerate(suggestions):
            with sug_cols[i]:
                if st.button(s, key=f"sugg_{i}", width="stretch"):
                    selected_title = s
                    recommend_clicked = True

# ---------------------------------------------------------------------------
# Run recommendation
# ---------------------------------------------------------------------------
if recommend_clicked and selected_title:
    with st.spinner(t("common.loading")):
        result = recommender.recommend(selected_title, top_n=top_n)

    if not result.ok:
        st.markdown(f'<div class="cm-empty">{result.error}</div>', unsafe_allow_html=True)
    else:
        add_to_search_history(result.query_title)
        add_to_recently_viewed(result.query_title)
        increment_recommendation_count()

        query_details = recommender.get_movie_details(result.query_title)
        if is_authenticated() and query_details:
            add_history(current_user_id(), query_details.movie_id, query_details.title)

        st.success(t("common.showing_results_for", title=result.query_title))

        if query_details:
            with st.expander(result.query_title, expanded=False):
                qc1, qc2 = st.columns([1, 4])
                with qc1:
                    from services.tmdb_service import fetch_poster
                    st.image(fetch_poster(query_details.movie_id), width="stretch")
                with qc2:
                    st.markdown(f"**{', '.join(query_details.genres) or '—'}**")
                    st.markdown(f"{query_details.director}")
                    st.markdown(f"{', '.join(query_details.cast) or '—'}")
                    st.markdown(query_details.overview)

        st.markdown(f'<div class="cm-section-title">{t("nav.recommendations")}</div>', unsafe_allow_html=True)
        cols = st.columns(5)
        for i, rec in enumerate(result.recommendations):
            with cols[i % 5]:
                render_movie_card(rec, key_prefix=f"rec_{rec.movie_id}", show_match_score=True)
elif recommend_clicked and not selected_title:
    st.markdown('<div class="cm-empty">—</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Recently viewed
# ---------------------------------------------------------------------------
recently_viewed = st.session_state.get("recently_viewed", [])
if recently_viewed:
    st.markdown('<div class="cm-section-title">' + t("home.your_recent_searches") + '</div>', unsafe_allow_html=True)
    st.markdown(
        " ".join(f'<span class="cm-badge cyan">{title}</span>' for title in recently_viewed),
        unsafe_allow_html=True,
    )
