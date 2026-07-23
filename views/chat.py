from contextlib import closing
from functools import lru_cache
import os
import re
import sqlite3
from typing import Any, Mapping

import streamlit as st

from pubmed import get_connection


CHAT_HISTORY_KEY = "chat_messages"
USER_NAME_KEY = "chat_user_name"
CHAT_MEMORY_USER_KEY = "chat_memory_user_id"
LOCAL_PREVIEW_USER_ID = "local-preview"

MEDICAL_REFUSAL_MESSAGE = (
    "\uc774 \uc571\uc740 pubMed \uba54\ud0c0\ub370\uc774\ud130 \ubd84\uc11d\uc6a9\uc774\uba70, "
    "\uac1c\uc778 \uc758\ub8cc \uc870\uc5b8, \uc9c4\ub2e8 \uad00\ub828 \uc9c8\ubb38\uc5d0\ub294 "
    "\ub2f5\ubcc0\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4. \uc758\ub8cc \uad00\ub828 "
    "\uacb0\uc815\uc740 \uc758\ub8cc \uc804\ubb38\uac00\uc640 \uc0c1\ub2f4\ud574 \uc8fc\uc138\uc694."
)

DEFAULT_ASSISTANT_MESSAGE = (
    "\uc548\ub155\ud558\uc138\uc694. PubMed \uba54\ud0c0\ub370\uc774\ud130 \ubd84\uc11d\uc744 "
    "\ub3c4\uc640\ub4dc\ub9b4\uac8c\uc694. \ub370\uc774\ud130 \uc694\uc57d, "
    "\uc5f0\ub3c4\ubcc4 \ub17c\ubb38 \uc218, \uc0c1\uc704 \uc800\ub110, "
    "\ud0a4\uc6cc\ub4dc \ud0d0\uc0c9 \ub4f1\uc744 \ubb3c\uc5b4\ubcf4\uc138\uc694."
)

MEDICAL_CONTEXT_TERMS = (
    "\uac10\uae30",
    "\uac74\uac15",
    "\uac80\uc0ac",
    "\uace0\ud608\uc555",
    "\uae08\uae30",
    "\uae30\uce68",
    "\ub450\ud1b5",
    "\ub2f9\ub1e8",
    "\ubcf5\uc6a9",
    "\ubd80\uc791\uc6a9",
    "\uc0c1\ub2f4",
    "\uc218\uc220",
    "\uc220",
    "\uc544\ud30c",
    "\uc544\ud514",
    "\uc54c\ub808\ub974\uae30",
    "\uc57d",
    "\uc74c\uc8fc",
    "\uc758\uc0ac",
    "\uc758\ub8cc",
    "\uc758\ud559",
    "\uc784\uc2e0",
    "\uc99d\uc0c1",
    "\uc9c4\ub2e8",
    "\uc9c4\ub8cc",
    "\uc9c8\ud658",
    "\uc9c8\ubcd1",
    "\uc57d\ubb3c",
    "\ucc98\ubc29",
    "\uce58\ub8cc",
    "\ud0c0\uc774\ub808\ub180",
    "\ud1b5\uc99d",
    "\ud658\uc790",
    "acetaminophen",
    "alcohol",
    "diagnosis",
    "diagnose",
    "dose",
    "dosage",
    "drug",
    "medicine",
    "pain",
    "paracetamol",
    "patient",
    "prescribe",
    "prescription",
    "symptom",
    "treatment",
    "tylenol",
)
PERSONAL_ADVICE_PATTERNS = (
    "\u3131\u314a",
    "\uad00\ucc2e",
    "\uad1c\ucc2e",
    "\uad1c\ucd98",
    "\uac00\ub2a5",
    "\ub418\ub098",
    "\ub418\ub098\uc694",
    "\ub420\uae4c",
    "\ub420\uae4c\uc694",
    "\uba39\uc5b4\ub3c4",
    "\uba39\uc73c\uba74",
    "\ubb34\uc2a8 \ubcd1",
    "\ubb50 \uba39",
    "\ubcf5\uc6a9\ud574\ub3c4",
    "\uc5b4\ub5bb\uac8c \ud574\uc57c",
    "\uc5bc\ub9c8\ub098 \uba39",
    "\uc870\uc5b8",
    "\uc9c4\ub2e8",
    "\ucc98\ubc29",
    "\ucd94\ucc9c",
    "\uce58\ub8cc",
    "\ud574\ub3c4 \ub418",
    "?",
    "can i",
    "can you diagnose",
    "diagnose me",
    "should i",
    "what should i take",
)
MEDICAL_SAFETY_MODEL_ENV = "OPENAI_CHAT_MODEL"
MEDICAL_SAFETY_DEFAULT_MODEL = "gpt-4o-mini"
MEDICAL_SAFETY_SYSTEM_PROMPT = (
    "You are a strict safety guardrail for a PubMed metadata analysis chatbot. "
    "Classify the user's message.\n"
    "Return only BLOCK or ALLOW.\n\n"
    "BLOCK when the user asks for personal medical advice, diagnosis, "
    "prescription, dosing, drug safety for themselves or another specific "
    "person, treatment decisions, symptom triage, or whether an action is "
    "medically okay.\n"
    "ALLOW when the user asks about PubMed metadata, papers, journals, "
    "research trends, app usage, or general literature analysis without "
    "asking for personal medical decisions."
)


