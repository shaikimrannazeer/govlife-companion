from __future__ import annotations

from datetime import date

from utils.helpers import parse_date


BUDGET_ALLOCATION_RULE = {
    "Food and groceries": 15,
    "House rent / maintenance": 15,
    "Bills and utilities": 8,
    "Transport": 7,
    "Medical and health": 5,
    "Children education": 10,
    "EMI / loans": 20,
    "Savings / investment": 20,
    "Personal shopping / lifestyle": 5,
    "Emergency fund": 5,
}

BUDGET_CATEGORY_MAP = {
    "Food and groceries": ["Food"],
    "House rent / maintenance": ["Rent"],
    "Bills and utilities": ["Bills", "Insurance"],
    "Transport": ["Travel"],
    "Medical and health": ["Medical"],
    "Children education": ["Children education"],
    "EMI / loans": ["EMI"],
    "Savings / investment": [],
    "Personal shopping / lifestyle": ["Shopping"],
    "Emergency fund": [],
}


def safe_pct(part: float, total: float) -> float:
    return round((part / total) * 100, 1) if total else 0


def budget_health_score(income: float, expenses: float, emi: float) -> int:
    if income <= 0:
        return 0
    savings_pct = max(0, (income - expenses) / income) * 100
    emi_pct = emi / income * 100
    score = 50 + min(savings_pct, 30) - max(0, emi_pct - 25) - max(0, expenses - income) / income * 40
    return int(max(0, min(100, score)))


def months_until(value) -> int:
    dt = parse_date(value)
    if not dt:
        return 0
    today = date.today()
    return max(0, (dt.year - today.year) * 12 + dt.month - today.month)


def retirement_score(corpus: float, goal: float, pension: float, expense: float) -> int:
    corpus_score = min(60, (corpus / goal) * 60) if goal else 20
    pension_score = min(40, (pension / expense) * 40) if expense else 20
    return int(max(0, min(100, corpus_score + pension_score)))


def loan_progress(original: float, remaining: float) -> float:
    if not original:
        return 0
    return max(0, min(100, (original - remaining) / original * 100))


def recommended_budget(salary: float) -> tuple[list[dict], bool]:
    raw_total = sum(BUDGET_ALLOCATION_RULE.values())
    needs_adjustment = raw_total > 100
    scale = 100 / raw_total if needs_adjustment else 1
    rows = []
    for category, pct in BUDGET_ALLOCATION_RULE.items():
        adjusted_pct = pct * scale
        rows.append(
            {
                "Category": category,
                "Rule %": pct,
                "Adjusted %": round(adjusted_pct, 2),
                "Recommended amount": round(float(salary or 0) * adjusted_pct / 100, 2),
            }
        )
    return rows, needs_adjustment


def budget_status(category: str, actual: float, recommended: float) -> str:
    if category in {"Savings / investment", "Emergency fund"}:
        if actual >= recommended:
            return "Good"
        if actual >= recommended * 0.75:
            return "Warning"
        return "Danger"
    if actual <= recommended:
        return "Good"
    if actual <= recommended * 1.15:
        return "Warning"
    return "Danger"
