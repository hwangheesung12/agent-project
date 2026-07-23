from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from langchain.messages import AIMessage, HumanMessage
from streamlit.testing.v1 import AppTest

from views.chat import (
    MEDICAL_REFUSAL_MESSAGE,
    OPENAI_DEFAULT_MODEL,
    MedicalAdviceMiddleware,
    build_openai_chat_model,
    build_chat_user_id,
    default_chat_messages,
    generate_chatbot_reply,
    load_chat_memory,
    medical_advice_guardrail,
    save_chat_memory,
    should_block_medical_advice,
)


OPENAI_SETTINGS_TEST_SCRIPT = """
from views.chat import render_openai_settings

render_openai_settings()
"""


class ChatTests(unittest.TestCase):
    def test_medical_refusal_message_matches_required_copy(self):
        self.assertEqual(
            MEDICAL_REFUSAL_MESSAGE,
            "이 앱은 PubMed 메타데이터 분석용이며, 개인 의료 조언, 진단, 처방 "
            "관련 질문에는 답변할 수 없습니다. 의료 관련 결정은 의료 전문가와 "
            "상담해 주세요.",
        )

    def test_blocks_personal_medical_advice_question(self):
        question = "음주 후 타이레놀 먹어도 되나요?"

        self.assertTrue(should_block_medical_advice(question))
        self.assertEqual(
            medical_advice_guardrail(question),
            MEDICAL_REFUSAL_MESSAGE,
        )
        self.assertEqual(
            generate_chatbot_reply(question),
            MEDICAL_REFUSAL_MESSAGE,
        )

    def test_blocks_short_slang_medical_advice_question(self):
        question = "오늘 술 먹었는데 타이레놀 ㄱㅊ?"

        self.assertTrue(should_block_medical_advice(question))
        self.assertEqual(
            medical_advice_guardrail(question),
            MEDICAL_REFUSAL_MESSAGE,
        )
        self.assertEqual(
            generate_chatbot_reply(question),
            MEDICAL_REFUSAL_MESSAGE,
        )

    def test_allows_pubmed_metadata_question(self):
        question = "연도별 논문 추세는 어디서 확인하나요?"

        self.assertFalse(should_block_medical_advice(question))
        self.assertIn("연도별 논문 수", generate_chatbot_reply(question))

    def test_configured_chat_uses_selected_key_and_model(self):
        class FakeChatAgent:
            def invoke(self, _payload):
                return {"messages": [AIMessage(content="선택 모델 응답")]}

        with patch(
            "views.chat.build_pubmed_chat_agent",
            return_value=FakeChatAgent(),
        ) as build_agent:
            reply = generate_chatbot_reply(
                "연구 동향을 알려 주세요.",
                api_key="sk-test",
                model_name="gpt-5.6-luna",
            )

        self.assertEqual(reply, "선택 모델 응답")
        build_agent.assert_called_once_with("sk-test", "gpt-5.6-luna")

    def test_gpt_5_6_model_uses_none_reasoning(self):
        with patch("views.chat.ChatOpenAI") as chat_openai:
            build_openai_chat_model("sk-test", "gpt-5.6-luna")

        chat_openai.assert_called_once_with(
            model="gpt-5.6-luna",
            api_key="sk-test",
            timeout=30,
            max_retries=1,
            reasoning_effort="none",
        )

    def test_existing_default_model_preserves_temperature(self):
        with patch("views.chat.ChatOpenAI") as chat_openai:
            build_openai_chat_model("sk-test", OPENAI_DEFAULT_MODEL)

        chat_openai.assert_called_once_with(
            model=OPENAI_DEFAULT_MODEL,
            api_key="sk-test",
            timeout=30,
            max_retries=1,
            temperature=0,
        )

    def test_middleware_short_circuits_explicit_medical_advice(self):
        middleware = MedicalAdviceMiddleware()

        result = middleware.before_agent(
            {
                "messages": [
                    HumanMessage(content="술 마신 뒤 타이레놀 먹어도 되나요?")
                ]
            },
            runtime=None,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["jump_to"], "end")
        self.assertEqual(
            result["messages"][-1].content,
            MEDICAL_REFUSAL_MESSAGE,
        )

    def test_middleware_allows_pubmed_metadata_question(self):
        middleware = MedicalAdviceMiddleware()

        result = middleware.before_agent(
            {
                "messages": [
                    HumanMessage(content="연도별 논문 추세는 어디서 확인하나요?")
                ]
            },
            runtime=None,
        )

        self.assertIsNone(result)

    def test_openai_settings_confirms_and_hides_api_key_input(self):
        app = AppTest.from_string(
            OPENAI_SETTINGS_TEST_SCRIPT,
            default_timeout=15,
        ).run()

        self.assertEqual(
            [item.label for item in app.get("button_group")],
            ["모델 선택"],
        )
        self.assertEqual([item.label for item in app.text_input], ["OpenAI API 키"])

        with patch("views.chat.validate_openai_credentials") as validate:
            app.text_input[0].input("sk-test")
            app.button[0].click()
            app.run()

        validate.assert_called_once_with("sk-test", OPENAI_DEFAULT_MODEL)
        self.assertEqual([item.value for item in app.success], ["확인 완료"])
        self.assertEqual(len(app.text_input), 0)

    def test_google_account_identifier_prefers_subject(self):
        self.assertEqual(
            build_chat_user_id(
                {
                    "sub": "google-user-123",
                    "email": "USER@example.com",
                }
            ),
            "google-sub:google-user-123",
        )
        self.assertEqual(
            build_chat_user_id({"email": "USER@example.com"}),
            "google-email:user@example.com",
        )

    def test_chat_memory_persists_and_is_separated_by_google_account(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "chat.db")
            user_a = "google-sub:user-a"
            user_b = "google-sub:user-b"
            messages_a = [
                {"role": "user", "content": "A 사용자의 질문"},
                {"role": "assistant", "content": "A 사용자에게 답변"},
            ]
            messages_b = [
                {"role": "user", "content": "B 사용자의 질문"},
                {"role": "assistant", "content": "B 사용자에게 답변"},
            ]

            save_chat_memory(db_path, user_a, messages_a, "Alice")
            save_chat_memory(db_path, user_b, messages_b, "Bob")

            loaded_a = load_chat_memory(db_path, user_a)
            loaded_b = load_chat_memory(db_path, user_b)

            self.assertEqual(loaded_a["messages"], messages_a)
            self.assertEqual(loaded_a["user_name"], "Alice")
            self.assertEqual(loaded_b["messages"], messages_b)
            self.assertEqual(loaded_b["user_name"], "Bob")

            save_chat_memory(
                db_path,
                user_a,
                default_chat_messages(),
            )
            self.assertEqual(
                load_chat_memory(db_path, user_b)["messages"],
                messages_b,
            )


if __name__ == "__main__":
    unittest.main()
