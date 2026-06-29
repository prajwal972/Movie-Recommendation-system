"""
Minimal i18n: load each locale's JSON once, look up dotted keys
("auth.login_title"), fall back to English then to the raw key if a
translation is ever missing.

Translation accuracy note: the Hindi, Marathi, Spanish, and Japanese strings
were translated directly (no machine-translation API was available in the
build environment). They cover short, common UI vocabulary and should be
fine for a portfolio/demo, but get a native speaker to proofread them —
especially Hindi/Marathi/Japanese — before treating this as production-grade
localization for real users.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict

import streamlit as st

import config.settings as config


@lru_cache(maxsize=None)
def _load_locale(language: str) -> Dict[str, Any]:
    path = config.LOCALES_DIR / f"{language}.json"
    if not path.exists():
        path = config.LOCALES_DIR / f"{config.DEFAULT_LANGUAGE}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _lookup(data: Dict[str, Any], dotted_key: str) -> str | None:
    node: Any = data
    for part in dotted_key.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node if isinstance(node, str) else None


def current_language() -> str:
    return st.session_state.get("language", config.DEFAULT_LANGUAGE)


def set_current_language(language: str) -> None:
    if language in config.SUPPORTED_LANGUAGES:
        st.session_state["language"] = language


def t(dotted_key: str, **kwargs) -> str:
    """Translate ``dotted_key`` into the current session language.

    Falls back to English, then to the raw key, so a missing translation
    never crashes the UI — it just shows slightly wrong text, which is easy
    to spot and fix.
    """
    language = current_language()
    value = _lookup(_load_locale(language), dotted_key)
    if value is None and language != config.DEFAULT_LANGUAGE:
        value = _lookup(_load_locale(config.DEFAULT_LANGUAGE), dotted_key)
    if value is None:
        value = dotted_key

    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError):
            return value
    return value
