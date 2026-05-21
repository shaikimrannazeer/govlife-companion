from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st

from database.db import execute, table_df
from utils.calculations import months_until, retirement_score
from utils.helpers import money
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("retirement_planner"))
    user_id = user["id"]
    default_retire = user.get("expected_retirement_date") or "2045-01-01"
    with st.form("retirement_form"):
        col1, col2 = st.columns(2)
        retirement_date = col1.date_input("Retirement date", value=date.fromisoformat(default_retire))
        pension = col2.number_input("Pension estimate input", min_value=0.0, step=1000.0)
        pf = col1.number_input("PF/NPS savings input", min_value=0.0, step=10000.0)
        gratuity = col2.number_input("Gratuity estimate input", min_value=0.0, step=10000.0)
        goal = col1.number_input("Retirement corpus goal", min_value=0.0, step=10000.0)
        expense = col2.number_input("Post-retirement monthly expense estimate", min_value=0.0, step=1000.0)
        notes = st.text_area("Notes")
        if st.form_submit_button("Save retirement plan"):
            execute(
                """INSERT INTO retirement (user_id, retirement_date, pension_estimate, pf_nps_savings,
                gratuity_estimate, corpus_goal, post_retirement_expense, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, retirement_date.isoformat(), pension, pf, gratuity, goal, expense, notes),
            )
            st.success("Retirement plan saved.")

    df = table_df("retirement", user_id)
    if df.empty:
        st.info("Add retirement estimates to see readiness.")
        return
    latest = df.iloc[-1]
    corpus = latest["pf_nps_savings"] + latest["gratuity_estimate"]
    gap = max(0, latest["corpus_goal"] - corpus)
    months = months_until(latest["retirement_date"])
    monthly_needed = gap / months if months else gap
    score = retirement_score(corpus, latest["corpus_goal"], latest["pension_estimate"], latest["post_retirement_expense"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Years/months left", f"{months // 12}y {months % 12}m")
    c2.metric("Readiness score", f"{score}/100")
    c3.metric("Savings gap", money(gap))
    c4.metric("Monthly savings needed", money(monthly_needed))
    if gap > latest["corpus_goal"] * 0.30:
        st.warning("Retirement savings gap is high.")
    if latest["pension_estimate"] < latest["post_retirement_expense"]:
        st.warning("Expected pension is lower than expected expenses. Please verify official rules with your department.")
    chart = {"Metric": ["Corpus", "Gap", "Pension", "Monthly expense"], "Amount": [corpus, gap, latest["pension_estimate"], latest["post_retirement_expense"]]}
    st.plotly_chart(px.bar(chart, x="Metric", y="Amount", title="Retirement timeline and readiness"), use_container_width=True)
