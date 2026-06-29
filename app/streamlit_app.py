"""
CineMatch AI — entry point / router.

This file owns the one-time, page-config-and-up setup (page config, DB init,
CSS, session init) and builds the navigation. Individual pages under
pages/ contain only their own content — none of them call
st.set_page_config(), since Streamlit only allows that once, here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config.settings as config
from database.db import init_db
from database.models import get_language
from i18n.translator import current_language, set_current_language, t
from utils.session import current_user_id, current_username, init_session_state, is_authenticated, logout_session
from utils.styling import load_css

st.set_page_config(page_title=config.APP_NAME, layout="wide", initial_sidebar_state="expanded")

init_db()
init_session_state()
load_css(config.THEME_CSS)

# On first load of an authenticated session, adopt the user's saved language
# preference instead of always defaulting to English.
if is_authenticated() and not st.session_state.get("_language_synced"):
    set_current_language(get_language(current_user_id()))
    st.session_state["_language_synced"] = True

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-brand">
            <div>
                <div class="sidebar-title">{config.APP_NAME}</div>
                <div class="sidebar-subtitle">{t('app.tagline')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

pages = [
    st.Page("pages/0_Home.py", title=t("nav.home"), default=True),
    st.Page("pages/1_Recommendations.py", title=t("nav.recommendations")),
    st.Page("pages/2_Analytics.py", title=t("nav.analytics")),
    st.Page("pages/3_About.py", title=t("nav.about")),
]

if is_authenticated():
    pages.append(st.Page("pages/6_Settings.py", title=t("nav.settings")))
else:
    pages.append(st.Page("pages/4_Login.py", title=t("nav.login")))
    pages.append(st.Page("pages/5_Register.py", title=t("nav.register")))

nav = st.navigation(pages)

with st.sidebar:
    st.divider()
    if is_authenticated():
        initials = current_username()[:2].upper()
        st.markdown(
            f"""
            <div class="cm-user-row">
                <div class="cm-avatar">{initials}</div>
                <div>{current_username()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button(t("nav.logout"), width="stretch"):
            logout_session()
            st.rerun()
    else:
        st.caption(t("auth.continue_as_guest"))

nav.run()
