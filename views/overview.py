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

CHART_HEIGHT = 330


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

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(
        4,
        gap="medium",
        vertical_alignment="top",
    )
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

    chart_col1, chart_col2 = st.columns(2, gap="medium")
    with chart_col1:
        st.subheader("연도별 논문 수")
        if papers_by_year:
            st.altair_chart(
                _papers_by_year_chart(papers_by_year),
                width="stretch",
            )
        else:
            st.info("출판 연도가 있는 논문 데이터가 없습니다.")

    with chart_col2:
        st.subheader("상위 저널")
        if top_journals:
            st.altair_chart(_top_journals_chart(top_journals), width="stretch")
        else:
            st.info("저널 정보가 있는 논문 데이터가 없습니다.")


def _papers_by_year_chart(
    papers_by_year: list[dict[str, int]],
) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=papers_by_year))
        .mark_bar(
            color="#7047eb",
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
        )
        .encode(
            x=alt.X(
                "pub_year:O",
                title="출판 연도",
                sort="ascending",
                axis=alt.Axis(
                    labelAngle=-35,
                    labelPadding=8,
                    ticks=False,
                ),
            ),
            y=alt.Y(
                "paper_count:Q",
                title="논문 수",
                scale=alt.Scale(zero=True, nice=True),
                axis=alt.Axis(grid=True, tickMinStep=1, tickCount=7),
            ),
            tooltip=[
                alt.Tooltip("pub_year:O", title="출판 연도"),
                alt.Tooltip("paper_count:Q", title="논문 수"),
            ],
        )
        .properties(width="container", height=CHART_HEIGHT)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            domainColor="#77718f",
            gridColor="#dddff0",
            gridOpacity=0.8,
            labelColor="#4b4760",
            labelFontSize=11,
            tickColor="#77718f",
            titleColor="#343047",
            titleFontSize=12,
            titlePadding=12,
        )
    )


def _top_journals_chart(
    top_journals: list[dict[str, str | int]],
) -> alt.Chart:
    return (
        alt.Chart(alt.Data(values=top_journals))
        .mark_bar(
            color="#8061e8",
            size=20,
            cornerRadiusEnd=5,
        )
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
                    labelLimit=155,
                    labelFontSize=10,
                    labelPadding=8,
                    ticks=False,
                ),
            ),
            tooltip=[
                alt.Tooltip("journal:N", title="저널"),
                alt.Tooltip("paper_count:Q", title="논문 수"),
            ],
        )
        .properties(width="container", height=CHART_HEIGHT)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            domainColor="#77718f",
            gridColor="#dddff0",
            gridOpacity=0.8,
            labelColor="#4b4760",
            tickColor="#77718f",
            titleColor="#343047",
            titleFontSize=12,
            titlePadding=12,
        )
    )
