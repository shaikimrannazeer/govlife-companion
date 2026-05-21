from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import streamlit as st


EXPENSE_CATEGORIES = [
    "Food", "Rent", "EMI", "Children education", "Medical", "Travel", "Shopping",
    "Parents support", "Bills", "Insurance", "Other",
]

LOAN_TYPES = ["Home loan", "Vehicle loan", "Personal loan", "Gold loan", "Education loan", "Other"]

DOCUMENT_TYPES = [
    "Aadhaar", "PAN", "Passport", "Voter ID", "Salary slips", "Pension papers",
    "Insurance papers", "Property documents", "Children school certificates",
    "Medical reports", "Bank documents", "Service records", "Nominee forms",
]

REMINDER_CATEGORIES = [
    "EMI", "Insurance renewal", "School fees", "Medicine", "Doctor appointment",
    "Document expiry", "Pension paperwork", "Tax filing", "Bills", "Family events",
    "PF nomination check", "PF yearly check", "Insurance premium", "Insurance maturity", "Custom",
]

INSURANCE_TYPES = [
    "Health insurance", "Life insurance", "Term insurance", "Vehicle insurance",
    "Home insurance", "Accident insurance", "Other insurance",
]


def load_css() -> None:
    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def money(value: float | int | None) -> str:
    value = float(value or 0)
    return "₹{:,.0f}".format(value)


def parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def days_until(value) -> int | None:
    dt = parse_date(value)
    if not dt:
        return None
    return (dt - date.today()).days


def card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""<div class="gov-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div>{note}</div>
        </div>""",
        unsafe_allow_html=True,
    )
