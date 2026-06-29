"""CineMatch AI — Register page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config.settings as config
from i18n.translator import t
from services.auth_service import register_user
from utils.session import init_session_state, is_authenticated, login_session

init_session_state()

if is_authenticated():
    st.switch_page("pages/0_Home.py")

st.markdown('<div class="cm-auth-wrapper cm-fade-in">', unsafe_allow_html=True)
st.markdown('<div class="cm-auth-card">', unsafe_allow_html=True)
st.markdown(f'<div class="cm-auth-title">{t("auth.register_title")}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="cm-auth-subtitle">{t("auth.register_subtitle")}</div>', unsafe_allow_html=True)

with st.form("register_form"):
    username = st.text_input(t("auth.username"))
    email = st.text_input(t("auth.email"))
    phone_number = st.text_input(t("auth.phone_number"))
    password = st.text_input(t("auth.password"), type="password")
    confirm_password = st.text_input(t("auth.confirm_password"), type="password")
    submitted = st.form_submit_button(t("auth.register_button"), width="stretch")

st.caption(f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters, with a letter and a number.")

if submitted:
    result = register_user(username, email, phone_number, password, confirm_password)
    if result.success:
        login_session(result.user)
        st.success(t("auth.account_created"))
        st.session_state["_language_synced"] = False
        st.rerun()
    else:
        for err in result.errors:
            st.error(err)

st.markdown(f'<div class="cm-auth-switch">{t("auth.have_account")}</div>', unsafe_allow_html=True)
st.page_link("pages/4_Login.py", label=t("auth.login_link"))
st.markdown("</div></div>", unsafe_allow_html=True)
