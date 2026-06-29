"""CineMatch AI — Login page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from i18n.translator import t
from services.auth_service import login_user
from utils.session import init_session_state, is_authenticated, login_session

init_session_state()

if is_authenticated():
    st.switch_page("pages/0_Home.py")

st.markdown('<div class="cm-auth-wrapper cm-fade-in">', unsafe_allow_html=True)
st.markdown('<div class="cm-auth-card">', unsafe_allow_html=True)
st.markdown(f'<div class="cm-auth-title">{t("auth.login_title")}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="cm-auth-subtitle">{t("auth.login_subtitle")}</div>', unsafe_allow_html=True)

with st.form("login_form"):
    identifier = st.text_input(t("auth.username"))
    password = st.text_input(t("auth.password"), type="password")
    submitted = st.form_submit_button(t("auth.login_button"), width="stretch")

if submitted:
    result = login_user(identifier, password)
    if result.success:
        login_session(result.user)
        st.session_state["_language_synced"] = False  # re-adopt this user's saved language on rerun
        st.rerun()
    else:
        for err in result.errors:
            st.error(err)

st.markdown(f'<div class="cm-auth-switch">{t("auth.no_account")}</div>', unsafe_allow_html=True)
st.page_link("pages/5_Register.py", label=t("auth.create_account_link"))
st.markdown("</div></div>", unsafe_allow_html=True)
