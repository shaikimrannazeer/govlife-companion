from __future__ import annotations

from datetime import date

import streamlit as st

from database.db import execute, table_df
from utils.helpers import money
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("children_education_planner"))
    user_id = user["id"]
    with st.form("education_form"):
        col1, col2 = st.columns(2)
        child = col1.text_input("Child name")
        institution = col2.text_input("School/college name")
        course = col1.text_input("Class/course")
        fee = col2.number_input("Fee amount", min_value=0.0, step=1000.0)
        fee_due = col1.date_input("Fee due date", value=date.today())
        exam = col2.date_input("Exam date", value=date.today())
        tuition = col1.number_input("Tuition fee", min_value=0.0, step=500.0)
        goal = col2.number_input("Education savings goal", min_value=0.0, step=10000.0)
        notes = st.text_area("Scholarship notes")
        if st.form_submit_button("Add education plan"):
            execute(
                """INSERT INTO education (user_id, child_name, institution, class_course, fee_amount,
                fee_due_date, exam_date, tuition_fee, savings_goal, scholarship_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, child, institution, course, fee, fee_due.isoformat(), exam.isoformat(), tuition, goal, notes),
            )
            st.success("Education plan added.")
    df = table_df("education", user_id)
    if df.empty:
        st.info("No education plans yet.")
        return
    yearly = (df["fee_amount"].sum() + df["tuition_fee"].sum()) * 12
    goal = df["savings_goal"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Upcoming fee records", len(df))
    c2.metric("Estimated yearly education cost", money(yearly))
    c3.metric("Savings needed per month", money(goal / 12 if goal else 0))
    st.dataframe(df.sort_values("fee_due_date"), use_container_width=True, hide_index=True)
