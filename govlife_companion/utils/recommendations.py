from __future__ import annotations

from database.db import fetch_all


def build_recommendations(user_id: int, income: float, expenses: float, emi: float) -> list[str]:
    items: list[str] = []
    if income and (income - expenses) / income < 0.20:
        items.append("Savings are below 20%. Review shopping, travel, and other variable expenses this month.")
    if income and emi / income > 0.40:
        items.append("EMI is above 40% of income. Avoid taking new loans until the ratio improves.")
    if expenses > income:
        items.append("Expenses are higher than income. Prepare a strict monthly budget immediately.")

    fees = fetch_all(
        "SELECT child_name, fee_due_date FROM education WHERE user_id=? AND fee_due_date BETWEEN date('now') AND date('now', '+10 day')",
        (user_id,),
    )
    for fee in fees:
        items.append(f"School or college fee for {fee['child_name']} is due on {fee['fee_due_date']}.")

    health = fetch_all(
        "SELECT MAX(record_date) AS last_record FROM health_records WHERE user_id=?",
        (user_id,),
    )
    if not health or not health[0]["last_record"]:
        items.append("No recent health record found. Add a basic BP, sugar, and weight checkup.")
    leave = fetch_all(
        "SELECT remaining_cl, remaining_el FROM leave_balance WHERE user_id=?",
        (user_id,),
    )
    if leave:
        if leave[0]["remaining_cl"] == 0:
            items.append("No CL left. Use EL or adjust leave plans carefully.")
        if leave[0]["remaining_el"] < 5:
            items.append("EL balance is low. Keep longer leave plans for important needs.")
    return items or ["Your core indicators look stable. Keep updating salary, expenses, reminders, leave, and health records monthly."]
