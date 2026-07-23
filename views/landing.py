import streamlit as st

from views.theme import apply_clay_theme


def render_landing(auth_ready: bool) -> None:
    apply_clay_theme()
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 14% 18%, rgba(137, 104, 243, 0.2), transparent 27%),
                radial-gradient(circle at 88% 78%, rgba(112, 71, 235, 0.16), transparent 30%),
                linear-gradient(145deg, #f7f8fc, #e6ebfb);
        }
        [data-testid="stHeader"] { background: transparent; }
        .landing-shell {
            position: relative;
            max-width: 780px;
            margin: 8vh auto 2.5rem;
            padding: 4rem 3.5rem;
            text-align: center;
            background: linear-gradient(145deg, #ffffff, #e5eafb);
            border: 3px solid rgba(255, 255, 255, 0.82);
            border-radius: 42px;
            box-shadow:
                22px 25px 48px rgba(102, 110, 150, 0.26),
                -20px -20px 42px rgba(255, 255, 255, 0.94),
                inset 6px 6px 15px rgba(255, 255, 255, 0.76),
                inset -8px -8px 18px rgba(107, 118, 164, 0.11);
        }
        .landing-badge {
            display: inline-block;
            margin-bottom: 1.45rem;
            padding: 0.65rem 1.15rem;
            color: #5124c8;
            background: linear-gradient(145deg, #ffffff, #e2e7f9);
            border: 2px solid rgba(255, 255, 255, 0.82);
            border-radius: 18px;
            box-shadow:
                7px 8px 15px rgba(118, 128, 171, 0.3),
                -6px -6px 13px rgba(255, 255, 255, 0.9),
                inset 3px 3px 7px rgba(255, 255, 255, 0.72),
                inset -4px -4px 8px rgba(108, 118, 160, 0.14);
            font-size: 0.86rem;
            font-weight: 900;
            letter-spacing: 0.08em;
        }
        .landing-title {
            margin: 0;
            color: #292441;
            font-size: clamp(3rem, 8vw, 5.4rem);
            font-weight: 900;
            letter-spacing: -0.06em;
            line-height: 1.05;
            text-shadow:
                4px 4px 2px rgba(255, 255, 255, 0.82),
                8px 10px 16px rgba(81, 36, 200, 0.18);
        }
        .landing-description {
            max-width: 610px;
            margin: 1.65rem auto 0;
            color: #6c6983;
            font-size: 1.12rem;
            line-height: 1.8;
            font-weight: 650;
        }
        .landing-features {
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 2.2rem;
        }
        .landing-feature {
            padding: 0.78rem 1.15rem;
            color: #403a63;
            background: linear-gradient(145deg, #ffffff, #e4e9f9);
            border: 2px solid rgba(255, 255, 255, 0.82);
            border-radius: 18px;
            box-shadow:
                7px 8px 14px rgba(117, 127, 169, 0.3),
                -6px -6px 12px rgba(255, 255, 255, 0.86),
                inset 3px 3px 7px rgba(255, 255, 255, 0.7),
                inset -4px -4px 8px rgba(109, 119, 161, 0.15);
            font-size: 0.9rem;
            font-weight: 850;
        }
        div[data-testid="stButton"] > button {
            min-height: 3.7rem;
            border-radius: 22px !important;
            font-size: 1rem;
            font-weight: 900;
        }
        @media (max-width: 760px) {
            .landing-shell {
                margin-top: 4vh;
                padding: 2.8rem 1.5rem;
                border-radius: 36px;
            }
        }
        </style>

        <section class="landing-shell">
            <div class="landing-badge">PUBMED INSIGHT SERVICE</div>
            <h1 class="landing-title">메디톡톡</h1>
            <p class="landing-description">
                PubMed 논문을 간편하게 수집하고, 연도별 연구 동향과 주요 저널을
                한눈에 분석하는 의학 논문 인사이트 서비스입니다.
            </p>
            <div class="landing-features">
                <span class="landing-feature">논문 자동 수집</span>
                <span class="landing-feature">연구 동향 시각화</span>
                <span class="landing-feature">검색 및 CSV 저장</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _, login_col, _ = st.columns([1.45, 1, 1.45])
    with login_col:
        if auth_ready:
            st.button(
                "Google로 로그인",
                type="primary",
                width="stretch",
                on_click=st.login,
            )
            st.caption("로그인 후 PubMed 대시보드를 이용할 수 있습니다.")
        else:
            st.button("Google로 로그인", width="stretch", disabled=True)
            st.warning(
                "Google 로그인 설정이 필요합니다. "
                "`.streamlit/secrets.toml`에 OAuth 정보를 입력하세요."
            )
