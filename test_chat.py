from pathlib import Path

from views.chat import (
    MEDICAL_REFUSAL_MESSAGE,
    generate_chatbot_reply,
    load_chat_memory,
    medical_advice_middleware,
    should_block_medical_advice,
)


def test_blocks_personal_medical_advice_question():
    question = "\uc74c\uc8fc \ud6c4 \ud0c0\uc774\ub808\ub180 \uba39\uc5b4\ub3c4 \ub418\ub098\uc694?"

    assert should_block_medical_advice(question)
    assert medical_advice_middleware(question) == MEDICAL_REFUSAL_MESSAGE
    assert generate_chatbot_reply(question) == MEDICAL_REFUSAL_MESSAGE


def test_blocks_short_slang_medical_advice_question():
    question = "\uc624\ub298 \uc220 \uba39\uc5c8\ub294\ub370 \ud0c0\uc774\ub808\ub180 \u3131\u314a?"

    assert should_block_medical_advice(question)
    assert medical_advice_middleware(question) == MEDICAL_REFUSAL_MESSAGE
    assert generate_chatbot_reply(question) == MEDICAL_REFUSAL_MESSAGE


def test_allows_pubmed_metadata_question():
    question = "\uc5f0\ub3c4\ubcc4 \ub17c\ubb38 \ucd94\uc138\ub294 \uc5b4\ub514\uc11c \ud655\uc778\ud558\ub098\uc694?"

    assert not should_block_medical_advice(question)
    assert "\uc5f0\ub3c4\ubcc4 \ub17c\ubb38 \uc218" in generate_chatbot_reply(question)


def test_load_chat_memory_restores_saved_messages(tmp_path: Path):
    memory_path = tmp_path / "chat_memory.json"
    memory_path.write_text(
        (
            '{"messages":[{"role":"user","content":"hello"},'
            '{"role":"assistant","content":"hi"}],"user_name":"Jay"}'
        ),
        encoding="utf-8",
    )

    loaded_memory = load_chat_memory(memory_path)

    assert loaded_memory["messages"][-1] == {"role": "assistant", "content": "hi"}
    assert loaded_memory["user_name"] == "Jay"
