from __future__ import annotations

import io
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database.db import fetch_one, table_df
from modules.insurance_tracker import yearly_premium
from modules.pf_tracker import pf_projection
from utils.calculations import months_until, safe_pct
from utils.helpers import money


def build_monthly_report_pdf(user: dict) -> bytes:
    user_id = user["id"]
    salary_row = fetch_one(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM salary WHERE user_id=? AND month=strftime('%Y-%m','now')",
        (user_id,),
    )
    salary = salary_row["total"] or float(user.get("monthly_salary") or 0)
    expenses_row = fetch_one(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=strftime('%Y-%m','now')",
        (user_id,),
    )
    expenses = expenses_row["total"] or 0
    loans = table_df("loans", user_id)
    leave = fetch_one("SELECT * FROM leave_balance WHERE user_id=?", (user_id,))
    pf = table_df("pf_tracker", user_id)
    insurance = table_df("insurance_policies", user_id)
    retirement = table_df("retirement", user_id)
    reminders = fetch_one("SELECT COUNT(*) AS total FROM reminders WHERE user_id=? AND status!='Completed'", (user_id,))

    total_emi = loans["emi_amount"].sum() if not loans.empty else 0
    yearly_prem = 0
    active_policies = 0
    if not insurance.empty:
        active_policies = int((insurance["status"] == "Active").sum())
        yearly_prem = sum(yearly_premium(row["premium_amount"], row["premium_frequency"]) for _, row in insurance.iterrows())
    pf_estimate = 0
    if not pf.empty:
        latest_pf = pf.iloc[-1]
        monthly_pf = latest_pf["employee_contribution"] + latest_pf["employer_contribution"]
        years_left = months_until(latest_pf["retirement_date"]) // 12
        projected = pf_projection(latest_pf["current_balance"], monthly_pf, latest_pf["interest_rate"], years_left)
        pf_estimate = projected.iloc[-1]["Estimated PF balance"] if not projected.empty else 0

    lines = [
        "GovLife Companion - Monthly Report",
        f"Date: {date.today().isoformat()}",
        f"Employee: {user.get('full_name')}",
        "",
        f"Monthly salary: {money(salary)}",
        f"Monthly expenses: {money(expenses)}",
        f"Actual savings: {money(salary - expenses)} ({safe_pct(salary - expenses, salary)}%)",
        f"Total EMI: {money(total_emi)} ({safe_pct(total_emi, salary)}% of salary)",
        f"CL remaining: {leave['remaining_cl'] if leave else 0}",
        f"EL remaining: {leave['remaining_el'] if leave else 0}",
        f"Estimated PF at retirement: {money(pf_estimate)}",
        f"Active insurance policies: {active_policies}",
        f"Estimated yearly premium: {money(yearly_prem)}",
        f"Open reminders: {reminders['total'] if reminders else 0}",
    ]
    if not retirement.empty:
        latest = retirement.iloc[-1]
        lines.append(f"Retirement corpus goal: {money(latest['corpus_goal'])}")
        lines.append(f"Post-retirement expense estimate: {money(latest['post_retirement_expense'])}")

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    for i, line in enumerate(lines):
        pdf.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 14 if i == 0 else 10)
        pdf.drawString(40, y, str(line)[:110])
        y -= 22
        if y < 40:
            pdf.showPage()
            y = 800
    pdf.save()
    return buffer.getvalue()