def default_chat_messages() -> list[dict[str, str]]:
    return [{"role": "assistant", "content": DEFAULT_ASSISTANT_MESSAGE}]


def sanitize_messages(messages: Any) -> list[dict[str, str]]:
    if not isinstance(messages, list):
        return default_chat_messages()

    sanitized = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            sanitized.append({"role": role, "content": content})

    return sanitized or default_chat_messages()


def build_chat_user_id(user_info: Mapping[str, Any]) -> str:
    subject = str(user_info.get("sub") or "").strip()
    if subject:
        return f"google-sub:{subject}"

    email = str(user_info.get("email") or "").strip().casefold()
    if email:
        return f"google-email:{email}"

    return LOCAL_PREVIEW_USER_ID


def current_chat_user_id() -> str:
    return build_chat_user_id(st.user)


def ensure_chat_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS chat_users (
            user_id TEXT PRIMARY KEY,
            user_name TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES chat_users(user_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id_id
        ON chat_messages(user_id, id);
        """
    )
    conn.commit()


def load_chat_memory(db_path: str, user_id: str) -> dict[str, Any]:
    with closing(get_connection(db_path)) as conn:
        ensure_chat_tables(conn)
        profile = conn.execute(
            "SELECT user_name FROM chat_users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()

    messages = sanitize_messages(
        [{"role": role, "content": content} for role, content in rows]
    )
    return {
        "messages": messages,
        "user_name": profile[0] if profile else None,
    }


def save_chat_memory(
    db_path: str,
    user_id: str,
    messages: list[dict[str, str]],
    user_name: str | None = None,
) -> None:
    sanitized_messages = sanitize_messages(messages)
    with closing(get_connection(db_path)) as conn:
        ensure_chat_tables(conn)
        with conn:
            conn.execute(
                """
                INSERT INTO chat_users (user_id, user_name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    user_name = excluded.user_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, user_name),
            )
            conn.execute(
                "DELETE FROM chat_messages WHERE user_id = ?",
                (user_id,),
            )
            conn.executemany(
                """
                INSERT INTO chat_messages (user_id, role, content)
                VALUES (?, ?, ?)
                """,
                [
                    (user_id, message["role"], message["content"])
                    for message in sanitized_messages
                ],
            )


def save_current_chat_memory(db_path: str, user_id: str) -> None:
    try:
        save_chat_memory(
            db_path=db_path,
            user_id=user_id,
            messages=st.session_state.get(
                CHAT_HISTORY_KEY,
                default_chat_messages(),
            ),
            user_name=st.session_state.get(USER_NAME_KEY),
        )
    except (OSError, sqlite3.Error) as exc:
        st.warning(f"채팅 내역을 저장하지 못했습니다: {exc}")


def initialize_chat_state(db_path: str, user_id: str) -> None:
    if st.session_state.get(CHAT_MEMORY_USER_KEY) != user_id:
        saved_memory = load_chat_memory(db_path, user_id)
        st.session_state[CHAT_HISTORY_KEY] = saved_memory["messages"]
        saved_user_name = saved_memory.get("user_name")
        if isinstance(saved_user_name, str) and saved_user_name:
            st.session_state[USER_NAME_KEY] = saved_user_name
        else:
            st.session_state.pop(USER_NAME_KEY, None)
        st.session_state[CHAT_MEMORY_USER_KEY] = user_id

    if CHAT_HISTORY_KEY not in st.session_state:
        st.session_state[CHAT_HISTORY_KEY] = default_chat_messages()


def should_block_medical_advice(message: str) -> bool:
    normalized = message.casefold()
    has_medical_context = any(term in normalized for term in MEDICAL_CONTEXT_TERMS)
    asks_personal_advice = any(
        pattern in normalized for pattern in PERSONAL_ADVICE_PATTERNS
    )
    mentions_first_person = bool(
        re.search(r"\b(i|me|my)\b", normalized)
    ) or any(term in normalized for term in ("\ub098", "\ub0b4", "\uc800", "\uc81c\uac00"))
    asks_question = "?" in normalized or any(
        ending in normalized
        for ending in (
            "\ub098\uc694",
            "\uac00\uc694",
            "\uc694",
            "\uae4c",
            "\uc74c",
            "\uc784",
        )
    )

    return has_medical_context and (
        asks_personal_advice or mentions_first_person or asks_question
    )


@lru_cache(maxsize=1)
def build_medical_safety_chain():
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MEDICAL_SAFETY_SYSTEM_PROMPT),
            ("human", "{message}"),
        ]
    )
    model_name = os.getenv(
        MEDICAL_SAFETY_MODEL_ENV,
        MEDICAL_SAFETY_DEFAULT_MODEL,
    ).strip()
    llm = ChatOpenAI(
        model=model_name or MEDICAL_SAFETY_DEFAULT_MODEL,
        temperature=0,
        timeout=8,
        max_retries=1,
    )
    return prompt | llm | StrOutputParser()


