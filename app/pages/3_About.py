"""CineMatch AI — About page (minimal, user-facing only).

Deliberately does NOT include architecture diagrams, dataset/model
internals, tech stack, or developer notes — those belong in the GitHub
README per the product brief's "Remove from Frontend" rule, not in the
product UI.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from i18n.translator import t
from utils.session import init_session_state

init_session_state()

st.markdown(
    f"""
    <div class="cm-hero cm-fade-in" style="padding:1.8rem 2rem;">
        <div class="cm-hero-title" style="font-size:1.9rem;">{t('about.title')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="cm-card">{t("about.body")}</div>', unsafe_allow_html=True)
st.write("")
st.markdown(f"**{t('about.contact')}**")
st.markdown("[GitHub](https://github.com/prajwal972) · [LinkedIn](https://www.linkedin.com/in/prajwal972)")
