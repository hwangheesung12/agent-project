from contextlib import closing
import json
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest

from pubmed import PubMedRecord, get_connection, save_records


DASHBOARD_TEST_SCRIPT = """
from views.dashboard import render_dashboard

render_dashboard({db_path!r})
"""


class DashboardTests(unittest.TestCase):
    def test_unauthenticated_user_only_sees_landing_page(self):
        app_path = str(Path(__file__).with_name("app.py"))
        app = AppTest.from_file(app_path).run(timeout=15)

        self.assertFalse(app.exception)
        self.assertTrue(any("메디톡톡" in item.value for item in app.markdown))
        self.assertTrue(any("--clay-bg" in item.value for item in app.markdown))
        self.assertEqual([button.label for button in app.button], ["Google로 로그인"])
        self.assertEqual(len(app.tabs), 0)
        self.assertEqual(len(app.sidebar.text_input), 0)

    def test_authenticated_dashboard_keeps_existing_features(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "dashboard.db")
            with closing(get_connection(db_path)) as conn:
                save_records(
                    conn,
                    [
                        PubMedRecord("1", "A", "", "Journal A", 2023, "Kim"),
                        PubMedRecord("2", "B", "", "Journal A", 2024, "Lee"),
                        PubMedRecord("3", "C", "", "Journal B", 2024, "Park"),
                    ],
                )

            app = AppTest.from_string(
                DASHBOARD_TEST_SCRIPT.format(db_path=db_path),
                default_timeout=15,
            ).run(timeout=15)

            self.assertFalse(app.exception)
            self.assertTrue(any("--clay-bg" in item.value for item in app.markdown))
            self.assertEqual(
                [(metric.label, metric.value) for metric in app.metric],
                [
                    ("전체 논문 수", "3"),
                    ("신규 수집", "0"),
                    ("중복 Skip", "0"),
                    ("총 저널 수", "2"),
                ],
            )
            self.assertEqual(
                [header.value for header in app.subheader],
                ["연도별 논문 수", "상위 저널", "수집 논문 목록"],
            )
            self.assertEqual(
                [selectbox.label for selectbox in app.selectbox],
                ["저널", "모델"],
            )
            sidebar_markers = [
                node.value
                for node in app.sidebar
                if node.type in {"header", "caption"}
            ]
            self.assertLess(
                sidebar_markers.index("PubMed 검색 설정"),
                sidebar_markers.index("OpenAI 설정"),
            )
            self.assertLess(
                sidebar_markers.index("OpenAI 설정"),
                sidebar_markers.index("사용자님"),
            )
            self.assertEqual(
                [button.label for button in app.get("download_button")],
                ["CSV 다운로드"],
            )
            chat_history_blocks = [
                block
                for block in app.get("flex_container")
                if any(
                    getattr(child, "type", None) == "chat_message"
                    for child in block.children.values()
                )
            ]
            self.assertEqual(len(chat_history_blocks), 1)
            self.assertEqual(
                chat_history_blocks[0].proto.height_config.pixel_height,
                520,
            )
            chat_tab = next(tab for tab in app.tabs if tab.label == "채팅")
            self.assertTrue(
                chat_tab.children[1].proto.id.endswith(
                    "-chat_history_scroll"
                )
            )
            self.assertTrue(
                chat_tab.children[2].proto.id.endswith("-chat_input_area")
            )
            self.assertEqual(len(app.chat_input), 0)
            message_input = next(
                item for item in app.text_input if item.label == "메시지"
            )
            self.assertTrue(message_input.disabled)

            charts = app.get("vega_lite_chart")
            self.assertEqual(len(charts), 2)
            year_chart_spec = json.loads(charts[0].proto.spec)
            journal_chart_spec = json.loads(charts[1].proto.spec)
            self.assertEqual(year_chart_spec["height"], 330)
            self.assertEqual(journal_chart_spec["height"], 330)
            self.assertEqual(year_chart_spec["width"], "container")
            self.assertEqual(journal_chart_spec["width"], "container")
            self.assertEqual(
                journal_chart_spec["mark"],
                {
                    "type": "bar",
                    "color": "#8061e8",
                    "cornerRadiusEnd": 5,
                    "size": 20,
                },
            )
            self.assertEqual(journal_chart_spec["encoding"]["x"]["title"], "Count")
            self.assertEqual(
                journal_chart_spec["encoding"]["y"]["sort"],
                {"field": "paper_count", "order": "descending"},
            )
            self.assertEqual(
                journal_chart_spec["encoding"]["y"]["axis"]["labelLimit"],
                155,
            )


if __name__ == "__main__":
    unittest.main()
