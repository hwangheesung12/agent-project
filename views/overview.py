from contextlib import closing

import altair as alt
import streamlit as st

from pubmed import (
    count_journals,
    count_records,
    count_records_by_year,
    count_top_journals,
    get_connection,
)


def render_overview(
    db_path: str,
    stats: dict[str, int],
    options: dict[str, object] | None,
) -> None:
    with closing(get_connection(db_path)) as conn:
        total_papers = count_records(conn)
        total_journals = count_journals(conn)
        papers_by_year = count_records_by_year(conn)
        top_journals = count_top_journals(conn)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("전체 논문 수", total_papers)
    metric_col2.metric("신규 수집", stats["saved"])
    metric_col3.metric("중복 Skip", stats["duplicates"])
    metric_col4.metric("총 저널 수", total_journals)

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
            st.altair_chart(_top_journals_chart(top_journals), width="stretch")
        else:
            st.info("저널 정보가 있는 논문 데이터가 없습니다.")


def _top_journals_chart(
    top_journals: list[dict[str, str | int]],
) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=top_journals))
        .mark_bar(color="#1f77b4", size=21)
        .encode(
            x=alt.X(
                "paper_count:Q",
                title="Count",
                scale=alt.Scale(zero=True, nice=True),
                axis=alt.Axis(grid=True, tickMinStep=1, tickCount=8),
            ),
            y=alt.Y(
                "journal:N",
                title=None,
                sort=alt.EncodingSortField(field="paper_count", order="descending"),
                axis=alt.Axis(
                    grid=False,
                    labelLimit=185,
                    labelFontSize=10,
                    labelPadding=6,
                    ticks=False,
                ),
            ),
            tooltip=[
                alt.Tooltip("journal:N", title="저널"),
                alt.Tooltip("paper_count:Q", title="논문 수"),
            ],
        )
        .properties(height=320)
        .configure_view(stroke="#333333", strokeWidth=1)
        .configure_axis(
            domainColor="#333333",
            gridColor="#e6e6e6",
            gridOpacity=1,
            labelColor="#222222",
            tickColor="#333333",
            titleColor="#222222",
            titleFontSize=12,
        )
    )
