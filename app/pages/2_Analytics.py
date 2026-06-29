"""CineMatch AI — Analytics page."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config.settings as config
from i18n.translator import t
from services.recommendation_service import load_recommender
from utils.session import init_session_state

init_session_state()


@st.cache_resource(show_spinner=False)
def get_recommender():
    return load_recommender()


try:
    recommender = get_recommender()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

movies = recommender.movies

st.markdown(
    f"""
    <div class="cm-hero cm-fade-in" style="padding:1.8rem 2rem;">
        <div class="cm-hero-title" style="font-size:1.9rem;">{t('nav.analytics')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

px.defaults.template = config.PLOTLY_TEMPLATE
px.defaults.color_discrete_sequence = config.PLOTLY_COLORWAY
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color=config.THEME["text"], margin=dict(t=50, l=10, r=10, b=10),
)

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">Filters</div>', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
with f1:
    year_min, year_max = int(movies["release_year"].min()), int(movies["release_year"].max())
    year_range = st.slider("Release year", year_min, year_max, (max(year_min, 1990), year_max))
with f2:
    genre_filter = st.multiselect("Genres", options=recommender.all_genres(), default=[])
with f3:
    min_votes = st.slider("Minimum vote count", 0, 2000, 0, step=50)

filtered = movies[
    (movies["release_year"] >= year_range[0]) & (movies["release_year"] <= year_range[1])
    & (movies["vote_count"] >= min_votes)
]
if genre_filter:
    filtered = filtered[filtered["genres"].apply(lambda g: any(genre in g for genre in genre_filter))]

st.caption(f"{len(filtered):,} of {len(movies):,} movies match the current filters.")

# ---------------------------------------------------------------------------
# Genre analysis
# ---------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">Genre analysis</div>', unsafe_allow_html=True)
genre_counts = Counter(g for sub in filtered["genres"] for g in sub)
gcol1, gcol2 = st.columns([1.3, 1])
with gcol1:
    if genre_counts:
        top = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        fig = px.bar(
            x=[c for _, c in top], y=[g for g, _ in top], orientation="h",
            labels={"x": "Movies", "y": ""}, title="Movies per genre",
        )
        fig.update_layout(**PLOT_LAYOUT, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")
    else:
        st.markdown('<div class="cm-empty">No movies match the current filters.</div>', unsafe_allow_html=True)
with gcol2:
    if genre_counts:
        top8 = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        fig = px.pie(values=[c for _, c in top8], names=[g for g, _ in top8], title="Top-8 genre share", hole=0.45)
        fig.update_layout(**PLOT_LAYOUT)
        st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Movie trend analysis
# ---------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">Release trend</div>', unsafe_allow_html=True)
yearly = filtered.groupby("release_year").size().reset_index(name="count")
fig = px.area(yearly, x="release_year", y="count", labels={"release_year": "Year", "count": "Movies released"},
               title="Movies released per year")
fig.update_traces(line_color=config.THEME["accent_violet"])
fig.update_layout(**PLOT_LAYOUT)
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Ratings analysis + popular movies
# ---------------------------------------------------------------------------
rcol1, rcol2 = st.columns(2)
with rcol1:
    st.markdown('<div class="cm-section-title">Ratings distribution</div>', unsafe_allow_html=True)
    fig = px.histogram(filtered, x="vote_average", nbins=25, title="Vote average distribution",
                        labels={"vote_average": "Vote average"})
    fig.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig, width="stretch")
with rcol2:
    st.markdown('<div class="cm-section-title">Most popular movies</div>', unsafe_allow_html=True)
    top_pop = filtered.nlargest(10, "popularity")[["title", "popularity"]].iloc[::-1]
    fig = px.bar(top_pop, x="popularity", y="title", orientation="h", title="Top 10 by popularity score")
    fig.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">Runtime distribution</div>', unsafe_allow_html=True)
runtime = filtered[(filtered["runtime"] > 0) & (filtered["runtime"] < 240)]["runtime"]
fig = px.histogram(runtime, nbins=40, labels={"value": "Runtime (minutes)"}, title="Runtime distribution")
fig.update_layout(**PLOT_LAYOUT, showlegend=False)
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Similarity distribution (model behaviour)
# ---------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">Similarity score distribution</div>', unsafe_allow_html=True)
st.caption("A random sample of pairwise similarity scores across the full catalogue.")
rng = np.random.default_rng(42)
sample_idx = rng.integers(0, recommender.similarity.shape[0], size=2000)
sample_scores = recommender.similarity[sample_idx, rng.integers(0, recommender.similarity.shape[0], size=2000)] * 100
fig = px.histogram(sample_scores, nbins=40, labels={"value": "Similarity score (%)"},
                    title="Distribution of pairwise similarity scores (2,000-pair sample)")
fig.update_layout(**PLOT_LAYOUT, showlegend=False)
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Session-level recommendation & search analytics
# ---------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">Your session analytics</div>', unsafe_allow_html=True)
scol1, scol2, scol3 = st.columns(3)
with scol1:
    st.markdown(
        f"""<div class="cm-kpi"><div class="cm-kpi-value">{st.session_state.get('search_count', 0)}</div>
        <div class="cm-kpi-label">Searches this session</div></div>""", unsafe_allow_html=True)
with scol2:
    st.markdown(
        f"""<div class="cm-kpi"><div class="cm-kpi-value">{st.session_state.get('recommendation_count', 0)}</div>
        <div class="cm-kpi-label">Recommendation runs</div></div>""", unsafe_allow_html=True)
with scol3:
    st.markdown(
        f"""<div class="cm-kpi"><div class="cm-kpi-value">{len(st.session_state.get('recently_viewed', []))}</div>
        <div class="cm-kpi-label">Distinct movies viewed</div></div>""", unsafe_allow_html=True)
