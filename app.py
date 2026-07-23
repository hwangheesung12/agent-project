from datetime import date
import os

import streamlit as st

from pubmed import PubMedClient, PubMedError, get_connection, list_records, save_records


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


load_env()

st.set_page_config(
    page_title="PubMed Insight Dashboard",
    page_icon="🧬",
    layout="wide",
)

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
        placeholder="검색 키워드를 입력하세요",
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
        "PubMed 수집", type="primary", use_container_width=True
    )

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
                with get_connection(os.getenv("PUBMED_DB_PATH", "pubmed.db")) as conn:
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
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("검색 PMID 수", stats["total"])
    metric_col2.metric("신규 저장", stats["saved"])
    metric_col3.metric("중복 Skip", stats["duplicates"])
    metric_col4.metric("수집 실패", stats["failed"])

    options = st.session_state.get("pubmed_search_options")
    if options:
        st.info(
            f"검색 조건: {options['keyword']} "
            f"({options['start_year']}~{options['end_year']}), "
            f"최대 {options['max_papers']}건"
        )
    else:
        st.info("사이드바에서 검색 조건을 입력하고 PubMed 수집을 실행하세요.")

with tab_papers:
    with get_connection(os.getenv("PUBMED_DB_PATH", "pubmed.db")) as conn:
        stored_records = list_records(conn)

    if stored_records:
        st.dataframe(stored_records, use_container_width=True, hide_index=True)
    else:
        st.info("저장된 논문이 없습니다.")

with tab_chat:
    st.info("챗봇 기능은 저장된 논문 데이터를 연결해 사용할 수 있습니다.")
