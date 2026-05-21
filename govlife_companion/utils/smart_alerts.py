from __future__ import annotations

from datetime import date

from database.db import fetch_all, fetch_one, table_df
from modules.insurance_tracker import yearly_premium
from utils.calculations import months_until, safe_pct
from utils.helpers import money


def collect_smart_alerts(user: dict) -> list[dict]:
    user_id = user["id"]
    alerts: list[dict] = []
    salary_row = fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM salary WHERE user_id=? AND month=strftime('%Y-%m','now')", (user_id,))
    salary = salary_row["total"] or float(user.get("monthly_salary") or 0)
    expenses_row = fetch_one("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=strftime('%Y-%m','now')", (user_id,))
    expenses = expenses_row["total"] or 0
    emi_row = fetch_one("SELECT COALESCE(SUM(emi_amount), 0) AS total FROM loans WHERE user_id=? AND remaining_balance > 0", (user_id,))
    emi = emi_row["total"] or 0
    leave = fetch_one("SELECT * FROM leave_balance WHERE user_id=?", (user_id,))
    pf = fetch_one("SELECT * FROM pf_tracker WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    insurance = table_df("insurance_policies", user_id)
    retirement = table_df("retirement", user_id)

    if salary and emi / salary > 0.40:
        alerts.append({"Level": "Danger", "Area": "EMI", "Message": f"EMI is {safe_pct(emi, salary)}% of salary. Avoid new loans."})
    if salary and (salary - expenses) / salary < 0.20:
        alerts.append({"Level": "Warning", "Area": "Savings", "Message": "Savings are below 20%. Review variable spending."})
    if expenses > salary:
        alerts.append({"Level": "Danger", "Area": "Budget", "Message": "Expenses are higher than income."})
    if leave:
        if leave["remaining_cl"] <= 0:
            alerts.append({"Level": "Warning", "Area": "Leave", "Message": "No CL left."})
        if leave["remaining_el"] < 5:
            alerts.append({"Level": "Warning", "Area": "Leave", "Message": "EL balance is low."})
    if pf and not pf["nominee_name"]:
        alerts.append({"Level": "Warning", "Area": "PF", "Message": "PF nominee name is missing. Check nomination."})
    if pf and months_until(pf["retirement_date"]) <= 60:
        alerts.append({"Level": "Warning", "Area": "PF", "Message": "Retirement is within 5 years. Check PF nomination and service records."})
    if not insurance.empty:
        renewal_dates = __import__("pandas").to_datetime(insurance["renewal_date"], errors="coerce")
        soon = (renewal_dates >= __import__("pandas").Timestamp(date.today())) & (renewal_dates <= __import__("pandas").Timestamp(date.today()) + __import__("pandas").Timedelta(days=30))
        if soon.any():
            alerts.append({"Level": "Warning", "Area": "Insurance", "Message": "Insurance renewal is due within 30 days."})
        if ((insurance["status"] == "Expired") | (renewal_dates < __import__("pandas").Timestamp(date.today()))).any():
            alerts.append({"Level": "Danger", "Area": "Insurance", "Message": "One or more policies are expired."})
    if not retirement.empty:
        latest = retirement.iloc[-1]
        corpus = latest["pf_nps_savings"] + latest["gratuity_estimate"]
        if latest["corpus_goal"] and corpus < latest["corpus_goal"] * 0.70:
            alerts.append({"Level": "Warning", "Area": "Retirement", "Message": f"Retirement savings gap is high. Current estimate: {money(corpus)}."})
    stale_health = fetch_all("SELECT MAX(record_date) AS last_record FROM health_records WHERE user_id=?", (user_id,))
    if not stale_health or not stale_health[0]["last_record"]:
        alerts.append({"Level": "Info", "Area": "Health", "Message": "No recent health record found."})
    return alerts or [{"Level": "Good", "Area": "Overall", "Message": "No urgent alerts found."}]

