from contextlib import closing
from datetime import date
import os

import streamlit as st

from pubmed import PubMedClient, PubMedError, get_connection, save_records
from views.chat import (
    clear_openai_credentials,
    render_chat,
    render_openai_settings,
)
from views.overview import render_overview
from views.papers import render_papers
from views.theme import apply_clay_theme


CURRENT_YEAR = date.today().year


def logout_user() -> None:
    clear_openai_credentials()
    st.logout()


def render_dashboard(db_path: str) -> None:
    apply_clay_theme()
    if "collection_stats" not in st.session_state:
        st.session_state["collection_stats"] = {
            "total": 0,
            "saved": 0,
            "duplicates": 0,
            "failed": 0,
        }

    with st.sidebar:
        st.header("PubMed 검색 설정")

        keyword = st.text_input(
            "검색어",
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
                "종료 연도",
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

        st.divider()
        render_openai_settings()

        st.divider()
        user_name = st.user.get("name", "사용자")
        user_email = st.user.get("email", "")
        st.caption(f"{user_name}님")
        if user_email:
            st.caption(user_email)
        st.button("로그아웃", on_click=logout_user, width="stretch")

    if collect_clicked:
        if not keyword.strip():
            st.sidebar.error("검색어를 입력하세요.")
        elif start_year > end_year:
            st.sidebar.error("시작 연도는 종료 연도보다 클 수 없습니다.")
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
                    with closing(get_connection(db_path)) as conn:
                        saved, duplicates = save_records(conn, records)

                st.session_state["collection_stats"] = {
                    "total": len(pmids),
                    "saved": saved,
                    "duplicates": duplicates,
                    "failed": failed,
                }
                st.sidebar.success(
                    f"수집 완료: 신규 {saved}건, "
                    f"중복 {duplicates}건, 실패 {failed}건"
                )
            except (PubMedError, OSError) as exc:
                st.sidebar.error(f"PubMed 수집 실패: {exc}")

    st.markdown(
        '<span class="dashboard-kicker">MEDI TALK TALK · PUBMED INSIGHT</span>',
        unsafe_allow_html=True,
    )
    st.title("메디톡톡 연구 대시보드")
    st.markdown(
        '<p class="dashboard-subtitle">'
        "수집한 의학 논문의 흐름과 주요 저널을 한눈에 확인하세요."
        "</p>",
        unsafe_allow_html=True,
    )

    tab_overview, tab_papers, tab_chat = st.tabs(["개요", "논문 목록", "챗봇"])

    with tab_overview:
        render_overview(
            db_path=db_path,
            stats=st.session_state["collection_stats"],
            options=st.session_state.get("pubmed_search_options"),
        )

    with tab_papers:
        render_papers(db_path=db_path, current_year=CURRENT_YEAR)

    with tab_chat:
        render_chat(db_path=db_path)
