from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import fetch_all, fetch_one, table_df
from modules.budget import build_budget_comparison
from modules.insurance_tracker import yearly_premium
from modules.pf_tracker import pf_projection
from utils.calculations import months_until, safe_pct
from utils.helpers import card, money
from utils.recommendations import build_recommendations
from utils.smart_alerts import collect_smart_alerts
from utils.translations import t


def _totals(user_id: int) -> dict:
    salary = fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM salary WHERE user_id=? AND month=strftime('%Y-%m','now')", (user_id,))
    profile_salary = fetch_one("SELECT monthly_salary FROM users WHERE id=?", (user_id,))
    income = salary["total"] or profile_salary["monthly_salary"] or 0
    expenses = fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=strftime('%Y-%m','now')", (user_id,))["total"]
    emi = fetch_one("SELECT COALESCE(SUM(emi_amount), 0) AS total FROM loans WHERE user_id=? AND remaining_balance > 0", (user_id,))["total"]
    reminders = fetch_one("SELECT COUNT(*) AS total FROM reminders WHERE user_id=? AND status!='Completed' AND reminder_date>=date('now')", (user_id,))["total"]
    retire = fetch_one("SELECT expected_retirement_date FROM users WHERE id=?", (user_id,))
    leave = fetch_one("SELECT remaining_cl, remaining_el FROM leave_balance WHERE user_id=?", (user_id,))
    upcoming_leave = fetch_one(
        "SELECT COUNT(*) AS total FROM leave_records WHERE user_id=? AND from_date>=date('now') AND status!='Rejected'",
        (user_id,),
    )["total"]
    pf = fetch_one("SELECT * FROM pf_tracker WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    insurance = fetch_one(
        """SELECT
        SUM(CASE WHEN status='Active' THEN 1 ELSE 0 END) AS active_policies,
        SUM(CASE WHEN renewal_date BETWEEN date('now') AND date('now', '+30 day') THEN 1 ELSE 0 END) AS upcoming_renewals
        FROM insurance_policies WHERE user_id=?""",
        (user_id,),
    )
    pf_current = pf["current_balance"] if pf else 0
    pf_monthly = (pf["employee_contribution"] + pf["employer_contribution"]) if pf else 0
    pf_years = months_until(pf["retirement_date"]) // 12 if pf else 0
    pf_df = pf_projection(pf_current, pf_monthly, pf["interest_rate"] if pf else 0, pf_years) if pf else pd.DataFrame()
    pf_estimated = pf_df.iloc[-1]["Estimated PF balance"] if not pf_df.empty else 0
    return {
        "income": income, "expenses": expenses, "savings": income - expenses, "emi": emi,
        "reminders": reminders,
        "retirement_months": months_until(retire["expected_retirement_date"]),
        "cl_remaining": leave["remaining_cl"] if leave else 0,
        "el_remaining": leave["remaining_el"] if leave else 0,
        "upcoming_leave": upcoming_leave,
        "pf_current": pf_current,
        "pf_estimated": pf_estimated,
        "active_insurance": insurance["active_policies"] or 0 if insurance else 0,
        "upcoming_insurance": insurance["upcoming_renewals"] or 0 if insurance else 0,
    }


