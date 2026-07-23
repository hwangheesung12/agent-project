from contextlib import closing
import json
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest

from pubmed import PubMedRecord, get_connection, save_records


def dashboard_test_app(db_path: str) -> None:
    from views.dashboard import render_dashboard

    render_dashboard(db_path)


class DashboardTests(unittest.TestCase):
    def test_unauthenticated_user_only_sees_landing_page(self):
        app_path = str(Path(__file__).with_name("app.py"))
        app = AppTest.from_file(app_path).run(timeout=15)

        self.assertFalse(app.exception)
        self.assertTrue(any("메디톡톡" in item.value for item in app.markdown))
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

            app = AppTest.from_function(
                dashboard_test_app,
                args=(db_path,),
                default_timeout=15,
            ).run(timeout=15)

            self.assertFalse(app.exception)
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
                ["저널"],
            )
            self.assertEqual(
                [button.label for button in app.get("download_button")],
                ["CSV 다운로드"],
            )

            charts = app.get("vega_lite_chart")
            self.assertEqual(len(charts), 2)
            journal_chart_spec = json.loads(charts[1].proto.spec)
            self.assertEqual(
                journal_chart_spec["mark"],
                {"type": "bar", "color": "#1f77b4", "size": 21},
            )
            self.assertEqual(journal_chart_spec["encoding"]["x"]["title"], "Count")
            self.assertEqual(
                journal_chart_spec["encoding"]["y"]["sort"],
                {"field": "paper_count", "order": "descending"},
            )
            self.assertEqual(
                journal_chart_spec["encoding"]["y"]["axis"]["labelLimit"],
                185,
            )


if __name__ == "__main__":
    unittest.main()
