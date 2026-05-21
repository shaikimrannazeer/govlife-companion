from __future__ import annotations

import smtplib
from email.message import EmailMessage

import streamlit as st

from database.db import execute, fetch_one, table_df
from utils.translations import t


def _settings(user_id: int) -> dict:
    row = fetch_one("SELECT * FROM notification_settings WHERE user_id=?", (user_id,))
    if row:
        return dict(row)
    execute("INSERT INTO notification_settings (user_id) VALUES (?)", (user_id,))
    return dict(fetch_one("SELECT * FROM notification_settings WHERE user_id=?", (user_id,)))


def _send_email(settings: dict, subject: str, body: str) -> tuple[bool, str]:
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings["sender_email"]
        msg["To"] = settings["receiver_email"]
        msg.set_content(body)
        with smtplib.SMTP(settings["smtp_host"], int(settings["smtp_port"] or 587), timeout=20) as server:
            server.starttls()
            if settings["smtp_username"]:
                server.login(settings["smtp_username"], settings["smtp_password"] or "")
            server.send_message(msg)
        return True, "Email sent."
    except Exception as exc:
        return False, f"Email failed: {exc}"


def render(user: dict) -> None:
    st.title(t("notifications"))
    user_id = user["id"]
    settings = _settings(user_id)
    st.caption("Email sending works with your SMTP details. WhatsApp/SMS numbers are stored for planning and future integrations.")

    with st.form("notification_settings_form"):
        email_enabled = st.checkbox("Enable email notifications", value=bool(settings["email_enabled"]))
        col1, col2 = st.columns(2)
        smtp_host = col1.text_input("SMTP host", value=settings["smtp_host"] or "")
        smtp_port = col2.number_input("SMTP port", value=int(settings["smtp_port"] or 587), min_value=1, max_value=65535)
        smtp_username = col1.text_input("SMTP username", value=settings["smtp_username"] or "")
        smtp_password = col2.text_input("SMTP password/app password", value=settings["smtp_password"] or "", type="password")
        sender = col1.text_input("Sender email", value=settings["sender_email"] or "")
        receiver = col2.text_input("Receiver email", value=settings["receiver_email"] or "")
        whatsapp = col1.text_input("WhatsApp number", value=settings["whatsapp_number"] or "")
        sms = col2.text_input("SMS number", value=settings["sms_number"] or "")
        if st.form_submit_button("Save notification settings", use_container_width=True):
            execute(
                """UPDATE notification_settings
                SET email_enabled=?, smtp_host=?, smtp_port=?, smtp_username=?, smtp_password=?,
                    sender_email=?, receiver_email=?, whatsapp_number=?, sms_number=?, updated_at=CURRENT_TIMESTAMP
                WHERE user_id=?""",
                (int(email_enabled), smtp_host, smtp_port, smtp_username, smtp_password, sender, receiver, whatsapp, sms, user_id),
            )
            st.success("Notification settings saved.")

    st.subheader("Send upcoming reminder email")
    reminders = table_df("reminders", user_id)
    pending = reminders[reminders["status"] != "Completed"] if not reminders.empty else reminders
    if pending.empty:
        st.info("No pending reminders.")
    else:
        text = "\n".join(f"- {r['reminder_date']}: {r['title']} ({r['category']})" for _, r in pending.head(20).iterrows())
        st.text_area("Message preview", text, height=180)
        if st.button("Send reminder email", use_container_width=True):
            settings = _settings(user_id)
            if not settings["email_enabled"]:
                st.warning("Enable email notifications first.")
            else:
                ok, message = _send_email(settings, "GovLife upcoming reminders", text)
                execute(
                    "INSERT INTO notification_log (user_id, channel, title, message, status) VALUES (?, ?, ?, ?, ?)",
                    (user_id, "Email", "GovLife upcoming reminders", text, "Sent" if ok else "Failed"),
                )
                st.success(message) if ok else st.error(message)

    logs = table_df("notification_log", user_id)
    if not logs.empty:
        st.subheader("Notification log")
        st.dataframe(logs.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)

