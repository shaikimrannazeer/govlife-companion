from __future__ import annotations

from datetime import date

import streamlit as st

from database.db import execute, table_df
from utils.helpers import money
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("trip_planner"))
    user_id = user["id"]
    with st.form("trip_form"):
        col1, col2, col3 = st.columns(3)
        destination = col1.text_input("Destination")
        people = col2.number_input("Number of people", min_value=1, value=1)
        leave = col3.number_input("Leave balance", min_value=0.0, step=0.5)
        start = col1.date_input("Travel start date", value=date.today())
        end = col2.date_input("Travel end date", value=date.today())
        packing = col3.text_input("Packing checklist item")
        hotel = col1.number_input("Hotel budget", min_value=0.0, step=1000.0)
        food = col2.number_input("Food budget", min_value=0.0, step=1000.0)
        transport = col3.number_input("Transport budget", min_value=0.0, step=1000.0)
        other = st.number_input("Other budget", min_value=0.0, step=1000.0)
        packed = st.checkbox("Packing item completed")
        if st.form_submit_button("Add trip plan"):
            execute(
                """INSERT INTO trips (user_id, destination, people, start_date, end_date, hotel_budget,
                food_budget, transport_budget, other_budget, leave_balance, packing_item, packed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, destination, int(people), start.isoformat(), end.isoformat(), hotel, food, transport, other, leave, packing, int(packed)),
            )
            st.success("Trip plan added.")
    df = table_df("trips", user_id)
    if df.empty:
        st.info("No trips planned yet.")
        return
    total = df[["hotel_budget", "food_budget", "transport_budget", "other_budget"]].sum().sum()
    people = max(1, int(df["people"].sum()))
    c1, c2, c3 = st.columns(3)
    c1.metric("Trip budget summary", money(total))
    c2.metric("Per person cost", money(total / people))
    c3.metric("Savings required before trip", money(total))
    st.dataframe(df, use_container_width=True, hide_index=True)
