from contextlib import closing
import json
import os
from pathlib import Path
import tempfile
import unittest

from streamlit.testing.v1 import AppTest

from pubmed import PubMedRecord, get_connection, save_records


class DashboardTests(unittest.TestCase):
    def test_overview_metrics_and_charts_with_stored_records(self):
        previous_db_path = os.environ.get("PUBMED_DB_PATH")
        try:
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

                os.environ["PUBMED_DB_PATH"] = db_path
                app_path = str(Path(__file__).with_name("app.py"))
                app = AppTest.from_file(app_path).run(timeout=15)

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
        finally:
            if previous_db_path is None:
                os.environ.pop("PUBMED_DB_PATH", None)
            else:
                os.environ["PUBMED_DB_PATH"] = previous_db_path


if __name__ == "__main__":
    unittest.main()