def classify_medical_advice_with_langchain_guardrail(message: str) -> bool | None:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return None

    try:
        classification = build_medical_safety_chain().invoke(
            {"message": message}
        )
    except Exception:
        return None

    normalized = str(classification).strip().casefold()
    if normalized.startswith("block"):
        return True
    if normalized.startswith("allow"):
        return False
    return None


def medical_advice_guardrail(message: str) -> str | None:
    if should_block_medical_advice(message):
        return MEDICAL_REFUSAL_MESSAGE

    langchain_decision = classify_medical_advice_with_langchain_guardrail(message)
    if langchain_decision:
        return MEDICAL_REFUSAL_MESSAGE

    return None


def medical_advice_middleware(message: str) -> str | None:
    return medical_advice_guardrail(message)


def remember_user_details(message: str) -> None:
    name_match = re.search(
        r"(?:\ub0b4\s*\uc774\ub984\uc740|\uc81c\s*\uc774\ub984\uc740|\ub098\ub294|\uc800\ub294)\s*([A-Za-z\uac00-\ud7a3]{2,20})",
        message,
    )
    if name_match:
        st.session_state[USER_NAME_KEY] = name_match.group(1)


def generate_chatbot_reply(message: str) -> str:
    blocked_reply = medical_advice_guardrail(message)
    if blocked_reply:
        return blocked_reply

    remember_user_details(message)
    normalized = message.casefold()
    user_name = st.session_state.get(USER_NAME_KEY)

    if "\uc774\ub984" in normalized and any(
        term in normalized for term in ("\ubb50", "\ubb34\uc5c7", "\uae30\uc5b5")
    ):
        if user_name:
            return f"{user_name}\ub2d8\uc774\ub77c\uace0 \uae30\uc5b5\ud558\uace0 \uc788\uc5b4\uc694."
        return (
            "\uc544\uc9c1 \uc774\ub984\uc744 \uc54c\ub824\uc8fc\uc9c0 \uc54a\uc73c\uc168\uc5b4\uc694. "
            "\uc608: '\ub0b4 \uc774\ub984\uc740 Jay\uc57c'\ucc98\ub7fc \uc54c\ub824\uc8fc\uc138\uc694."
        )

    if any(term in normalized for term in ("\uc548\ub155", "hello", "hi")):
        greeting = f"{user_name}\ub2d8, " if user_name else ""
        return f"\uc548\ub155\ud558\uc138\uc694, {greeting}PubMed \ub370\uc774\ud130 \ubd84\uc11d\uc744 \ub3c4\uc640\ub4dc\ub9b4\uac8c\uc694."

    if any(term in normalized for term in ("\uae30\uc5b5", "memory", "\uba54\ubaa8\ub9ac")):
        if user_name:
            return (
                f"\ud604\uc7ac \uae30\uc5b5\ud558\uace0 \uc788\ub294 \uc815\ubcf4: "
                f"\uc0ac\uc6a9\uc790 \uc774\ub984\uc740 {user_name}\ub2d8\uc785\ub2c8\ub2e4."
            )
        return (
            "\ud604\uc7ac \uae30\uc5b5\ud55c \uc0ac\uc6a9\uc790 \uc815\ubcf4\ub294 \uc544\uc9c1 "
            "\uc5c6\uc5b4\uc694. \ub300\ud654 \uc911 \uc54c\ub824\uc8fc\uc2e0 \uc774\ub984\uc740 "
            "\uae30\uc5b5\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4."
        )

    if any(term in normalized for term in ("\uc5f0\ub3c4", "year", "\ucd94\uc138", "trend")):
        return "\uc5f0\ub3c4\ubcc4 \ub17c\ubb38 \uc218\ub294 '\uac1c\uc694' \ud0ed\uc758 \ub9c9\ub300\uadf8\ub798\ud504\uc5d0\uc11c \ud655\uc778\ud560 \uc218 \uc788\uc5b4\uc694."

    if any(term in normalized for term in ("\uc800\ub110", "journal")):
        return "\uc0c1\uc704 \uc800\ub110\uacfc \uc800\ub110\ubcc4 \ub17c\ubb38 \uc218\ub294 '\uac1c\uc694' \ud0ed\uacfc '\ub17c\ubb38 \ubaa9\ub85d' \ud544\ud130\uc5d0\uc11c \ud655\uc778\ud560 \uc218 \uc788\uc5b4\uc694."

    if any(term in normalized for term in ("\ub17c\ubb38", "paper", "pmid", "\ucd08\ub85d", "abstract")):
        return "\ub17c\ubb38 \uc81c\ubaa9, \ucd08\ub85d, PMID, \uc800\ub110, \ucd9c\ud310\uc5f0\ub3c4\ub294 '\ub17c\ubb38 \ubaa9\ub85d' \ud0ed\uc5d0\uc11c \uac80\uc0c9\ud558\uace0 CSV\ub85c \ub0b4\ub824\ubc1b\uc744 \uc218 \uc788\uc5b4\uc694."

    return (
        "PubMed \uba54\ud0c0\ub370\uc774\ud130\uc5d0 \ub300\ud574 \uc9c8\ubb38\ud574 \uc8fc\uc138\uc694. "
        "\uc608: '\uc5f0\ub3c4\ubcc4 \ucd94\uc138\ub97c \uc5b4\ub514\uc11c \ubcf4\ub098\uc694?', "
        "'\uc0c1\uc704 \uc800\ub110\uc744 \ud655\uc778\ud558\uace0 \uc2f6\uc5b4\uc694', "
        "'\ub0b4 \uc774\ub984\uc740 Jay\uc57c'\ucc98\ub7fc \ubb3c\uc5b4\ubcfc \uc218 \uc788\uc2b5\ub2c8\ub2e4."
    )


