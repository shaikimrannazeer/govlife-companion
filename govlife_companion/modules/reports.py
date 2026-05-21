from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st

from database.db import fetch_one, table_df
from modules.budget import build_budget_comparison
from modules.insurance_tracker import yearly_premium
from utils.monthly_report import build_monthly_report_pdf
from utils.helpers import money
from utils.translations import t

REPORTS = {
    "Salary budget recommendation report": "salary_budget",
    "Actual spending comparison report": "spending_comparison",
    "CL/EL leave report": "leave_records",
    "EMI safety report": "emi_safety",
    "PF report": "pf_tracker",
    "Insurance report": "insurance_policies",
    "Upcoming insurance renewal report": "upcoming_insurance_renewal",
    "Yearly premium report": "yearly_premium",
    "Loan report": "loans",
    "Health tracking report": "health_records",
    "Retirement readiness report": "retirement",
    "Reminder report": "reminders",
}


def _report_df(report_key: str, user: dict) -> pd.DataFrame:
    user_id = user["id"]
    expenses = table_df("expenses", user_id)
    if not expenses.empty:
        current_month = date.today().strftime("%Y-%m")
        expenses = expenses[pd.to_datetime(expenses["expense_date"]).dt.strftime("%Y-%m") == current_month]
    salary_row = fetch_one(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM salary WHERE user_id=? AND month=strftime('%Y-%m','now')",
        (user_id,),
    )
    salary = salary_row["total"] or float(user.get("monthly_salary") or 0)

    if report_key in {"salary_budget", "spending_comparison"}:
        comparison, adjusted = build_budget_comparison(salary, expenses)
        df = pd.DataFrame(comparison)
        df["Rule adjusted"] = "Yes" if adjusted else "No"
        return df

    if report_key == "emi_safety":
        loans = table_df("loans", user_id)
        total_emi = loans["emi_amount"].sum() if not loans.empty else 0
        ratio = (total_emi / salary * 100) if salary else 0
        status = "Danger" if ratio > 40 else "Warning" if ratio > 20 else "Good"
        return pd.DataFrame(
            [
                {
                    "Monthly salary": money(salary),
                    "Total EMI": money(total_emi),
                    "EMI ratio": f"{ratio:.1f}%",
                    "Status": status,
                    "Suggestion": "Avoid taking new loans." if ratio > 20 else "EMI is within a safer range.",
                }
            ]
        )

    if report_key == "upcoming_insurance_renewal":
        policies = table_df("insurance_policies", user_id)
        if policies.empty:
            return policies
        renewal_dates = pd.to_datetime(policies["renewal_date"], errors="coerce")
        today = pd.Timestamp(date.today())
        return policies[(renewal_dates >= today) & (renewal_dates <= today + pd.Timedelta(days=30))]

    if report_key == "yearly_premium":
        policies = table_df("insurance_policies", user_id)
        if policies.empty:
            return policies
        policies = policies.copy()
        policies["yearly_premium"] = policies.apply(lambda r: yearly_premium(r["premium_amount"], r["premium_frequency"]), axis=1)
        return policies.groupby("insurance_type", as_index=False).agg(
            total_yearly_premium=("yearly_premium", "sum"),
            policy_count=("id", "count"),
            total_coverage=("sum_assured", "sum"),
        )

    return table_df(report_key, user_id)


def render(user: dict) -> None:
    st.title(t("reports"))
    st.subheader("Monthly auto report")
    pdf_bytes = build_monthly_report_pdf(user)
    st.download_button(
        "Download monthly PDF report",
        pdf_bytes,
        file_name=f"govlife_monthly_report_{date.today().isoformat()}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.divider()
    report_name = st.selectbox("Choose report", list(REPORTS))
    df = _report_df(REPORTS[report_name], user)
    if df.empty:
        st.info("No records found for this report.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(t("download_csv"), csv, file_name=f"{report_name.lower().replace(' ', '_')}.csv", mime="text/csv")

    st.caption("Simple PDF export")
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.drawString(40, 800, report_name)
        y = 770
        for line in df.head(25).astype(str).to_string(index=False).splitlines():
            pdf.drawString(40, y, line[:100])
            y -= 14
            if y < 40:
                pdf.showPage()
                y = 800
        pdf.save()
        st.download_button("Download PDF", buffer.getvalue(), file_name=f"{report_name}.pdf", mime="application/pdf")
    except Exception:
        st.info("Install reportlab if you want PDF report export. CSV export is ready.")
