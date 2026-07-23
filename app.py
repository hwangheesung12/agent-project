from contextlib import closing
from datetime import date
import csv
import io
import os

import streamlit as st

from pubmed import (
    PubMedClient,
    PubMedError,
    get_connection,
    list_journals,
    count_journals,
    count_records,
    count_records_by_year,
    count_top_journals,
    get_connection,
    list_records,
    save_records,
)


CURRENT_YEAR = date.today().year


def load_env(path: str = ".env") -> None:
    """Load simple KEY=VALUE entries without requiring an extra dependency."""
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def records_to_csv(records: list[dict[str, object]]) -> bytes:
    output = io.StringIO()
    fieldnames = ["pmid", "title", "abstract", "journal", "pub_year", "authors"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue().encode("utf-8-sig")


load_env()
DB_PATH = os.getenv("PUBMED_DB_PATH", "pubmed.db")

st.set_page_config(
    page_title="PubMed Insight Dashboard",
    page_icon="🔎",
    layout="wide",
)

if "collection_stats" not in st.session_state:
    st.session_state["collection_stats"] = {
        "total": 0,
        "saved": 0,
        "duplicates": 0,
        "failed": 0,
    }

if "paper_filters" not in st.session_state:
    st.session_state["paper_filters"] = {
        "search_term": "",
        "start_year": 1900,
        "end_year": CURRENT_YEAR,
        "journal": "",
    }

with st.sidebar:
    st.header("PubMed 검색 설정")

    keyword = st.text_input(
        "키워드",
        value="CRISPR cancer therapy",
        placeholder="검색할 키워드를 입력하세요",
    )

    year_col1, year_col2 = st.columns(2)
    with year_col1:
        start_year = st.number_input(
            "시작 연도",
            min_value=1900,
            max_value=CURRENT_YEAR,
            value=2018,
            step=1,
        )
    with year_col2:
        end_year = st.number_input(
            "끝 연도",
            min_value=1900,
            max_value=CURRENT_YEAR,
            value=CURRENT_YEAR,
            step=1,
        )

    max_papers = st.slider(
        "최대 수집 논문 수",
        min_value=1,
        max_value=100,
        value=20,
        step=1,
    )

    collect_clicked = st.button(
        "PubMed 수집", type="primary", width="stretch"
    )

if collect_clicked:
    if not keyword.strip():
        st.sidebar.error("검색어를 입력하세요.")
    elif start_year > end_year:
        st.sidebar.error("시작 연도는 끝 연도보다 클 수 없습니다.")
    else:
        options = {
            "keyword": keyword.strip(),
            "start_year": int(start_year),
            "end_year": int(end_year),
            "max_papers": int(max_papers),
        }
        st.session_state["pubmed_search_options"] = options

        try:
            with st.spinner("PubMed에서 논문을 수집하고 있습니다..."):
                client = PubMedClient(
                    api_key=os.getenv("NCBI_API_KEY", ""),
                    email=os.getenv("NCBI_EMAIL", ""),
                )
                pmids = client.search(**options)
                records, failed = client.fetch(pmids)
                with get_connection(DB_PATH) as conn:
                with closing(
                    get_connection(os.getenv("PUBMED_DB_PATH", "pubmed.db"))
                ) as conn:
                    saved, duplicates = save_records(conn, records)

            st.session_state["collection_stats"] = {
                "total": len(pmids),
                "saved": saved,
                "duplicates": duplicates,
                "failed": failed,
            }
            st.sidebar.success(
                f"수집 완료: 신규 {saved}건, 중복 {duplicates}건, 실패 {failed}건"
            )
        except (PubMedError, OSError) as exc:
            st.sidebar.error(f"PubMed 수집 실패: {exc}")

st.title("PubMed Insight Dashboard")

tab_overview, tab_papers, tab_chat = st.tabs(["개요", "논문 목록", "챗봇"])

with tab_overview:
    stats = st.session_state["collection_stats"]
    with closing(
        get_connection(os.getenv("PUBMED_DB_PATH", "pubmed.db"))
    ) as conn:
        total_papers = count_records(conn)
        total_journals = count_journals(conn)
        papers_by_year = count_records_by_year(conn)
        top_journals = count_top_journals(conn)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("전체 논문 수", total_papers)
    metric_col2.metric("신규 수집", stats["saved"])
    metric_col3.metric("중복 Skip", stats["duplicates"])
    metric_col4.metric("총 저널 수", total_journals)

    options = st.session_state.get("pubmed_search_options")
    if options:
        st.info(
            f"검색 조건: {options['keyword']} "
            f"({options['start_year']}~{options['end_year']}), "
            f"최대 {options['max_papers']}건"
        )
    else:
        st.info("사이드바에서 검색 조건을 입력하고 PubMed 수집을 실행하세요.")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("연도별 논문 수")
        if papers_by_year:
            st.bar_chart(
                papers_by_year,
                x="pub_year",
                y="paper_count",
                x_label="출판 연도",
                y_label="논문 수",
                color="#287FB8",
                height=420,
            )
        else:
            st.info("출판 연도가 있는 논문 데이터가 없습니다.")

    with chart_col2:
        st.subheader("상위 저널")
        if top_journals:
            st.bar_chart(
                top_journals,
                x="paper_count",
                y="journal",
                x_label="논문 수",
                y_label="저널",
                color="#287FB8",
                horizontal=True,
                height=420,
            )
        else:
            st.info("저널 정보가 있는 논문 데이터가 없습니다.")

with tab_papers:
    st.subheader("수집 논문 목록")

    with get_connection(DB_PATH) as conn:
        journals = list_journals(conn)

    current_filters = st.session_state["paper_filters"]
    with st.form("paper_filter_form"):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2.2, 1, 1, 1.4])
        with filter_col1:
            search_term = st.text_input(
                "제목/Abstract 검색",
                value=current_filters["search_term"],
                placeholder="검색어를 입력하세요",
            )
        with filter_col2:
            filter_start_year = st.number_input(
                "시작 연도",
                min_value=1900,
                max_value=CURRENT_YEAR,
                value=int(current_filters["start_year"]),
                step=1,
            )
        with filter_col3:
            filter_end_year = st.number_input(
                "끝 연도",
                min_value=1900,
                max_value=CURRENT_YEAR,
                value=int(current_filters["end_year"]),
                step=1,
            )
        with filter_col4:
            journal_options = ["전체", *journals]
            saved_journal = current_filters["journal"] or "전체"
            journal_index = (
                journal_options.index(saved_journal)
                if saved_journal in journal_options
                else 0
            )
            selected_journal = st.selectbox(
                "저널",
                options=journal_options,
                index=journal_index,
            )

        search_clicked = st.form_submit_button("검색", type="primary")

    if search_clicked:
        if filter_start_year > filter_end_year:
            st.error("시작 연도는 끝 연도보다 클 수 없습니다.")
        else:
            st.session_state["paper_filters"] = {
                "search_term": search_term.strip(),
                "start_year": int(filter_start_year),
                "end_year": int(filter_end_year),
                "journal": "" if selected_journal == "전체" else selected_journal,
            }

    applied_filters = st.session_state["paper_filters"]
    with get_connection(DB_PATH) as conn:
        stored_records = list_records(
            conn,
            search_term=applied_filters["search_term"],
            start_year=int(applied_filters["start_year"]),
            end_year=int(applied_filters["end_year"]),
            journal=applied_filters["journal"],
        )

    if stored_records:
        st.caption(f"검색 결과 {len(stored_records)}건")
        st.dataframe(stored_records, use_container_width=True, hide_index=True)
        st.download_button(
            "CSV 다운로드",
            data=records_to_csv(stored_records),
            file_name="pubmed_filtered_records.csv",
            mime="text/csv",
        )
    else:
        st.info("조건에 맞는 논문이 없습니다.")

with tab_chat:
    st.info("챗봇 기능은 저장된 논문 데이터를 연결해 사용할 수 있습니다.")
