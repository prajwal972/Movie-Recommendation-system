"""
Reusable NLP preprocessing pipeline.

This module is the single source of truth for text cleaning logic used both
offline (notebooks/03_Feature_Engineering.ipynb, when building the `tags`
column) and online (the Streamlit app, when normalizing free-text input).
Keeping one implementation in one place guarantees the two never drift apart.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

_NLTK_RESOURCES = ("stopwords", "punkt")


def _ensure_nltk_data() -> None:
    """Download required NLTK corpora on first use, silently, if missing."""
    for resource in _NLTK_RESOURCES:
        try:
            nltk.data.find(
                f"corpora/{resource}" if resource == "stopwords" else f"tokenizers/{resource}"
            )
        except LookupError:
            nltk.download(resource, quiet=True)


_ensure_nltk_data()

_STOPWORDS = set(stopwords.words("english"))
_STEMMER = PorterStemmer()
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")


def collapse_name(name: str) -> str:
    """Collapse a multi-word proper noun into one token.

    'Sam Worthington' -> 'samworthington'

    This stops the vectorizer from treating a person's first and last name
    as two generic, unrelated word features.
    """
    return name.replace(" ", "").lower().strip()


def clean_text(text: str) -> str:
    """Lowercase and strip everything except letters, digits, and spaces."""
    text = text.lower()
    return _NON_ALNUM_RE.sub(" ", text)


def tokenize(text: str) -> List[str]:
    """Whitespace tokenization (sufficient for already-cleaned text)."""
    return text.split()


def remove_stopwords(tokens: List[str], min_len: int = 2) -> List[str]:
    """Drop English stopwords and tokens shorter than ``min_len``."""
    return [t for t in tokens if t not in _STOPWORDS and len(t) >= min_len]


def stem_tokens(tokens: List[str]) -> List[str]:
    """Apply Porter stemming to every token."""
    return [_STEMMER.stem(t) for t in tokens]


@lru_cache(maxsize=4096)
def clean_and_stem(text: str) -> str:
    """Full pipeline: clean -> tokenize -> remove stopwords -> stem.

    Cached because the same query strings (e.g. genre names typed into a
    filter) get re-cleaned often during a single Streamlit session.
    """
    tokens = tokenize(clean_text(text))
    tokens = remove_stopwords(tokens)
    tokens = stem_tokens(tokens)
    return " ".join(tokens)


def build_tags(
    overview: str,
    genres: List[str],
    keywords: List[str],
    cast: List[str],
    director: str,
) -> str:
    """Combine all content fields for one movie into a single cleaned tag string.

    Mirrors the exact logic used in notebooks/03_Feature_Engineering.ipynb so
    a tag computed here and a tag computed in the notebook are identical for
    the same inputs.
    """
    parts: List[str] = []
    parts.extend(str(overview).split())
    parts.extend(collapse_name(g) for g in genres)
    parts.extend(collapse_name(k) for k in keywords)
    parts.extend(collapse_name(c) for c in cast)
    if director:
        parts.append(collapse_name(director))

    raw_tag_string = " ".join(parts)
    return clean_and_stem(raw_tag_string)
