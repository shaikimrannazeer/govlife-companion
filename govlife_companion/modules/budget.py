from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import execute, table_df
from utils.calculations import (
    BUDGET_CATEGORY_MAP,
    budget_health_score,
    budget_status,
    recommended_budget,
    safe_pct,
)
from utils.helpers import EXPENSE_CATEGORIES, money
from utils.translations import t


def build_budget_comparison(salary_amount: float, expenses) -> tuple[list[dict], bool]:
    rows, adjusted = recommended_budget(salary_amount)
    actual_by_category = {}
    if expenses is not None and not expenses.empty:
        grouped = expenses.groupby("category")["amount"].sum().to_dict()
        for row in rows:
            actual_by_category[row["Category"]] = sum(grouped.get(cat, 0) for cat in BUDGET_CATEGORY_MAP[row["Category"]])

    savings_actual = max(0, float(salary_amount or 0) - (expenses["amount"].sum() if expenses is not None and not expenses.empty else 0))
    for row in rows:
        actual = savings_actual if row["Category"] in {"Savings / investment", "Emergency fund"} else actual_by_category.get(row["Category"], 0)
        row["Actual spending"] = round(actual, 2)
        row["Difference"] = round(row["Recommended amount"] - actual, 2)
        row["Status"] = budget_status(row["Category"], actual, row["Recommended amount"])
    return rows, adjusted


def render(user: dict) -> None:
    user_id = user["id"]
    st.title(t("salary_budget_planner"))
    col1, col2 = st.columns(2)
    with col1:
        with st.form("salary_form"):
            month = st.text_input("Month (YYYY-MM)", value=date.today().strftime("%Y-%m"))
            amount = st.number_input("Income amount", min_value=0.0, step=1000.0)
            source = st.text_input("Income source", value="Monthly salary")
            notes = st.text_area("Notes")
            if st.form_submit_button("Add income"):
                execute("INSERT INTO salary (user_id, month, amount, source, notes) VALUES (?, ?, ?, ?, ?)", (user_id, month, amount, source, notes))
                st.success("Income added.")
    with col2:
        with st.form("expense_form"):
            expense_date = st.date_input("Expense date", value=date.today())
            category = st.selectbox("Category", EXPENSE_CATEGORIES)
            expense_type = st.radio("Expense type", ["Fixed", "Variable"], horizontal=True)
            amount = st.number_input("Expense amount", min_value=0.0, step=500.0, key="expense_amount")
            notes = st.text_area("Expense notes")
            if st.form_submit_button("Add expense"):
                execute(
                    "INSERT INTO expenses (user_id, expense_date, category, amount, expense_type, notes) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, expense_date.isoformat(), category, amount, expense_type, notes),
                )
                st.success("Expense added.")

    salary = table_df("salary", user_id)
    expenses = table_df("expenses", user_id)
    current_month = date.today().strftime("%Y-%m")
    month_salary = salary[salary["month"] == current_month] if not salary.empty else salary
    month_expenses = expenses[pd.to_datetime(expenses["expense_date"]).dt.strftime("%Y-%m") == current_month] if not expenses.empty else expenses
    income = month_salary["amount"].sum() if not month_salary.empty else float(user.get("monthly_salary") or 0)
    spent = month_expenses["amount"].sum() if not month_expenses.empty else 0
    emi = month_expenses.loc[month_expenses["category"] == "EMI", "amount"].sum() if not month_expenses.empty else 0
    savings = income - spent
    score = budget_health_score(income, spent, emi)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total income", money(income))
    c2.metric("Total expenses", money(spent))
    c3.metric("Savings", money(savings), f"{safe_pct(savings, income)}%")
    c4.metric("Budget health score", f"{score}/100")

    if income and emi / income > 0.40:
        st.warning("EMI is more than 40% of income.")
    if income and savings / income < 0.20:
        st.warning("Savings are less than 20% of income.")
    if spent > income:
        st.error("Expenses are more than income.")

    st.subheader(t("salary_budget_planner"))
    plan_salary = st.number_input(
        "Monthly salary for budget plan",
        min_value=0.0,
        value=float(income or user.get("monthly_salary") or 0),
        step=1000.0,
    )
    if st.button(t("generate_budget_plan"), use_container_width=True):
        st.session_state.show_budget_plan = True

    if st.session_state.get("show_budget_plan"):
        comparison, adjusted = build_budget_comparison(plan_salary, month_expenses)
        if adjusted:
            st.warning("The requested category percentages total more than 100%, so the app adjusted them proportionally for a realistic plan.")
        comparison_df = pd.DataFrame(comparison)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        emi_actual = comparison_df.loc[comparison_df["Category"] == "EMI / loans", "Actual spending"].sum()
        savings_actual = comparison_df.loc[comparison_df["Category"] == "Savings / investment", "Actual spending"].sum()
        if plan_salary and emi_actual / plan_salary > 0.20:
            st.warning(t("emi_warning"))
        if plan_salary and savings_actual / plan_salary < 0.20:
            st.warning(t("savings_low"))
        if spent > plan_salary:
            st.error(t("expenses_high"))

        chart_df = comparison_df.melt(
            id_vars="Category",
            value_vars=["Recommended amount", "Actual spending"],
            var_name="Type",
            value_name="Amount",
        )
        st.plotly_chart(px.bar(chart_df, x="Category", y="Amount", color="Type", barmode="group", title="Recommended budget vs actual spending"), use_container_width=True)
        st.plotly_chart(px.pie(comparison_df, names="Category", values="Recommended amount", title="Salary allocation pie chart"), use_container_width=True)

    if not expenses.empty:
        st.plotly_chart(px.bar(expenses.groupby("category", as_index=False)["amount"].sum(), x="category", y="amount", title="Family expense breakdown"), use_container_width=True)
        st.dataframe(expenses.sort_values("expense_date", ascending=False), use_container_width=True, hide_index=True)