def render(user: dict) -> None:
    st.title(t("dashboard"))
    user_id = user["id"]
    totals = _totals(user_id)

    cols = st.columns(4)
    savings_target = totals["income"] * 0.20
    recommended_spending = totals["income"] - savings_target
    data = [
        (t("monthly_salary"), money(totals["income"]), ""),
        (t("recommended_monthly_spending"), money(recommended_spending), "20%"),
        (t("actual_spending"), money(totals["expenses"]), ""),
        (t("savings_target"), money(savings_target), "20%"),
        (t("actual_savings"), money(totals["savings"]), f"{safe_pct(totals['savings'], totals['income'])}%"),
        (t("emi_ratio"), f"{safe_pct(totals['emi'], totals['income'])}%", money(totals["emi"])),
        (t("cl_remaining"), f"{totals['cl_remaining']:g}", f"Upcoming leave: {totals['upcoming_leave']}"),
        (t("el_remaining"), f"{totals['el_remaining']:g}", ""),
        (t("pf_current_balance"), money(totals["pf_current"]), ""),
        (t("estimated_pf_retirement"), money(totals["pf_estimated"]), ""),
        (t("active_insurance_policies"), str(int(totals["active_insurance"])), ""),
        (t("upcoming_insurance_renewal"), str(int(totals["upcoming_insurance"])), "30 days"),
        (t("retirement_countdown"), f"{totals['retirement_months']} months", ""),
        (t("upcoming_reminders"), str(totals["reminders"]), ""),
    ]
    for i, item in enumerate(data):
        with cols[i % 4]:
            card(*item)

    st.subheader("Financial charts")
    expenses = table_df("expenses", user_id)
    month_expenses = expenses.copy()
    if not month_expenses.empty:
        month_expenses = month_expenses[pd.to_datetime(month_expenses["expense_date"]).dt.strftime("%Y-%m") == pd.Timestamp.today().strftime("%Y-%m")]
    salary = table_df("salary", user_id)
    loans = table_df("loans", user_id)
    leave = table_df("leave_balance", user_id)
    pf = table_df("pf_tracker", user_id)
    insurance = table_df("insurance_policies", user_id)
    col1, col2 = st.columns(2)
    with col1:
        comparison, _ = build_budget_comparison(totals["income"], month_expenses)
        comparison_df = pd.DataFrame(comparison)
        chart_df = comparison_df.melt(
            id_vars="Category",
            value_vars=["Recommended amount", "Actual spending"],
            var_name="Type",
            value_name="Amount",
        )
        st.plotly_chart(px.bar(chart_df, x="Category", y="Amount", color="Type", barmode="group", title="Recommended vs actual spending"), use_container_width=True)
    with col2:
        if not salary.empty or not expenses.empty:
            s = salary.groupby("month", as_index=False)["amount"].sum() if not salary.empty else pd.DataFrame(columns=["month", "amount"])
            if not expenses.empty:
                expenses["month"] = pd.to_datetime(expenses["expense_date"]).dt.strftime("%Y-%m")
                e = expenses.groupby("month", as_index=False)["amount"].sum()
            else:
                e = pd.DataFrame(columns=["month", "amount"])
            trend = pd.merge(s, e, on="month", how="outer", suffixes=("_income", "_expense")).fillna(0)
            trend["savings"] = trend["amount_income"] - trend["amount_expense"]
            st.plotly_chart(px.line(trend, x="month", y="savings", markers=True, title="Monthly savings trend"), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        emi_df = pd.DataFrame({"Metric": ["Monthly income", "Monthly EMI"], "Amount": [totals["income"], totals["emi"]]})
        st.plotly_chart(px.bar(emi_df, x="Metric", y="Amount", title="EMI vs salary", color="Metric"), use_container_width=True)
    with col4:
        if not leave.empty:
            row = leave.iloc[-1]
            leave_df = pd.DataFrame(
                {
                    "Leave": ["CL used", "CL remaining", "EL used", "EL remaining"],
                    "Days": [row["used_cl"], row["remaining_cl"], row["used_el"], row["remaining_el"]],
                }
            )
            st.plotly_chart(px.bar(leave_df, x="Leave", y="Days", title="CL and EL balance", color="Leave"), use_container_width=True)
        else:
            st.info("Add leave balance to see CL and EL chart.")

    col5, col6 = st.columns(2)
    with col5:
        if not pf.empty:
            latest_pf = pf.iloc[-1]
            monthly_pf = latest_pf["employee_contribution"] + latest_pf["employer_contribution"]
            years_left = months_until(latest_pf["retirement_date"]) // 12
            pf_chart = pf_projection(latest_pf["current_balance"], monthly_pf, latest_pf["interest_rate"], years_left)
            st.plotly_chart(px.line(pf_chart, x="Year", y="Estimated PF balance", markers=True, title="PF growth projection"), use_container_width=True)
        else:
            st.info("Add PF details to see PF projection.")
    with col6:
        if not insurance.empty:
            insurance["yearly_premium"] = insurance.apply(lambda r: yearly_premium(r["premium_amount"], r["premium_frequency"]), axis=1)
            premium = insurance.groupby("insurance_type", as_index=False)["yearly_premium"].sum()
            st.plotly_chart(px.bar(premium, x="insurance_type", y="yearly_premium", title="Insurance premium by type"), use_container_width=True)
        else:
            st.info("Add insurance policies to see premium chart.")

    st.subheader("Smart recommendations")
    for item in build_recommendations(user_id, totals["income"], totals["expenses"], totals["emi"]):
        st.write(f"- {item}")

    st.subheader(t("smart_alerts"))
    for alert in collect_smart_alerts(user)[:5]:
        msg = f"**{alert['Area']}**: {alert['Message']}"
        if alert["Level"] == "Danger":
            st.error(msg)
        elif alert["Level"] == "Warning":
            st.warning(msg)
        elif alert["Level"] == "Good":
            st.success(msg)
        else:
            st.info(msg)

    if user["role"] == "admin":
        st.subheader("Admin overview")
        users = fetch_one("SELECT COUNT(*) AS total FROM users")["total"]
        rows = fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        st.write(f"Total users: **{users}**")
        st.write(f"System tables: **{len(rows)}**")
