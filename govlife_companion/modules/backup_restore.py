from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

import streamlit as st

from database.db import DB_PATH
from utils.translations import t


def render(user: dict) -> None:
    st.title(t("backup_restore"))
    st.caption("Create a local backup of the SQLite database or restore a previous backup.")
    if DB_PATH.exists():
        st.download_button(
            "Download database backup",
            DB_PATH.read_bytes(),
            file_name=f"govlife_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            mime="application/octet-stream",
            use_container_width=True,
        )

    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    if st.button("Create local backup copy", use_container_width=True):
        target = backup_dir / f"govlife_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, target)
        st.success(f"Backup created: {target}")

    st.subheader("Restore database")
    st.warning("Restore replaces the current local database. Restart the app after restore.")
    uploaded = st.file_uploader("Upload .db backup", type=["db"])
    if uploaded and st.button("Restore uploaded backup", use_container_width=True):
        restore_copy = backup_dir / f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DB_PATH, restore_copy)
        DB_PATH.write_bytes(uploaded.getbuffer())
        st.success("Database restored. Please restart Streamlit.")

