from __future__ import annotations

from datetime import date

import plotly.express as px
import streamlit as st

from database.db import execute, table_df
from utils.calculations import loan_progress, safe_pct
from utils.helpers import LOAN_TYPES, money
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("loan_emi_tracker"))
    user_id = user["id"]
    with st.form("loan_form"):
        col1, col2, col3 = st.columns(3)
        loan_type = col1.selectbox("Loan type", LOAN_TYPES)
        bank = col2.text_input("Bank name")
        due_day = col3.number_input("Due day reminder", min_value=1, max_value=31, value=7)
        loan_amount = col1.number_input("Loan amount", min_value=0.0, step=10000.0)
        rate = col2.number_input("Interest rate (%)", min_value=0.0, step=0.1)
        emi = col3.number_input("EMI amount", min_value=0.0, step=1000.0)
        start = col1.date_input("Start date", value=date.today())
        end = col2.date_input("End date", value=date.today())
        remaining = col3.number_input("Remaining balance", min_value=0.0, step=10000.0)
        if st.form_submit_button("Add loan"):
            execute(
                """INSERT INTO loans (user_id, loan_type, bank_name, loan_amount, interest_rate,
                emi_amount, start_date, end_date, remaining_balance, due_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, loan_type, bank, loan_amount, rate, emi, start.isoformat(), end.isoformat(), remaining, int(due_day)),
            )
            st.success("Loan added.")

    loans = table_df("loans", user_id)
    if loans.empty:
        st.info("No loans added yet.")
        return

    total_loan = loans["loan_amount"].sum()
    total_emi = loans["emi_amount"].sum()
    salary = float(user.get("monthly_salary") or 0)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total loan amount", money(total_loan))
    c2.metric("Total EMI per month", money(total_emi))
    c3.metric("EMI to salary ratio", f"{safe_pct(total_emi, salary)}%")

    loans["closing_progress"] = loans.apply(lambda r: loan_progress(r["loan_amount"], r["remaining_balance"]), axis=1)
    st.plotly_chart(px.bar(loans, x="loan_type", y="closing_progress", color="bank_name", title="Loan closing progress"), use_container_width=True)

    st.subheader("Extra payment calculator")
    col1, col2 = st.columns(2)
    extra = col1.number_input("Extra payment per month", min_value=0.0, step=1000.0)
    selected_remaining = col2.number_input("Loan remaining balance to estimate", min_value=0.0, value=float(loans["remaining_balance"].sum()), step=10000.0)
    if total_emi + extra > 0:
        months = selected_remaining / (total_emi + extra)
        base_months = selected_remaining / total_emi if total_emi else months
        st.success(f"Estimated closing time: {months:.1f} months. Approx months saved: {max(0, base_months - months):.1f}.")
        st.caption("Interest saved is an estimate. Please verify exact figures with your bank.")
    st.dataframe(loans, use_container_width=True, hide_index=True)
