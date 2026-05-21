from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import execute, table_df
from utils.calculations import months_until
from utils.helpers import money, parse_date
from utils.translations import t


def pf_projection(current_balance: float, monthly_contribution: float, annual_rate: float, years: int) -> pd.DataFrame:
    balance = float(current_balance or 0)
    monthly_rate = (float(annual_rate or 0) / 100) / 12
    rows = []
    for year in range(0, max(0, years) + 1):
        if year > 0:
            for _ in range(12):
                balance = (balance + monthly_contribution) * (1 + monthly_rate)
        rows.append({"Year": year, "Estimated PF balance": round(balance, 2)})
    return pd.DataFrame(rows)


def render(user: dict) -> None:
    st.title(t("pf_tracker"))
    st.caption(t("pf_note"))
    user_id = user["id"]

    with st.form("pf_form"):
        col1, col2 = st.columns(2)
        pf_type = col1.text_input("PF account type", value="GPF / EPF / NPS-linked PF")
        employee = col2.number_input("Monthly employee contribution", min_value=0.0, step=500.0)
        employer = col1.number_input("Monthly employer/government contribution", min_value=0.0, step=500.0)
        current = col2.number_input("Current PF balance", min_value=0.0, step=10000.0)
        rate = col1.number_input("Interest rate (%)", min_value=0.0, value=7.1, step=0.1)
        joining = col2.date_input("Joining date", value=date(2015, 1, 1))
        retirement = col1.date_input("Expected retirement date", value=parse_date(user.get("expected_retirement_date")) or date(2045, 1, 1))
        nominee = col2.text_input("Nominee name")
        notes = st.text_area("Notes")
        if st.form_submit_button("Save PF details", use_container_width=True):
            execute(
                """INSERT INTO pf_tracker
                (user_id, pf_account_type, employee_contribution, employer_contribution,
                 current_balance, interest_rate, joining_date, retirement_date, nominee_name, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, pf_type, employee, employer, current, rate, joining.isoformat(), retirement.isoformat(), nominee, notes),
            )
            st.success("PF details saved.")

    df = table_df("pf_tracker", user_id)
    if df.empty:
        st.warning(t("complete_pf"))
        return

    latest = df.iloc[-1]
    monthly = float(latest["employee_contribution"] or 0) + float(latest["employer_contribution"] or 0)
    yearly = monthly * 12
    years_left = months_until(latest["retirement_date"]) // 12
    projection = pf_projection(latest["current_balance"], monthly, latest["interest_rate"], years_left)
    estimated = float(projection.iloc[-1]["Estimated PF balance"]) if not projection.empty else float(latest["current_balance"] or 0)
    interest_estimate = max(0, estimated - float(latest["current_balance"] or 0) - yearly * years_left)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Current PF balance", money(latest["current_balance"]))
    c2.metric("Monthly contribution", money(monthly))
    c3.metric("Yearly contribution", money(yearly))
    c4.metric("Estimated retirement PF value", money(estimated))
    c5.metric("Years left", f"{years_left:g}")

    if any(float(latest[col] or 0) <= 0 for col in ["current_balance", "employee_contribution", "interest_rate"]) or not latest["retirement_date"]:
        st.warning(t("complete_pf"))
    if years_left <= 5:
        st.warning(t("pf_nomination_warning"))

    st.write(f"Estimated interest earned: **{money(interest_estimate)}**")
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.line(projection, x="Year", y="Estimated PF balance", markers=True, title="PF growth year by year"), use_container_width=True)
    contribution_df = pd.DataFrame(
        {
            "Contribution": ["Employee", "Employer/Government"],
            "Monthly amount": [latest["employee_contribution"], latest["employer_contribution"]],
        }
    )
    col2.plotly_chart(px.pie(contribution_df, names="Contribution", values="Monthly amount", title="Employee vs employer contribution"), use_container_width=True)
    st.dataframe(df.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
