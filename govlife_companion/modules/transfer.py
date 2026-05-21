from __future__ import annotations

import streamlit as st

from database.db import execute, table_df
from utils.translations import t

CHECKLIST = [
    "Apply for transfer documents", "Collect service records", "Update address",
    "Find rental house", "Transfer children's school", "Update bank branch if needed",
    "Shift gas connection", "Update Aadhaar address", "Move household items",
    "Save emergency contacts",
]


def render(user: dict) -> None:
    st.title(t("transfer_life_manager"))
    user_id = user["id"]
    with st.form("transfer_form"):
        col1, col2 = st.columns(2)
        city = col1.text_input("New city")
        rent = col2.number_input("Rent estimate", min_value=0.0, step=1000.0)
        item = col1.selectbox("Checklist item", CHECKLIST)
        category = col2.selectbox("Category", ["Office", "Home", "School", "Travel", "Documents", "Contacts"])
        notes = st.text_area("Important contacts / travel notes")
        done = st.checkbox("Completed")
        if st.form_submit_button("Save checklist item"):
            execute(
                "INSERT INTO transfers (user_id, item, city, rent_estimate, category, completed, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, item, city, rent, category, int(done), notes),
            )
            st.success("Transfer item saved.")
    df = table_df("transfers", user_id)
    if df.empty:
        st.info("Add your first transfer checklist item.")
        return
    st.progress(int(df["completed"].mean() * 100), text="Checklist completion")
    st.dataframe(df, use_container_width=True, hide_index=True)
