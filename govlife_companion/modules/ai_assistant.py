from __future__ import annotations

import os
import uuid

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from database.db import execute, fetch_all, fetch_one, table_df
from utils.helpers import money
from utils.pdf_reader import extract_pdf_text
from utils.translations import language_code, t

try:
    from streamlit_mic_recorder import speech_to_text
except Exception:
    speech_to_text = None

load_dotenv()

SYSTEM_PROMPT = """
You are GovLife AI Assistant, a simple and practical personal life assistant for Indian government employees.
Help with salary planning, monthly budget, EMI control, CL and EL leave tracking, retirement planning,
family planning, health reminders, and trip planning.
You can also help users with PF tracking, PF retirement estimates, insurance premium tracking,
renewal planning, nominee reminders, and insurance checklist.
Keep answers simple, step-by-step, and practical.
Do not give medical diagnosis, legal guarantee, or official pension guarantee.
Do not guarantee official PF or insurance values.
For official government rules, tell the user to verify with their department.
Tell users to verify final PF and insurance numbers with the official PF portal, insurance company, or department.
"""


def _client() -> OpenAI | None:
    key = st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def _ensure_chat_state() -> None:
    if "govlife_chat_id" not in st.session_state:
        st.session_state.govlife_chat_id = str(uuid.uuid4())
    if "govlife_chat_messages" not in st.session_state:
        st.session_state.govlife_chat_messages = []


def _save_message(user_id: int, role: str, message: str) -> None:
    execute(
        "INSERT INTO ai_chat_history (user_id, chat_id, role, message) VALUES (?, ?, ?, ?)",
        (user_id, st.session_state.govlife_chat_id, role, message),
    )


def _app_context(user: dict) -> str:
    user_id = user["id"]
    salary_row = fetch_one(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM salary WHERE user_id=? AND month=strftime('%Y-%m','now')",
        (user_id,),
    )
    salary = salary_row["total"] or float(user.get("monthly_salary") or 0)
    expenses = table_df("expenses", user_id)
    loans = table_df("loans", user_id)
    leave = fetch_one("SELECT * FROM leave_balance WHERE user_id=?", (user_id,))
    retirement = table_df("retirement", user_id)
    trips = table_df("trips", user_id)
    pf = table_df("pf_tracker", user_id)
    insurance = table_df("insurance_policies", user_id)
    health = fetch_one("SELECT MAX(reminder_date) AS medicine_due, MAX(checkup_date) AS checkup_due FROM health_records WHERE user_id=?", (user_id,))

    total_expenses = expenses["amount"].sum() if not expenses.empty else 0
    total_emi = loans["emi_amount"].sum() if not loans.empty else 0
    latest_retirement = retirement.iloc[-1].to_dict() if not retirement.empty else {}
    trip_summary = trips.tail(3).to_dict("records") if not trips.empty else []
    latest_pf = pf.iloc[-1].to_dict() if not pf.empty else {}
    insurance_summary = insurance.tail(5).to_dict("records") if not insurance.empty else []
    yearly_premium = 0
    if not insurance.empty:
        multipliers = {"Monthly": 12, "Quarterly": 4, "Half-yearly": 2, "Yearly": 1, "One-time": 0}
        yearly_premium = sum(float(row["premium_amount"] or 0) * multipliers.get(row["premium_frequency"], 1) for _, row in insurance.iterrows())

    return f"""
User profile:
- Name: {user.get('full_name')}
- Department: {user.get('department')}
- City: {user.get('city')}
- Family size: {user.get('family_size')}

Current app data:
- Monthly salary: {money(salary)}
- Monthly expenses: {money(total_expenses)}
- Actual savings: {money(salary - total_expenses)}
- Total EMI: {money(total_emi)}
- EMI ratio: {(total_emi / salary * 100) if salary else 0:.1f}%
- CL remaining: {leave['remaining_cl'] if leave else 0}
- EL remaining: {leave['remaining_el'] if leave else 0}
- Retirement data: {latest_retirement}
- PF tracker data: {latest_pf}
- Insurance policies: {insurance_summary}
- Estimated yearly insurance premium: {money(yearly_premium)}
- Recent trip plans: {trip_summary}
- Health reminders: medicine due {health['medicine_due'] if health else 'not set'}, checkup due {health['checkup_due'] if health else 'not set'}
"""


def ask_ai(messages: list[dict], context: str = "") -> str:
    client = _client()
    if not client:
        return "OpenAI API key is not configured. Please enter your key in the AI Assistant page."
    selected_language = st.session_state.get("language", "English")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    f"The user selected this app language: {selected_language}. "
                    "Always answer in that language unless the user asks for another language. "
                    "If selected language is Roman Hindi, write Hindi/Urdu style language using English letters."
                ),
            },
            {"role": "system", "content": f"Use this app data when relevant:\n{context}"},
            *messages,
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or ""


