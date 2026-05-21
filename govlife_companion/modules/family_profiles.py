from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from database.db import execute, table_df
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("family_profiles"))
    user_id = user["id"]
    with st.form("family_profile_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Name")
        relation = col2.text_input("Relation")
        dob = col1.date_input("Date of birth", value=date(2000, 1, 1))
        notes = st.text_area("Notes")
        if st.form_submit_button("Add family profile", use_container_width=True):
            execute(
                "INSERT INTO family_members (user_id, name, relation, date_of_birth, notes) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, relation, dob.isoformat(), notes),
            )
            st.success("Family profile added.")

    members = table_df("family_members", user_id)
    health = table_df("health_records", user_id)
    education = table_df("education", user_id)
    insurance = table_df("insurance_policies", user_id)
    if members.empty:
        st.info("Add family members to see linked health, education, and insurance details.")
        return

    for _, member in members.iterrows():
        with st.expander(f"{member['name']} - {member['relation']}", expanded=False):
            st.write(member["notes"] or "")
            h = health[health["member_name"].astype(str).str.lower() == str(member["name"]).lower()] if not health.empty else pd.DataFrame()
            e = education[education["child_name"].astype(str).str.lower() == str(member["name"]).lower()] if not education.empty else pd.DataFrame()
            ins = insurance[insurance["insured_person_name"].astype(str).str.lower() == str(member["name"]).lower()] if not insurance.empty else pd.DataFrame()
            c1, c2, c3 = st.columns(3)
            c1.metric("Health records", len(h))
            c2.metric("Education plans", len(e))
            c3.metric("Insurance policies", len(ins))
            if not h.empty:
                st.caption("Health")
                st.dataframe(h.tail(5), use_container_width=True, hide_index=True)
            if not e.empty:
                st.caption("Education")
                st.dataframe(e.tail(5), use_container_width=True, hide_index=True)
            if not ins.empty:
                st.caption("Insurance")
                st.dataframe(ins.tail(5), use_container_width=True, hide_index=True)

