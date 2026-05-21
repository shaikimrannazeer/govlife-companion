from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from utils.security import hash_password
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "govlife.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _run_migrations(conn)
        _seed_demo_data(conn)


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return int(cur.lastrowid)


def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(sql, params).fetchone()


def table_df(table: str, user_id: int | None = None):
    import pandas as pd

    allowed = {
        "users", "salary", "expenses", "loans", "family_members",
        "health_records", "education", "transfers", "trips", "retirement",
        "reminders", "ai_chat_history", "admin_settings", "leave_records", "leave_balance",
        "pf_tracker", "insurance_policies", "notification_settings", "notification_log",
    }
    if table not in allowed:
        raise ValueError("Unknown table")
    where = " WHERE user_id = ?" if user_id is not None and table != "users" else ""
    params = (user_id,) if where else ()
    with get_connection() as conn:
        return pd.read_sql_query(f"SELECT * FROM {table}{where}", conn, params=params)


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in cols)


def _run_migrations(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "ai_chat_history", "chat_id"):
        conn.execute("ALTER TABLE ai_chat_history ADD COLUMN chat_id TEXT")
    if not _column_exists(conn, "users", "preferred_language"):
        conn.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT DEFAULT 'English'")
    conn.commit()


def _seed_demo_data(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing:
        return

    user_hash = hash_password("demo123")
    admin_hash = hash_password("admin123")
    conn.execute(
        """INSERT INTO users
        (full_name, login_id, password_hash, role, department, job_type,
         date_of_joining, expected_retirement_date, monthly_salary, city, family_size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("Demo Employee", "demo@govlife.in", user_hash, "user", "Revenue Department",
         "Clerk", "2012-07-01", "2042-06-30", 65000, "Hyderabad", 4),
    )
    conn.execute(
        """INSERT INTO users
        (full_name, login_id, password_hash, role, department, job_type,
         date_of_joining, expected_retirement_date, monthly_salary, city, family_size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("GovLife Admin", "admin@govlife.in", admin_hash, "admin", "Administration",
         "Admin", "2010-01-01", "2040-01-01", 90000, "Delhi", 3),
    )
    user_id = 1
    conn.executemany(
        "INSERT INTO salary (user_id, month, amount, source, notes) VALUES (?, ?, ?, ?, ?)",
        [(user_id, "2026-05", 65000, "Monthly salary", "Demo salary"),
         (user_id, "2026-04", 64000, "Monthly salary", "Demo salary")],
    )
    conn.executemany(
        """INSERT INTO expenses (user_id, expense_date, category, amount, expense_type, notes)
        VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (user_id, "2026-05-05", "Food", 12000, "Variable", "Groceries"),
            (user_id, "2026-05-07", "EMI", 18000, "Fixed", "Home loan EMI"),
            (user_id, "2026-05-10", "Children education", 9000, "Fixed", "School fees"),
            (user_id, "2026-05-12", "Bills", 4500, "Fixed", "Power and mobile"),
        ],
    )
    conn.execute(
        """INSERT INTO loans (user_id, loan_type, bank_name, loan_amount, interest_rate,
        emi_amount, start_date, end_date, remaining_balance, due_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, "Home loan", "SBI", 2200000, 8.5, 18000, "2020-01-01", "2035-01-01", 1650000, 7),
    )
    conn.execute(
        """INSERT INTO reminders (user_id, title, category, reminder_date, repeat_type, priority, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, "Home loan EMI", "EMI", "2026-05-25", "Monthly", "High", "Pending", "Keep balance ready"),
    )
    conn.execute(
        """INSERT INTO leave_balance
        (user_id, total_cl, used_cl, remaining_cl, total_el, used_el, remaining_el)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, 12, 5, 7, 30, 8, 22),
    )
    conn.executemany(
        """INSERT INTO leave_records
        (user_id, leave_type, from_date, to_date, days, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            (user_id, "CL", "2026-05-03", "2026-05-03", 1, "Family work", "Approved"),
            (user_id, "EL", "2026-06-10", "2026-06-14", 5, "Family trip", "Pending"),
        ],
    )
    conn.commit()
