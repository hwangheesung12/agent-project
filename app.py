from datetime import date

import streamlit as st


CURRENT_YEAR = date.today().year


st.set_page_config(
    page_title="PubMed Insight Dashboard",
    page_icon="🔎",
    layout="wide",
)


with st.sidebar:
    st.header("PubMed 검색 설정")

    keyword = st.text_input(
        "키워드",
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

    collect_clicked = st.button("PubMed 수집", type="primary", use_container_width=True)


if collect_clicked:
    if not keyword.strip():
        st.sidebar.error("키워드를 입력하세요.")
    elif start_year > end_year:
        st.sidebar.error("시작 연도는 끝 연도보다 클 수 없습니다.")
    else:
        st.session_state["pubmed_search_options"] = {
            "keyword": keyword.strip(),
            "start_year": int(start_year),
            "end_year": int(end_year),
            "max_papers": int(max_papers),
        }
        st.sidebar.success("검색 조건이 저장되었습니다.")


st.title("PubMed Insight Dashboard")

tab_overview, tab_papers, tab_chat = st.tabs(["개요", "논문 목록", "챗봇"])

with tab_overview:
    options = st.session_state.get("pubmed_search_options")

    total_papers = 0
    new_saved = 0
    duplicated = 0
    failed = 0

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("총 논문 수", total_papers)
    metric_col2.metric("신규 저장", new_saved)
    metric_col3.metric("중복 Skip", duplicated)
    metric_col4.metric("저장 수", failed)

    if options:
        st.info(
            f"검색 조건: {options['keyword']} "
            f"({options['start_year']}~{options['end_year']}), "
            f"최대 {options['max_papers']}개"
        )
    else:
        st.info("아직 수집된 데이터가 없습니다. 사이드바에서 검색 조건을 입력하고 PubMed 수집을 실행하세요.")

with tab_papers:
    st.info("논문 목록은 PubMed API 수집 기능 연결 후 표시됩니다.")

with tab_chat:
    st.info("챗봇 기능은 수집된 논문 데이터 연결 후 사용할 수 있습니다.")
