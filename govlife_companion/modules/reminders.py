from __future__ import annotations

from datetime import date

import streamlit as st

from database.db import execute, table_df
from utils.helpers import REMINDER_CATEGORIES
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("reminders"))
    user_id = user["id"]
    with st.form("reminder_form"):
        col1, col2 = st.columns(2)
        title = col1.text_input("Title")
        category = col2.selectbox("Category", REMINDER_CATEGORIES)
        reminder_date = col1.date_input("Date", value=date.today())
        repeat = col2.selectbox("Repeat type", ["Once", "Daily", "Weekly", "Monthly", "Yearly"])
        priority = col1.selectbox("Priority", ["Low", "Medium", "High"])
        status = col2.selectbox("Status", ["Pending", "Completed"])
        notes = st.text_area("Notes")
        if st.form_submit_button("Add reminder"):
            execute(
                """INSERT INTO reminders (user_id, title, category, reminder_date, repeat_type, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, title, category, reminder_date.isoformat(), repeat, priority, status, notes),
            )
            st.success("Reminder saved.")
    df = table_df("reminders", user_id)
    if df.empty:
        st.info("No reminders yet.")
        return
    today = date.today().isoformat()
    tabs = st.tabs(["Today", "This week", "Overdue", "Completed", "All"])
    tabs[0].dataframe(df[df["reminder_date"] == today], use_container_width=True, hide_index=True)
    tabs[1].dataframe(df[(df["reminder_date"] >= today) & (df["reminder_date"] <= date.today().replace(day=min(date.today().day + 7, 28)).isoformat())], use_container_width=True, hide_index=True)
    tabs[2].dataframe(df[(df["reminder_date"] < today) & (df["status"] != "Completed")], use_container_width=True, hide_index=True)
    tabs[3].dataframe(df[df["status"] == "Completed"], use_container_width=True, hide_index=True)
    tabs[4].dataframe(df.sort_values("reminder_date"), use_container_width=True, hide_index=True)
