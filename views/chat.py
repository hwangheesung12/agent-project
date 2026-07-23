import json
import os
from pathlib import Path
import re
from typing import Any

import streamlit as st


CHAT_HISTORY_KEY = "chat_messages"
USER_NAME_KEY = "chat_user_name"
CHAT_MEMORY_LOADED_KEY = "chat_memory_loaded"
CHAT_MEMORY_FILE = Path(os.getenv("PUBMED_CHAT_MEMORY_PATH", ".chat_memory.json"))

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


def load_chat_memory(memory_path: Path = CHAT_MEMORY_FILE) -> dict[str, Any]:
    if not memory_path.exists():
        return {"messages": default_chat_messages()}

    try:
        with memory_path.open(encoding="utf-8") as memory_file:
            saved_memory = json.load(memory_file)
    except (OSError, json.JSONDecodeError):
        return {"messages": default_chat_messages()}

    if not isinstance(saved_memory, dict):
        return {"messages": default_chat_messages()}

    return {
        "messages": sanitize_messages(saved_memory.get("messages")),
        "user_name": saved_memory.get("user_name"),
    }


def save_chat_memory(memory_path: Path = CHAT_MEMORY_FILE) -> None:
    memory = {
        "messages": st.session_state.get(CHAT_HISTORY_KEY, default_chat_messages()),
        "user_name": st.session_state.get(USER_NAME_KEY),
    }

    try:
        with memory_path.open("w", encoding="utf-8") as memory_file:
            json.dump(memory, memory_file, ensure_ascii=False, indent=2)
    except OSError as exc:
        st.warning(f"\ucc44\ud305 \ub0b4\uc5ed\uc744 \uc800\uc7a5\ud558\uc9c0 \ubabb\ud588\uc2b5\ub2c8\ub2e4: {exc}")


def initialize_chat_state() -> None:
    if not st.session_state.get(CHAT_MEMORY_LOADED_KEY):
        saved_memory = load_chat_memory()
        st.session_state[CHAT_HISTORY_KEY] = saved_memory["messages"]
        if isinstance(saved_memory.get("user_name"), str):
            st.session_state[USER_NAME_KEY] = saved_memory["user_name"]
        st.session_state[CHAT_MEMORY_LOADED_KEY] = True

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


def medical_advice_middleware(message: str) -> str | None:
    if should_block_medical_advice(message):
        return MEDICAL_REFUSAL_MESSAGE
    return None


def remember_user_details(message: str) -> None:
    name_match = re.search(
        r"(?:\ub0b4\s*\uc774\ub984\uc740|\uc81c\s*\uc774\ub984\uc740|\ub098\ub294|\uc800\ub294)\s*([A-Za-z\uac00-\ud7a3]{2,20})",
        message,
    )
    if name_match:
        st.session_state[USER_NAME_KEY] = name_match.group(1)


def generate_chatbot_reply(message: str) -> str:
    blocked_reply = medical_advice_middleware(message)
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


def append_chat_message(role: str, content: str) -> None:
    st.session_state[CHAT_HISTORY_KEY].append({"role": role, "content": content})
    save_chat_memory()


def clear_chat_memory() -> None:
    st.session_state[CHAT_HISTORY_KEY] = default_chat_messages()
    st.session_state.pop(USER_NAME_KEY, None)
    save_chat_memory()


def render_previous_chat_history() -> None:
    saved_memory = load_chat_memory()
    saved_messages = saved_memory["messages"]

    if saved_messages == default_chat_messages():
        st.info("\uc800\uc7a5\ub41c \uc774\uc804 \ucc44\ud305 \ub0b4\uc5ed\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.")
        return

    for message in saved_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def render_chat() -> None:
    initialize_chat_state()

    chat_tab, previous_chat_tab = st.tabs(
        ["\ucc44\ud305", "\uc774\uc804 \ucc44\ud305"]
    )

    with chat_tab:
        if st.button("\ucc44\ud305 \ub0b4\uc5ed \ucd08\uae30\ud654"):
            clear_chat_memory()
            st.rerun()

        for message in st.session_state[CHAT_HISTORY_KEY]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("\uc9c8\ubb38\uc744 \uc785\ub825\ud574 PubMed \ub370\uc774\ud130\uc5d0 \ub300\ud574 \ubb3c\uc5b4\ubcf4\uc138\uc694.")
        if prompt:
            append_chat_message("user", prompt)
            with st.chat_message("user"):
                st.markdown(prompt)

            reply = generate_chatbot_reply(prompt)
            append_chat_message("assistant", reply)
            with st.chat_message("assistant"):
                st.markdown(reply)

    with previous_chat_tab:
        render_previous_chat_history()
