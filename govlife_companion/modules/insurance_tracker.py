from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import execute, table_df
from utils.helpers import INSURANCE_TYPES, money
from utils.translations import t


FREQUENCY_MULTIPLIER = {
    "Monthly": 12,
    "Quarterly": 4,
    "Half-yearly": 2,
    "Yearly": 1,
    "One-time": 0,
}


def yearly_premium(amount: float, frequency: str) -> float:
    return float(amount or 0) * FREQUENCY_MULTIPLIER.get(frequency, 1)


def render(user: dict) -> None:
    st.title(t("insurance_tracker"))
    user_id = user["id"]

    with st.form("insurance_form"):
        col1, col2 = st.columns(2)
        policy = col1.text_input("Policy name")
        company = col2.text_input("Insurance company")
        number = col1.text_input("Policy number")
        insurance_type = col2.selectbox("Insurance type", INSURANCE_TYPES)
        insured = col1.text_input("Insured person name")
        sum_assured = col2.number_input("Sum assured", min_value=0.0, step=10000.0)
        premium = col1.number_input("Premium amount", min_value=0.0, step=500.0)
        frequency = col2.selectbox("Premium frequency", ["Monthly", "Quarterly", "Half-yearly", "Yearly", "One-time"])
        start = col1.date_input("Start date", value=date.today())
        renewal = col2.date_input("Renewal date", value=date.today())
        maturity = col1.date_input("Maturity date", value=date.today())
        nominee = col2.text_input("Nominee name")
        status = st.selectbox("Status", ["Active", "Expired", "Pending Renewal"])
        notes = st.text_area("Notes")
        if st.form_submit_button("Save policy", use_container_width=True):
            execute(
                """INSERT INTO insurance_policies
                (user_id, policy_name, company_name, policy_number, insurance_type, insured_person_name,
                 sum_assured, premium_amount, premium_frequency, start_date, renewal_date, maturity_date,
                 nominee_name, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id, policy, company, number, insurance_type, insured, sum_assured, premium,
                    frequency, start.isoformat(), renewal.isoformat(), maturity.isoformat(), nominee, status, notes,
                ),
            )
            execute(
                """INSERT INTO reminders (user_id, title, category, reminder_date, repeat_type, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)""",
                (user_id, f"{policy} renewal", "Insurance renewal", renewal.isoformat(), "Yearly", "High", "Auto-created from Insurance Tracker"),
            )
            execute(
                """INSERT INTO reminders (user_id, title, category, reminder_date, repeat_type, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)""",
                (user_id, f"{policy} premium due", "Insurance premium", renewal.isoformat(), frequency, "Medium", "Auto-created from Insurance Tracker"),
            )
            execute(
                """INSERT INTO reminders (user_id, title, category, reminder_date, repeat_type, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)""",
                (user_id, f"{policy} maturity", "Insurance maturity", maturity.isoformat(), "Once", "Medium", "Auto-created from Insurance Tracker"),
            )
            st.success("Insurance policy saved.")

    df = table_df("insurance_policies", user_id)
    if df.empty:
        st.info("No insurance policies added yet.")
        return

    df["yearly_premium"] = df.apply(lambda r: yearly_premium(r["premium_amount"], r["premium_frequency"]), axis=1)
    today = pd.Timestamp(date.today())
    renewal_dates = pd.to_datetime(df["renewal_date"], errors="coerce")
    renewal_due = (renewal_dates >= today) & (renewal_dates <= today + pd.Timedelta(days=30))
    expired = (df["status"] == "Expired") | (renewal_dates < today)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total active policies", int((df["status"] == "Active").sum()))
    c2.metric("Total yearly premium", money(df["yearly_premium"].sum()))
    c3.metric("Upcoming renewals", int(renewal_due.sum()))
    c4.metric("Expired policies", int(expired.sum()))
    c5.metric("Total coverage amount", money(df["sum_assured"].sum()))

    if renewal_due.any():
        st.warning(t("insurance_renewal_soon"))
    if expired.any():
        st.error(t("policy_expired"))

    col1, col2, col3 = st.columns(3)
    type_filter = col1.multiselect("Filter by type", INSURANCE_TYPES)
    status_filter = col2.multiselect("Filter by status", ["Active", "Expired", "Pending Renewal"])
    due_only = col3.checkbox("Renewal due")
    view = df.copy()
    if type_filter:
        view = view[view["insurance_type"].isin(type_filter)]
    if status_filter:
        view = view[view["status"].isin(status_filter)]
    if due_only:
        view = view.loc[renewal_due]

    table = view.rename(
        columns={
            "policy_name": "Policy name",
            "insurance_type": "Type",
            "company_name": "Company",
            "premium_amount": "Premium",
            "renewal_date": "Renewal date",
            "status": "Status",
        }
    )
    st.dataframe(table[["Policy name", "Type", "Company", "Premium", "Renewal date", "Status"]], use_container_width=True, hide_index=True)

    col4, col5 = st.columns(2)
    premium_by_type = df.groupby("insurance_type", as_index=False)["yearly_premium"].sum()
    coverage_by_type = df.groupby("insurance_type", as_index=False)["sum_assured"].sum()
    col4.plotly_chart(px.bar(premium_by_type, x="insurance_type", y="yearly_premium", title="Insurance type wise premium"), use_container_width=True)
    col5.plotly_chart(px.bar(coverage_by_type, x="insurance_type", y="sum_assured", title="Coverage amount by insurance type"), use_container_width=True)
