from __future__ import annotations

from datetime import date

import streamlit as st

from database.db import execute, fetch_one
from utils.security import hash_password, verify_password
from utils.translations import LANGUAGES, t


def current_user():
    return st.session_state.get("user")


def logout() -> None:
    st.session_state.pop("user", None)
    st.rerun()


def _sync_auth_language() -> None:
    st.session_state.language = st.session_state.auth_language


def render_auth() -> None:
    if "language" not in st.session_state:
        st.session_state.language = "English"
    if "auth_language" not in st.session_state:
        st.session_state.auth_language = st.session_state.language
    st.selectbox(
        t("please_select_language"),
        LANGUAGES,
        key="auth_language",
        on_change=_sync_auth_language,
    )
    st.title("GovLife Companion")
    st.caption("A personal life management app for government employees and families.")
    tab_login, tab_register = st.tabs([t("login"), t("register")])

    with tab_login:
        with st.form("login_form"):
            login_id = st.text_input(t("email_mobile"))
            password = st.text_input(t("password"), type="password")
            submitted = st.form_submit_button(t("login"), use_container_width=True)
        if submitted:
            login_id = login_id.strip()
            if not login_id or not password:
                st.warning(t("invalid_login"))
                return

            user = fetch_one("SELECT * FROM users WHERE login_id=?", (login_id,))
            password_matches = bool(user and verify_password(password, user["password_hash"]))
            if password_matches:
                st.session_state.user = dict(user)
                st.session_state.language = user["preferred_language"] or st.session_state.get("language", "English")
                st.rerun()
                return

            st.error(t("invalid_login"))

        st.info("Demo user: demo@govlife.in / demo123\n\nAdmin: admin@govlife.in / admin123")

    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input(t("full_name"))
            login_id = st.text_input(t("email_mobile"), key="reg_login")
            password = st.text_input(t("create_password"), type="password")
            department = st.text_input(t("department"))
            job_type = st.text_input(t("job_type"))
            col1, col2 = st.columns(2)
            with col1:
                joining = st.date_input(t("date_of_joining"), value=date(2015, 1, 1))
                monthly_salary = st.number_input(t("monthly_salary"), min_value=0.0, step=1000.0)
            with col2:
                retirement = st.date_input(t("expected_retirement_date"), value=date(2045, 1, 1))
                family_size = st.number_input(t("family_size"), min_value=1, step=1)
            city = st.text_input(t("city"))
            register = st.form_submit_button(t("create_account"), use_container_width=True)

        if register:
            if not full_name or not login_id or not password:
                st.warning(t("required_register"))
                return
            try:
                execute(
                    """INSERT INTO users
                    (full_name, login_id, password_hash, role, department, job_type,
                    date_of_joining, expected_retirement_date, monthly_salary, city, family_size, preferred_language)
                    VALUES (?, ?, ?, 'user', ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        full_name.strip(), login_id.strip(), hash_password(password), department,
                        job_type, joining.isoformat(), retirement.isoformat(),
                        monthly_salary, city, int(family_size), st.session_state.get("language", "English"),
                    ),
                )
                st.success(t("account_created"))
            except Exception:
                st.error(t("already_registered"))