def append_chat_message(
    db_path: str,
    user_id: str,
    role: str,
    content: str,
) -> None:
    st.session_state[CHAT_HISTORY_KEY].append({"role": role, "content": content})
    save_current_chat_memory(db_path, user_id)


def clear_chat_memory(db_path: str, user_id: str) -> None:
    st.session_state[CHAT_HISTORY_KEY] = default_chat_messages()
    st.session_state.pop(USER_NAME_KEY, None)
    save_current_chat_memory(db_path, user_id)


def render_previous_chat_history(db_path: str, user_id: str) -> None:
    saved_memory = load_chat_memory(db_path, user_id)
    saved_messages = saved_memory["messages"]

    if saved_messages == default_chat_messages():
        st.info("\uc800\uc7a5\ub41c \uc774\uc804 \ucc44\ud305 \ub0b4\uc5ed\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.")
        return

    for message in saved_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def render_chat(db_path: str) -> None:
    user_id = current_chat_user_id()
    initialize_chat_state(db_path, user_id)

    chat_tab, previous_chat_tab = st.tabs(
        ["\ucc44\ud305", "\uc774\uc804 \ucc44\ud305"]
    )

    with chat_tab:
        if st.button("\ucc44\ud305 \ub0b4\uc5ed \ucd08\uae30\ud654"):
            clear_chat_memory(db_path, user_id)
            st.rerun()

        for message in st.session_state[CHAT_HISTORY_KEY]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("\uc9c8\ubb38\uc744 \uc785\ub825\ud574 PubMed \ub370\uc774\ud130\uc5d0 \ub300\ud574 \ubb3c\uc5b4\ubcf4\uc138\uc694.")
        if prompt:
            append_chat_message(db_path, user_id, "user", prompt)
            with st.chat_message("user"):
                st.markdown(prompt)

            reply = generate_chatbot_reply(prompt)
            append_chat_message(db_path, user_id, "assistant", reply)
            with st.chat_message("assistant"):
                st.markdown(reply)

    with previous_chat_tab:
        render_previous_chat_history(db_path, user_id)
