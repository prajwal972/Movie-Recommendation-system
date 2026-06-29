"""
Production recommendation engine.

Wraps the pickled movie table + cosine similarity matrix produced by
notebooks/04_Model_Building.ipynb behind a small, typed, testable API that
the Streamlit app (and any other future client — a FastAPI service, a CLI,
etc.) can call without knowing anything about pandas or pickle internals.
"""

from __future__ import annotations

import logging
import pickle
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

import config.settings as config

logger = logging.getLogger("cinematch")


@dataclass
class Recommendation:
    """A single recommended movie, ready for the UI to render."""

    movie_id: int
    title: str
    similarity_score: float  # 0-100
    genres: List[str]
    cast: List[str]
    director: str
    vote_average: float
    vote_count: int
    popularity: float
    runtime: Optional[float]
    release_year: Optional[int]
    overview: str


@dataclass
class RecommendationResult:
    """Everything one /recommend call returns, plus timing for the UI."""

    query_title: str
    recommendations: List[Recommendation] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class MovieNotFoundError(Exception):
    """Raised when an exact title lookup fails (callers should fuzzy-search first)."""


class MovieRecommender:
    """Loads the pickled model artifacts once and serves recommendations."""

    def __init__(
        self,
        movies_path: Path = config.MOVIES_PKL,
        similarity_path: Path = config.SIMILARITY_PKL,
    ) -> None:
        self.movies: pd.DataFrame = self._load_pickle(movies_path)
        self.similarity: np.ndarray = self._load_pickle(similarity_path)

        if len(self.movies) != self.similarity.shape[0]:
            raise ValueError(
                f"movies.pkl ({len(self.movies)} rows) and similarity.pkl "
                f"({self.similarity.shape[0]} rows) are out of sync. Re-run "
                f"notebooks/04_Model_Building.ipynb."
            )

        self._title_index = {
            title.lower(): idx for idx, title in enumerate(self.movies["title"])
        }
        self._all_titles: List[str] = self.movies["title"].tolist()
        logger.info("Loaded %d movies and a %s similarity matrix.", len(self.movies), self.similarity.shape)

    @staticmethod
    def _load_pickle(path: Path):
        if not path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {path}. Run all four notebooks in "
                f"notebooks/ in order (01 -> 04) to generate it, or download the "
                f"pre-built models/ folder from the project README."
            )
        with open(path, "rb") as f:
            return pickle.load(f)

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------
    def _index_for_title(self, title: str) -> int:
        idx = self._title_index.get(title.lower())
        if idx is None:
            raise MovieNotFoundError(f"'{title}' was not found in the dataset.")
        return idx

    def movie_exists(self, title: str) -> bool:
        return title.lower() in self._title_index

    def search_movie(self, query: str, limit: int = 8, score_cutoff: int = 50) -> List[str]:
        """Fuzzy-match ``query`` against all titles. Powers search suggestions."""
        if not query or not query.strip():
            return []
        matches = process.extract(
            query, self._all_titles, scorer=fuzz.token_sort_ratio, limit=limit, score_cutoff=score_cutoff,
        )
        return [title for title, _score, _idx in matches]

    def best_match(self, query: str) -> Optional[str]:
        """Single best fuzzy title match, or None if nothing is close enough.

        Uses a stricter cutoff than ``search_movie`` since this result is
        auto-selected (no human confirms it), e.g. as the recommend() fallback
        for a slightly misspelled title.
        """
        matches = self.search_movie(query, limit=1, score_cutoff=65)
        return matches[0] if matches else None

    # ------------------------------------------------------------------
    # Core recommendation logic
    # ------------------------------------------------------------------
    def _row_to_recommendation(self, row_idx: int, score: float) -> Recommendation:
        row = self.movies.iloc[row_idx]
        return Recommendation(
            movie_id=int(row["movie_id"]),
            title=row["title"],
            similarity_score=round(float(score) * 100, 1),
            genres=list(row["genres"]),
            cast=list(row["cast"]),
            director=row["director"] or "Unknown",
            vote_average=float(row["vote_average"]),
            vote_count=int(row["vote_count"]),
            popularity=float(row["popularity"]),
            runtime=float(row["runtime"]) if pd.notna(row["runtime"]) else None,
            release_year=int(row["release_year"]) if pd.notna(row["release_year"]) else None,
            overview=row["overview"],
        )

    def recommend(self, movie_title: str, top_n: int = config.DEFAULT_TOP_N) -> RecommendationResult:
        """Return the top-N most similar movies to ``movie_title``.

        Handles invalid movie names gracefully: if there's no exact match, it
        falls back to the closest fuzzy match instead of raising.
        """
        start = time.perf_counter()

        if not movie_title or not movie_title.strip():
            return RecommendationResult(query_title=movie_title, error="Please enter a movie title.")

        try:
            idx = self._index_for_title(movie_title)
            resolved_title = movie_title
        except MovieNotFoundError:
            fallback = self.best_match(movie_title)
            if fallback is None:
                return RecommendationResult(
                    query_title=movie_title,
                    error=f"No movie matching '{movie_title}' was found in the dataset.",
                )
            idx = self._index_for_title(fallback)
            resolved_title = fallback

        scores = list(enumerate(self.similarity[idx]))
        scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = [s for s in scores if s[0] != idx][:top_n]

        recommendations = [self._row_to_recommendation(i, score) for i, score in top_matches]
        elapsed = time.perf_counter() - start

        return RecommendationResult(
            query_title=resolved_title,
            recommendations=recommendations,
            elapsed_seconds=elapsed,
        )

    def get_similarity_score(self, title_a: str, title_b: str) -> Optional[float]:
        """Pairwise similarity (0-100) between two movies already in the dataset."""
        try:
            idx_a, idx_b = self._index_for_title(title_a), self._index_for_title(title_b)
        except MovieNotFoundError:
            return None
        return round(float(self.similarity[idx_a, idx_b]) * 100, 1)

    def get_movie_details(self, title: str) -> Optional[Recommendation]:
        try:
            idx = self._index_for_title(title)
        except MovieNotFoundError:
            return None
        return self._row_to_recommendation(idx, score=1.0)

    # ------------------------------------------------------------------
    # Home-page / analytics helpers
    # ------------------------------------------------------------------
    _CARD_COLUMNS = [
        "movie_id", "title", "release_year", "vote_average", "vote_count",
        "popularity", "genres", "runtime", "overview",
    ]

    def get_trending(self, n: int = 10) -> pd.DataFrame:
        """Top movies by TMDB popularity score."""
        return self.movies.nlargest(n, "popularity")[self._CARD_COLUMNS]

    def get_top_rated(self, n: int = 10, min_votes: int = config.TRENDING_VOTE_COUNT_THRESHOLD) -> pd.DataFrame:
        """Top-rated movies, restricted to a minimum vote count to avoid noisy outliers."""
        qualified = self.movies[self.movies["vote_count"] >= min_votes]
        return qualified.nlargest(n, "vote_average")[self._CARD_COLUMNS]

    def get_recently_released(self, n: int = 10, min_votes: int = 20) -> pd.DataFrame:
        """Newest releases in the dataset (it's a 2017 snapshot, so 'recent'
        is relative to the data, not to today — see README)."""
        qualified = self.movies[self.movies["vote_count"] >= min_votes]
        return qualified.nlargest(n, "release_year")[self._CARD_COLUMNS]

    def get_by_genre(self, genre: str, n: int = 10) -> pd.DataFrame:
        subset = self.movies[self.movies["genres"].apply(lambda g: genre in g)]
        return subset.nlargest(n, "popularity")[self._CARD_COLUMNS]

    def get_by_movie_id(self, movie_id: int) -> Optional[Recommendation]:
        matches = self.movies.index[self.movies["movie_id"] == movie_id]
        if len(matches) == 0:
            return None
        return self._row_to_recommendation(matches[0], score=1.0)

    def all_genres(self) -> List[str]:
        genres = {g for sub in self.movies["genres"] for g in sub}
        return sorted(genres)

    def all_actors(self) -> set:
        return {a for sub in self.movies["cast"] for a in sub}

    def all_directors(self) -> set:
        return {d for d in self.movies["director"] if d}


def load_recommender() -> MovieRecommender:
    """Convenience factory — the only entry point most callers need."""
    return MovieRecommender()
