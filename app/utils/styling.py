"""CSS injection helper."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st

logger = logging.getLogger("cinematch")


def load_css(css_path: Path) -> None:
    """Inject the app's stylesheet into the current page."""
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        logger.warning("Stylesheet not found at %s — using default Streamlit theme.", css_path)
