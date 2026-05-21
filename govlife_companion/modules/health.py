from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st

from database.db import execute, table_df
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("health_tracker"))
    st.caption("Tracking only. This app does not provide medical diagnosis.")
    user_id = user["id"]
    with st.form("health_form"):
        col1, col2, col3 = st.columns(3)
        member = col1.text_input("Family member")
        record_date = col2.date_input("Record date", value=date.today())
        weight = col3.number_input("Weight (kg)", min_value=0.0, step=0.5)
        systolic = col1.number_input("BP systolic", min_value=0, step=1)
        diastolic = col2.number_input("BP diastolic", min_value=0, step=1)
        sugar = col3.number_input("Sugar level", min_value=0.0, step=1.0)
        medicine = col1.text_input("Medicine reminder")
        reminder_date = col2.date_input("Medicine reminder date", value=date.today())
        appointment = col3.date_input("Doctor appointment", value=date.today())
        checkup = st.date_input("Health checkup schedule", value=date.today())
        notes = st.text_area("Medical history notes")
        if st.form_submit_button("Add health record"):
            execute(
                """INSERT INTO health_records
                (user_id, member_name, record_date, bp_systolic, bp_diastolic, sugar, weight,
                 medicine, reminder_date, appointment_date, checkup_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, member, record_date.isoformat(), int(systolic), int(diastolic), sugar, weight,
                 medicine, reminder_date.isoformat(), appointment.isoformat(), checkup.isoformat(), notes),
            )
            st.success("Health record added.")

    df = table_df("health_records", user_id)
    if df.empty:
        st.info("No health records yet.")
        return
    today = date.today().isoformat()
    if (df["reminder_date"] == today).any():
        st.warning("Medicine due today.")
    if (df["bp_systolic"].fillna(0) > 140).any() or (df["bp_diastolic"].fillna(0) > 90).any():
        st.warning("High BP reading found. Please consult a qualified doctor.")
    if (df["sugar"].fillna(0) > 180).any():
        st.warning("High sugar reading found. Please consult a qualified doctor.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(px.line(df, x="record_date", y=["bp_systolic", "bp_diastolic"], color="member_name", title="BP trend"), use_container_width=True)
    with col2:
        st.plotly_chart(px.line(df, x="record_date", y="sugar", color="member_name", title="Sugar trend"), use_container_width=True)
    with col3:
        st.plotly_chart(px.line(df, x="record_date", y="weight", color="member_name", title="Weight trend"), use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
