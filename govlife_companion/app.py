from __future__ import annotations

import streamlit as st

from database.db import execute, fetch_one, init_db
from modules import (
    ai_assistant,
    budget,
    dashboard,
    education,
    backup_restore,
    family_profiles,
    health,
    insurance_tracker,
    leave_tracker,
    loans,
    notifications,
    pf_tracker,
    reminders,
    reports,
    retirement,
    smart_alerts,
    transfer,
    trips,
)
from modules.auth import current_user, logout, render_auth
from utils.helpers import load_css
from utils.translations import LANGUAGES, t


st.set_page_config(page_title="GovLife Companion", page_icon="GL", layout="wide")
init_db()
load_css()


def open_ai_assistant() -> None:
    st.session_state.nav_page = "AI Assistant"


def render_floating_robo() -> None:
    st.markdown(
        f'<div class="robo-bubble-fixed">{t("may_i_help")}</div>',
        unsafe_allow_html=True,
    )
    st.button("🤖", key="robo_help_button", help="Open AI Assistant", on_click=open_ai_assistant)


def render_admin(user: dict) -> None:
    st.title("Admin")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total users", fetch_one("SELECT COUNT(*) AS total FROM users")["total"])
    c2.metric("Leave records", fetch_one("SELECT COUNT(*) AS total FROM leave_records")["total"])
    c3.metric("Reminders created", fetch_one("SELECT COUNT(*) AS total FROM reminders")["total"])
    c4.metric("PF records", fetch_one("SELECT COUNT(*) AS total FROM pf_tracker")["total"])
    c5.metric("Insurance policies", fetch_one("SELECT COUNT(*) AS total FROM insurance_policies")["total"])

    st.subheader("Anonymous app usage summary")
    st.write("This summary uses aggregate counts only and does not show private user records.")
    st.dataframe(
        {
            "Area": ["Budget records", "Loans", "PF records", "Insurance policies", "Health records", "Education plans", "AI messages"],
            "Count": [
                fetch_one("SELECT COUNT(*) AS total FROM expenses")["total"],
                fetch_one("SELECT COUNT(*) AS total FROM loans")["total"],
                fetch_one("SELECT COUNT(*) AS total FROM pf_tracker")["total"],
                fetch_one("SELECT COUNT(*) AS total FROM insurance_policies")["total"],
                fetch_one("SELECT COUNT(*) AS total FROM health_records")["total"],
                fetch_one("SELECT COUNT(*) AS total FROM education")["total"],
                fetch_one("SELECT COUNT(*) AS total FROM ai_chat_history")["total"],
            ],
        },
        use_container_width=True,
    )
    st.subheader("Manage categories")
    with st.form("category_form"):
        key = st.text_input("Category group", value="expense_category")
        value = st.text_input("Category name")
        if st.form_submit_button("Save category") and value:
            execute("INSERT INTO admin_settings (user_id, setting_key, setting_value) VALUES (?, ?, ?)", (user["id"], key, value))
            st.success("Category saved.")


def render_family(user: dict) -> None:
    from datetime import date
    from database.db import table_df

    st.title("Family Members")
    with st.form("family_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Name")
        relation = col2.text_input("Relation")
        dob = col1.date_input("Date of birth", value=date(2000, 1, 1))
        notes = st.text_area("Notes")
        if st.form_submit_button("Add family member"):
            execute(
                "INSERT INTO family_members (user_id, name, relation, date_of_birth, notes) VALUES (?, ?, ?, ?, ?)",
                (user["id"], name, relation, dob.isoformat(), notes),
            )
            st.success("Family member added.")
    df = table_df("family_members", user["id"])
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)


def main() -> None:
    user = current_user()
    if not user:
        render_auth()
        return
    st.session_state.language = st.session_state.get("language") or user.get("preferred_language") or "English"
    render_floating_robo()

    with st.sidebar:
        st.title("GovLife")
        selected_language = st.selectbox(
            t("language"),
            LANGUAGES,
            index=LANGUAGES.index(st.session_state.get("language", "English")),
            key="sidebar_language",
        )
        if selected_language != st.session_state.get("language"):
            st.session_state.language = selected_language
            execute("UPDATE users SET preferred_language=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (selected_language, user["id"]))
            st.session_state.user["preferred_language"] = selected_language
            st.rerun()
        st.write(user["full_name"])
        st.caption(f"{user['department'] or 'Department'} • {user['role'].title()}")
        pages = [
            "Dashboard", "Salary Budget Planner", "Loan and EMI Tracker", "Leave Tracker",
            "PF Tracker", "Insurance Tracker", "Health Tracker", "Children Education Planner",
            "Transfer Life Manager", "Trip Planner", "Retirement Planner", "Reminders",
            "Notifications", "Family Profiles", "Smart Alerts", "Backup & Restore",
            "AI Assistant", "Reports",
        ]
        if user["role"] == "admin":
            pages.append("Admin Panel")
        page = st.radio(
            "Navigation",
            pages,
            key="nav_page",
            label_visibility="collapsed",
            format_func=lambda page_name: {
                "Dashboard": t("dashboard"),
                "Salary Budget Planner": t("salary_budget_planner"),
                "Loan and EMI Tracker": t("loan_emi_tracker"),
                "Leave Tracker": t("leave_tracker"),
                "PF Tracker": t("pf_tracker"),
                "Insurance Tracker": t("insurance_tracker"),
                "Health Tracker": t("health_tracker"),
                "Children Education Planner": t("children_education_planner"),
                "Transfer Life Manager": t("transfer_life_manager"),
                "Trip Planner": t("trip_planner"),
                "Retirement Planner": t("retirement_planner"),
                "Reminders": t("reminders"),
                "Notifications": t("notifications"),
                "Family Profiles": t("family_profiles"),
                "Smart Alerts": t("smart_alerts"),
                "Backup & Restore": t("backup_restore"),
                "AI Assistant": t("ai_assistant"),
                "Reports": t("reports"),
                "Admin Panel": t("admin_panel"),
            }.get(page_name, page_name),
        )
        st.button(t("logout"), on_click=logout, use_container_width=True)

    routes = {
        "Dashboard": dashboard.render,
        "Salary Budget Planner": budget.render,
        "Loan and EMI Tracker": loans.render,
        "Family Members": render_family,
        "Leave Tracker": leave_tracker.render,
        "PF Tracker": pf_tracker.render,
        "Insurance Tracker": insurance_tracker.render,
        "Health Tracker": health.render,
        "Children Education Planner": education.render,
        "Transfer Life Manager": transfer.render,
        "Trip Planner": trips.render,
        "Retirement Planner": retirement.render,
        "Reminders": reminders.render,
        "Notifications": notifications.render,
        "Family Profiles": family_profiles.render,
        "Smart Alerts": smart_alerts.render,
        "Backup & Restore": backup_restore.render,
        "AI Assistant": ai_assistant.render,
        "Reports": reports.render,
        "Admin Panel": render_admin,
    }
    routes[page](user)


if __name__ == "__main__":
    main()
