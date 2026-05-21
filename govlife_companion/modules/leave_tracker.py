from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import execute, fetch_one, table_df
from utils.translations import t


def _balance(user_id: int) -> dict:
    row = fetch_one("SELECT * FROM leave_balance WHERE user_id=?", (user_id,))
    if row:
        return dict(row)
    execute(
        """INSERT INTO leave_balance
        (user_id, total_cl, used_cl, remaining_cl, total_el, used_el, remaining_el)
        VALUES (?, 0, 0, 0, 0, 0, 0)""",
        (user_id,),
    )
    return dict(fetch_one("SELECT * FROM leave_balance WHERE user_id=?", (user_id,)))


def _save_totals(user_id: int, total_cl: float, used_cl: float, total_el: float, used_el: float) -> None:
    execute(
        """UPDATE leave_balance
        SET total_cl=?, used_cl=?, remaining_cl=?, total_el=?, used_el=?, remaining_el=?, updated_at=CURRENT_TIMESTAMP
        WHERE user_id=?""",
        (total_cl, used_cl, max(0, total_cl - used_cl), total_el, used_el, max(0, total_el - used_el), user_id),
    )


def _add_leave(user_id: int, leave_type: str, from_date: date, to_date: date, days: float, reason: str, status: str) -> None:
    bal = _balance(user_id)
    available = bal["remaining_cl"] if leave_type == "CL" else bal["remaining_el"]
    if days > available:
        st.error(f"You cannot apply {days:g} {leave_type} days. Available balance is {available:g}.")
        return
    execute(
        """INSERT INTO leave_records (user_id, leave_type, from_date, to_date, days, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, leave_type, from_date.isoformat(), to_date.isoformat(), days, reason, status),
    )
    if leave_type == "CL":
        used = bal["used_cl"] + days
        _save_totals(user_id, bal["total_cl"], used, bal["total_el"], bal["used_el"])
    else:
        used = bal["used_el"] + days
        _save_totals(user_id, bal["total_cl"], bal["used_cl"], bal["total_el"], used)
    st.success(f"{leave_type} leave saved.")


def render(user: dict) -> None:
    st.title(t("leave_tracker"))
    user_id = user["id"]
    bal = _balance(user_id)

    with st.form("leave_balance_form"):
        st.subheader("Yearly leave balance")
        col1, col2, col3, col4 = st.columns(4)
        total_cl = col1.number_input("Total CL allowed", min_value=0.0, value=float(bal["total_cl"]), step=1.0)
        used_cl = col2.number_input("CL taken", min_value=0.0, value=float(bal["used_cl"]), step=1.0)
        total_el = col3.number_input("Total EL available", min_value=0.0, value=float(bal["total_el"]), step=1.0)
        used_el = col4.number_input("EL taken", min_value=0.0, value=float(bal["used_el"]), step=1.0)
        if st.form_submit_button("Update leave balance", use_container_width=True):
            if used_cl > total_cl:
                st.error("CL taken cannot be more than Total CL allowed.")
            elif used_el > total_el:
                st.error("EL taken cannot be more than Total EL available.")
            else:
                _save_totals(user_id, total_cl, used_cl, total_el, used_el)
                st.success("Leave balance updated.")
                st.rerun()

    bal = _balance(user_id)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total CL", f"{bal['total_cl']:g}")
    c2.metric("CL taken", f"{bal['used_cl']:g}")
    c3.metric("CL remaining", f"{bal['remaining_cl']:g}")
    c4.metric("Total EL", f"{bal['total_el']:g}")
    c5.metric("EL taken", f"{bal['used_el']:g}")
    c6.metric("EL remaining", f"{bal['remaining_el']:g}")

    if bal["remaining_cl"] == 0:
        st.warning("No CL left.")
    if bal["remaining_el"] < 5:
        st.warning("EL balance is low.")

    cl_tab, el_tab = st.tabs(["Apply CL", "Apply EL"])
    with cl_tab:
        with st.form("cl_form"):
            cl_date = st.date_input("Date of CL taken", value=date.today())
            cl_days = st.number_input("CL days", min_value=0.5, value=1.0, step=0.5)
            cl_reason = st.text_area("Reason", key="cl_reason")
            cl_status = st.selectbox("Status", ["Approved", "Pending", "Rejected"], key="cl_status")
            if st.form_submit_button("Save CL"):
                _add_leave(user_id, "CL", cl_date, cl_date, cl_days, cl_reason, cl_status)
                st.rerun()

    with el_tab:
        with st.form("el_form"):
            col1, col2 = st.columns(2)
            from_date = col1.date_input("Date from", value=date.today())
            to_date = col2.date_input("Date to", value=date.today())
            default_days = max(1, (to_date - from_date).days + 1)
            el_days = st.number_input("Number of days", min_value=0.5, value=float(default_days), step=0.5)
            el_reason = st.text_area("Reason", key="el_reason")
            el_status = st.selectbox("Status", ["Approved", "Pending", "Rejected"], key="el_status")
            if st.form_submit_button("Save EL"):
                if to_date < from_date:
                    st.error("To date cannot be before From date.")
                else:
                    _add_leave(user_id, "EL", from_date, to_date, el_days, el_reason, el_status)
                    st.rerun()

    st.subheader("Leave charts")
    chart_df = pd.DataFrame(
        [
            {"Leave": "CL", "Status": "Used", "Days": bal["used_cl"]},
            {"Leave": "CL", "Status": "Remaining", "Days": bal["remaining_cl"]},
            {"Leave": "EL", "Status": "Used", "Days": bal["used_el"]},
            {"Leave": "EL", "Status": "Remaining", "Days": bal["remaining_el"]},
        ]
    )
    col1, col2 = st.columns(2)
    col1.plotly_chart(px.pie(chart_df[chart_df["Leave"] == "CL"], names="Status", values="Days", title="CL used vs remaining"), use_container_width=True)
    col2.plotly_chart(px.pie(chart_df[chart_df["Leave"] == "EL"], names="Status", values="Days", title="EL used vs remaining"), use_container_width=True)

    records = table_df("leave_records", user_id)
    st.subheader("Leave history")
    if records.empty:
        st.info("No leave history yet.")
        return

    records["month"] = pd.to_datetime(records["from_date"]).dt.strftime("%Y-%m")
    trend = records.groupby(["month", "leave_type"], as_index=False)["days"].sum()
    st.plotly_chart(px.line(trend, x="month", y="days", color="leave_type", markers=True, title="Monthly leave usage trend"), use_container_width=True)

    col1, col2 = st.columns(2)
    type_filter = col1.multiselect("Filter by leave type", ["CL", "EL"])
    status_filter = col2.multiselect("Filter by status", ["Approved", "Pending", "Rejected"])
    view = records.copy()
    if type_filter:
        view = view[view["leave_type"].isin(type_filter)]
    if status_filter:
        view = view[view["status"].isin(status_filter)]
    view = view.rename(
        columns={
            "leave_type": "Leave type",
            "from_date": "From date",
            "to_date": "To date",
            "days": "Days",
            "reason": "Reason",
            "status": "Status",
            "created_at": "Created date",
        }
    )
    st.dataframe(
        view[["Leave type", "From date", "To date", "Days", "Reason", "Status", "Created date"]],
        use_container_width=True,
        hide_index=True,
    )
