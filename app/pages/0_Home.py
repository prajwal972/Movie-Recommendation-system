"""CineMatch AI — Home page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from components.movie_card import render_movie_card
from i18n.translator import t
from services.recommendation_service import load_recommender
from utils.session import init_session_state, queue_movie_details_bridge

init_session_state()


@st.cache_resource(show_spinner=False)
def get_recommender():
    return load_recommender()


try:
    recommender = get_recommender()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

# ---------------------------------------------------------------------------
# Hero + search
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="cm-hero cm-fade-in">
        <div class="cm-hero-title">{t('home.hero_title')}</div>
        <div class="cm-hero-sub">{t('home.hero_subtitle')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

search_col, btn_col = st.columns([5, 1])
with search_col:
    query = st.text_input(
        t("common.search_placeholder"), placeholder=t("common.search_placeholder"),
        label_visibility="collapsed", key="home_search_query",
    )
with btn_col:
    go = st.button(t("common.submit"), width="stretch")

if query:
    suggestions = recommender.search_movie(query, limit=6)
    if suggestions:
        sug_cols = st.columns(len(suggestions))
        for i, s in enumerate(suggestions):
            with sug_cols[i]:
                if st.button(s, key=f"home_sugg_{i}", width="stretch"):
                    queue_movie_details_bridge(s)
                    st.switch_page("pages/1_Recommendations.py")
    if go and suggestions:
        queue_movie_details_bridge(suggestions[0])
        st.switch_page("pages/1_Recommendations.py")


def render_row(title_key: str, data, key_prefix: str) -> None:
    st.markdown(f'<div class="cm-section-title">{t(title_key)}</div>', unsafe_allow_html=True)
    if data.empty:
        st.markdown('<div class="cm-empty">—</div>', unsafe_allow_html=True)
        return
    cols = st.columns(5)
    for i, (_, row) in enumerate(data.iterrows()):
        with cols[i % 5]:
            render_movie_card(row, key_prefix=f"{key_prefix}_{int(row['movie_id'])}", compact=True)


# ---------------------------------------------------------------------------
# Featured — blended popularity + rating, distinct from the pure-popularity
# Trending row below
# ---------------------------------------------------------------------------
featured = recommender.movies.copy()
featured["_blend"] = (
    featured["popularity"].rank(pct=True) * 0.5 + featured["vote_average"].rank(pct=True) * 0.5
)
featured = featured.nlargest(5, "_blend")[recommender._CARD_COLUMNS]
render_row("home.featured", featured, "featured")

render_row("home.trending_today", recommender.get_trending(10), "trending")
render_row("home.top_rated", recommender.get_top_rated(10), "toprated")
render_row("home.recently_released", recommender.get_recently_released(10), "recent")

# ---------------------------------------------------------------------------
# Genre carousel
# ---------------------------------------------------------------------------
st.markdown(f'<div class="cm-section-title">{t("home.browse_by_genre")}</div>', unsafe_allow_html=True)
genres = recommender.all_genres()
selected_genre = st.selectbox("genre", options=genres, index=genres.index("Action") if "Action" in genres else 0,
                               label_visibility="collapsed", key="home_genre_select")
genre_movies = recommender.get_by_genre(selected_genre, 10)
cols = st.columns(5)
for i, (_, row) in enumerate(genre_movies.iterrows()):
    with cols[i % 5]:
        render_movie_card(row, key_prefix=f"genre_{int(row['movie_id'])}", compact=True)

# ---------------------------------------------------------------------------
# Recent searches
# ---------------------------------------------------------------------------
history = st.session_state.get("search_history", [])
if history:
    st.markdown(f'<div class="cm-section-title">{t("home.your_recent_searches")}</div>', unsafe_allow_html=True)
    st.markdown(
        " ".join(f'<span class="cm-badge">{h}</span>' for h in history[:10]),
        unsafe_allow_html=True,
    )
