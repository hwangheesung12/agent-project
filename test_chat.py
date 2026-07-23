from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from views.chat import (
    MEDICAL_REFUSAL_MESSAGE,
    build_chat_user_id,
    default_chat_messages,
    generate_chatbot_reply,
    load_chat_memory,
    medical_advice_guardrail,
    medical_advice_middleware,
    save_chat_memory,
    should_block_medical_advice,
)


class ChatTests(unittest.TestCase):
    def test_blocks_personal_medical_advice_question(self):
        question = "음주 후 타이레놀 먹어도 되나요?"

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            self.assertTrue(should_block_medical_advice(question))
            self.assertEqual(
                medical_advice_guardrail(question),
                MEDICAL_REFUSAL_MESSAGE,
            )
            self.assertEqual(
                medical_advice_middleware(question),
                MEDICAL_REFUSAL_MESSAGE,
            )
            self.assertEqual(
                generate_chatbot_reply(question),
                MEDICAL_REFUSAL_MESSAGE,
            )

    def test_blocks_short_slang_medical_advice_question(self):
        question = "오늘 술 먹었는데 타이레놀 ㄱㅊ?"

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
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

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            self.assertFalse(should_block_medical_advice(question))
            self.assertIn("연도별 논문 수", generate_chatbot_reply(question))

    def test_langchain_guardrail_blocks_model_classified_question(self):
        class FakeSafetyChain:
            def invoke(self, _payload):
                return "BLOCK"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch(
                "views.chat.build_medical_safety_chain",
                return_value=FakeSafetyChain(),
            ):
                self.assertEqual(
                    medical_advice_guardrail("분류 모델 테스트용 문장"),
                    MEDICAL_REFUSAL_MESSAGE,
                )

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
