"""CineMatch AI — Settings page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config.settings as config
from database.models import get_preferred_genres, get_user_by_identifier, set_language, set_preferred_genres
from i18n.translator import set_current_language, t
from services.recommendation_service import load_recommender
from utils.session import current_user_id, current_username, init_session_state, is_authenticated, logout_session

init_session_state()

if not is_authenticated():
    st.markdown(f'<div class="cm-empty">{t("common.sign_in_to_continue")}</div>', unsafe_allow_html=True)
    st.page_link("pages/4_Login.py", label=t("nav.login"))
    st.stop()


@st.cache_resource(show_spinner=False)
def get_recommender():
    return load_recommender()


user_id = current_user_id()
user = get_user_by_identifier(current_username())

st.markdown(f'<div class="cm-section-title">{t("settings.title")}</div>', unsafe_allow_html=True)

st.markdown('<div class="cm-card">', unsafe_allow_html=True)
st.markdown(f"**{t('settings.profile')}**")
st.markdown(f"{t('auth.username')}: {user.username}")
st.markdown(f"{t('auth.email')}: {user.email}")
st.markdown(f"{t('settings.account_created')}: {user.created_at[:10]}")
st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="cm-card">', unsafe_allow_html=True)
st.markdown(f"**{t('settings.language')}**")
lang_codes = list(config.SUPPORTED_LANGUAGES.keys())
lang_labels = list(config.SUPPORTED_LANGUAGES.values())
current_idx = lang_codes.index(st.session_state.get("language", config.DEFAULT_LANGUAGE))
chosen_label = st.selectbox(t("settings.language"), options=lang_labels, index=current_idx, label_visibility="collapsed")
chosen_code = lang_codes[lang_labels.index(chosen_label)]

st.markdown(f"**{t('settings.preferred_genres')}**")
try:
    recommender = get_recommender()
    all_genres = recommender.all_genres()
except FileNotFoundError:
    all_genres = []
saved_genres = get_preferred_genres(user_id)
chosen_genres = st.multiselect(
    t("settings.preferred_genres"), options=all_genres, default=[g for g in saved_genres if g in all_genres],
    label_visibility="collapsed",
)

if st.button(t("settings.save_changes")):
    set_language(user_id, chosen_code)
    set_preferred_genres(user_id, chosen_genres)
    set_current_language(chosen_code)
    st.session_state["language"] = chosen_code
    st.success(t("settings.changes_saved"))
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

st.write("")
if st.button(t("nav.logout")):
    logout_session()
    st.switch_page("pages/0_Home.py")