def _api_key_box() -> None:
    with st.expander(t("openai_api_key"), expanded=not bool(st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY"))):
        st.caption("Your key is used only for this Streamlit session. It is not saved in the database or hardcoded.")
        key_input = st.text_input(
            t("enter_openai_key"),
            type="password",
            placeholder="sk-...",
            value=st.session_state.get("openai_api_key", ""),
        )
        col1, col2 = st.columns(2)
        if col1.button(t("use_this_key"), use_container_width=True):
            if key_input.strip():
                st.session_state.openai_api_key = key_input.strip()
                st.success("API key added for this session.")
            else:
                st.warning("Please enter an API key.")
        if col2.button(t("clear_session_key"), use_container_width=True):
            st.session_state.pop("openai_api_key", None)
            st.info("Session API key cleared.")
        if os.getenv("OPENAI_API_KEY") and not st.session_state.get("openai_api_key"):
            st.info("Using OPENAI_API_KEY from .env as fallback.")


def _chat_controls(user_id: int) -> None:
    col1, col2, col3 = st.columns(3)
    if col1.button(t("new_chat"), use_container_width=True):
        st.session_state.govlife_chat_id = str(uuid.uuid4())
        st.session_state.govlife_chat_messages = []
        st.rerun()
    if col2.button(t("clear_chat"), use_container_width=True):
        execute("DELETE FROM ai_chat_history WHERE user_id=? AND chat_id=?", (user_id, st.session_state.govlife_chat_id))
        st.session_state.govlife_chat_messages = []
        st.rerun()
    if col3.button(t("save_chat"), use_container_width=True):
        execute("DELETE FROM ai_chat_history WHERE user_id=? AND chat_id=?", (user_id, st.session_state.govlife_chat_id))
        for msg in st.session_state.govlife_chat_messages:
            _save_message(user_id, msg["role"], msg["content"])
        st.success("Chat saved.")


def _add_quick_prompt(text: str) -> None:
    st.session_state.voice_prompt_text = text


def _quick_actions(user: dict) -> None:
    st.subheader("AI quick actions")
    col1, col2, col3 = st.columns(3)
    if col1.button("Plan monthly budget", use_container_width=True):
        _add_quick_prompt("Plan my monthly budget using my salary, expenses, EMI, and savings target.")
    if col2.button("Draft leave letter", use_container_width=True):
        _add_quick_prompt("Create a simple official leave application message for my department.")
    if col3.button("Insurance checklist", use_container_width=True):
        _add_quick_prompt("Create an insurance renewal checklist using my insurance policies.")
    col4, col5, col6 = st.columns(3)
    if col4.button("PF explanation", use_container_width=True):
        _add_quick_prompt("Explain my PF growth in simple words and what I should check.")
    if col5.button("Create reminder idea", use_container_width=True):
        _add_quick_prompt("Suggest important reminders I should create based on my app data.")
    if col6.button("Monthly report summary", use_container_width=True):
        _add_quick_prompt("Summarize my monthly financial and family readiness report.")


def render(user: dict) -> None:
    st.title(t("ai_assistant"))
    user_id = user["id"]
    _ensure_chat_state()
    if "voice_prompt_text" not in st.session_state:
        st.session_state.voice_prompt_text = ""
    _api_key_box()
    _chat_controls(user_id)
    _quick_actions(user)

    st.caption("Ask follow-up questions about budget, EMI, CL/EL leave, PF, insurance, retirement, health reminders, trips, and letters.")
    example = "My PF balance is ₹3 lakh. How much can it become by retirement?"
    for msg in st.session_state.govlife_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.subheader(t("voice_help"))
    voice_col, input_col = st.columns([1, 3])
    with voice_col:
        st.write(t("speak"))
        if speech_to_text:
            spoken_text = speech_to_text(
                language=language_code(st.session_state.get("language", "English")),
                use_container_width=True,
                just_once=True,
                key="govlife_voice_input",
            )
            if spoken_text:
                st.session_state.voice_prompt_text = spoken_text
        else:
            st.info("Install streamlit-mic-recorder to enable voice input.")
    with input_col:
        st.text_area(
            t("transcribed_text"),
            placeholder=example,
            key="voice_prompt_text",
            height=110,
        )
    prompt = st.session_state.get("voice_prompt_text", "")
    if st.button(t("send"), use_container_width=True) and prompt.strip():
        user_msg = {"role": "user", "content": prompt}
        st.session_state.govlife_chat_messages.append(user_msg)
        _save_message(user_id, "user", prompt)
        st.session_state.voice_prompt_text = ""
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = ask_ai(st.session_state.govlife_chat_messages, _app_context(user))
            st.markdown(answer)
        st.session_state.govlife_chat_messages.append({"role": "assistant", "content": answer})
        _save_message(user_id, "assistant", answer)

    st.divider()
    st.subheader("PDF Document Reader")
    st.caption("This is separate from the removed Document Locker. PDFs are summarized for the current AI task only.")
    pdf = st.file_uploader("Upload PDF for AI summary", type=["pdf"])
    if pdf and st.button("Extract and summarize PDF"):
        text = extract_pdf_text(pdf)
        if not text:
            st.error("No readable text found in this PDF.")
        else:
            summary_prompt = {
                "role": "user",
                "content": (
                    "Summarize this PDF. Show key points, action items, important dates, "
                    "possible reminders, and visible amounts. Keep it simple.\n\n"
                    f"PDF text:\n{text[:12000]}"
                ),
            }
            with st.spinner("Summarizing PDF..."):
                st.markdown(ask_ai([summary_prompt], _app_context(user)))

    with st.expander("Saved chat history"):
        history = fetch_all(
            "SELECT chat_id, role, message, created_at FROM ai_chat_history WHERE user_id=? ORDER BY id DESC LIMIT 30",
            (user_id,),
        )
        for row in history:
            st.write(f"**{row['role'].title()}** ({row['created_at']}): {row['message']}")
