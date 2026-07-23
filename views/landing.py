import streamlit as st


def render_landing(auth_ready: bool) -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 18% 20%, rgba(77, 171, 247, 0.16), transparent 34%),
                radial-gradient(circle at 82% 75%, rgba(32, 201, 151, 0.14), transparent 32%),
                #f8fbff;
        }
        [data-testid="stHeader"] { background: transparent; }
        .landing-shell {
            max-width: 760px;
            margin: 10vh auto 2rem;
            padding: 3.5rem 3.25rem;
            text-align: center;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(42, 111, 151, 0.14);
            border-radius: 28px;
            box-shadow: 0 24px 70px rgba(33, 74, 99, 0.12);
        }
        .landing-badge {
            display: inline-block;
            margin-bottom: 1.1rem;
            padding: 0.4rem 0.85rem;
            color: #1971c2;
            background: #e7f5ff;
            border-radius: 999px;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.04em;
        }
        .landing-title {
            margin: 0;
            color: #17324d;
            font-size: clamp(3rem, 8vw, 5.4rem);
            font-weight: 800;
            letter-spacing: -0.06em;
            line-height: 1.05;
        }
        .landing-description {
            max-width: 610px;
            margin: 1.45rem auto 0;
            color: #526779;
            font-size: 1.12rem;
            line-height: 1.8;
        }
        .landing-features {
            display: flex;
            justify-content: center;
            gap: 0.7rem;
            flex-wrap: wrap;
            margin-top: 1.8rem;
        }
        .landing-feature {
            padding: 0.55rem 0.9rem;
            color: #2b4c63;
            background: #f1f7fb;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        div[data-testid="stButton"] > button {
            min-height: 3.15rem;
            border-radius: 12px;
            font-weight: 700;
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
