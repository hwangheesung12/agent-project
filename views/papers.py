from contextlib import closing
import csv
import io

import streamlit as st

from pubmed import get_connection, list_journals, list_records


def records_to_csv(records: list[dict[str, object]]) -> bytes:
    output = io.StringIO()
    fieldnames = ["pmid", "title", "abstract", "journal", "pub_year", "authors"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue().encode("utf-8-sig")


def render_papers(db_path: str, current_year: int) -> None:
    if "paper_filters" not in st.session_state:
        st.session_state["paper_filters"] = {
            "search_term": "",
            "start_year": 1900,
            "end_year": current_year,
            "journal": "",
        }

    st.subheader("수집 논문 목록")

    with closing(get_connection(db_path)) as conn:
        journals = list_journals(conn)

    current_filters = st.session_state["paper_filters"]
    with st.form("paper_filter_form"):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(
            [2.2, 1, 1, 1.4]
        )
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
                max_value=current_year,
                value=int(current_filters["start_year"]),
                step=1,
            )
        with filter_col3:
            filter_end_year = st.number_input(
                "종료 연도",
                min_value=1900,
                max_value=current_year,
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
            st.error("시작 연도는 종료 연도보다 클 수 없습니다.")
        else:
            st.session_state["paper_filters"] = {
                "search_term": search_term.strip(),
                "start_year": int(filter_start_year),
                "end_year": int(filter_end_year),
                "journal": "" if selected_journal == "전체" else selected_journal,
            }

    applied_filters = st.session_state["paper_filters"]
    with closing(get_connection(db_path)) as conn:
        stored_records = list_records(
            conn,
            search_term=applied_filters["search_term"],
            start_year=int(applied_filters["start_year"]),
            end_year=int(applied_filters["end_year"]),
            journal=applied_filters["journal"],
        )

    if stored_records:
        st.caption(f"검색 결과 {len(stored_records)}건")
        st.dataframe(stored_records, width="stretch", hide_index=True)
        st.download_button(
            "CSV 다운로드",
            data=records_to_csv(stored_records),
            file_name="pubmed_filtered_records.csv",
            mime="text/csv",
        )
    else:
        st.info("조건에 맞는 논문이 없습니다.")
