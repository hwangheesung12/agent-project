import streamlit as st


def apply_clay_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --clay-bg: #eef2ff;
            --clay-surface: #f7f8ff;
            --clay-surface-deep: #dfe6fa;
            --clay-primary: #7047eb;
            --clay-primary-dark: #5124c8;
            --clay-primary-soft: #a58af7;
            --clay-button-text: #34245f;
            --clay-button-primary-text: #ffffff;
            --clay-accent: #d8ccff;
            --clay-text: #272341;
            --clay-muted: #6c6983;
            --clay-radius-xl: 32px;
            --clay-radius-lg: 22px;
            --clay-radius-md: 16px;
            --clay-shadow:
                12px 14px 28px rgba(104, 112, 156, 0.22),
                -10px -10px 24px rgba(255, 255, 255, 0.9),
                inset 2px 2px 6px rgba(255, 255, 255, 0.76),
                inset -3px -3px 7px rgba(106, 113, 154, 0.1);
            --clay-shadow-small:
                6px 7px 14px rgba(104, 112, 156, 0.2),
                -6px -6px 14px rgba(255, 255, 255, 0.86),
                inset 2px 2px 4px rgba(255, 255, 255, 0.72),
                inset -2px -2px 5px rgba(106, 113, 154, 0.1);
        }

        html, body, [class*="st-"], [class*="css"] {
            color: var(--clay-text);
        }

        .block-container {
            max-width: 1440px;
            padding-top: 2.35rem;
            padding-bottom: 3rem;
        }

        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 7% 8%, rgba(137, 104, 243, 0.14), transparent 23rem),
                radial-gradient(circle at 95% 92%, rgba(112, 71, 235, 0.12), transparent 28rem),
                linear-gradient(145deg, #f6f7fc 0%, var(--clay-bg) 52%, #e5eafd 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(155deg, #f4f6ff, #e2e8fb);
            border-right: 3px solid rgba(255, 255, 255, 0.8);
            box-shadow:
                12px 0 28px rgba(101, 108, 149, 0.16),
                inset -5px 0 14px rgba(117, 128, 171, 0.09),
                inset 5px 0 12px rgba(255, 255, 255, 0.7);
        }

        h1, h2, h3 {
            color: var(--clay-text) !important;
            letter-spacing: -0.035em;
        }

        h1 {
            font-size: clamp(2.2rem, 4vw, 3.6rem) !important;
            font-weight: 900 !important;
            margin-bottom: 0 !important;
        }

        h2, h3 {
            font-weight: 850 !important;
        }

        .dashboard-kicker {
            display: inline-flex;
            align-items: center;
            margin-bottom: 0.55rem;
            padding: 0.45rem 0.8rem;
            color: var(--clay-primary-dark);
            background: rgba(255, 255, 255, 0.58);
            border: 1px solid rgba(255, 255, 255, 0.9);
            border-radius: 999px;
            box-shadow: var(--clay-shadow-small);
            font-size: 0.72rem;
            font-weight: 900;
            letter-spacing: 0.1em;
        }

        .dashboard-subtitle {
            margin: 0.2rem 0 1.35rem;
            color: var(--clay-muted);
            font-size: 1rem;
            font-weight: 600;
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        button[kind="primary"],
        button[kind="secondary"] {
            min-height: 3rem;
            color: var(--clay-button-text) !important;
            background: linear-gradient(145deg, #ffffff, #ecefff) !important;
            border: 2px solid rgba(255, 255, 255, 0.64) !important;
            border-radius: var(--clay-radius-md) !important;
            box-shadow:
                6px 7px 13px rgba(102, 110, 150, 0.2),
                -6px -6px 13px rgba(255, 255, 255, 0.78),
                inset 3px 3px 7px rgba(255, 255, 255, 0.68),
                inset -4px -4px 9px rgba(108, 118, 160, 0.12) !important;
            font-family: "Inter", "Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Segoe UI", sans-serif !important;
            font-size: 0.96rem !important;
            font-weight: 700 !important;
            letter-spacing: 0 !important;
            line-height: 1.25 !important;
            transition: transform 0.16s ease, box-shadow 0.16s ease;
        }

        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stDownloadButton"] > button[kind="primary"],
        button[kind="primary"] {
            color: var(--clay-button-primary-text) !important;
            background: linear-gradient(145deg, #8f70f2, #6843d8) !important;
            box-shadow:
                6px 8px 14px rgba(82, 55, 171, 0.24),
                -6px -6px 13px rgba(255, 255, 255, 0.78),
                inset 3px 3px 7px rgba(255, 255, 255, 0.32),
                inset -4px -4px 9px rgba(55, 26, 145, 0.18) !important;
        }

        [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(145deg, #63b7c7, #347f9b) !important;
            border-color: rgba(255, 255, 255, 0.72) !important;
            box-shadow:
                6px 8px 14px rgba(55, 117, 139, 0.24),
                -6px -6px 13px rgba(255, 255, 255, 0.78),
                inset 3px 3px 7px rgba(255, 255, 255, 0.34),
                inset -4px -4px 9px rgba(27, 90, 111, 0.18) !important;
        }

        div[data-testid="stButton"] > button:disabled,
        div[data-testid="stDownloadButton"] > button:disabled,
        div[data-testid="stButton"] > button:disabled:hover,
        div[data-testid="stDownloadButton"] > button:disabled:hover {
            color: #77718f !important;
            background: linear-gradient(145deg, #f4f5fb, #e5e9f7) !important;
            box-shadow:
                inset 3px 3px 7px rgba(119, 130, 173, 0.16),
                inset -4px -4px 8px rgba(255, 255, 255, 0.72) !important;
            opacity: 1 !important;
            transform: none;
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            transform: translateY(-3px) scale(1.015);
            box-shadow:
                9px 11px 18px rgba(102, 110, 150, 0.26),
                -7px -7px 16px rgba(255, 255, 255, 0.86),
                inset 4px 4px 8px rgba(255, 255, 255, 0.7),
                inset -5px -5px 11px rgba(108, 118, 160, 0.16) !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stDownloadButton"] > button[kind="primary"]:hover,
        button[kind="primary"]:hover {
            box-shadow:
                9px 11px 18px rgba(82, 55, 171, 0.3),
                -7px -7px 16px rgba(255, 255, 255, 0.86),
                inset 4px 4px 8px rgba(255, 255, 255, 0.38),
                inset -5px -5px 11px rgba(55, 26, 145, 0.22) !important;
        }

        [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover {
            box-shadow:
                9px 11px 18px rgba(55, 117, 139, 0.3),
                -7px -7px 16px rgba(255, 255, 255, 0.86),
                inset 4px 4px 8px rgba(255, 255, 255, 0.4),
                inset -5px -5px 11px rgba(27, 90, 111, 0.22) !important;
        }

        div[data-testid="stButton"] > button:active,
        div[data-testid="stDownloadButton"] > button:active {
            transform: translateY(2px);
            box-shadow:
                3px 3px 8px rgba(102, 110, 150, 0.24),
                inset 6px 6px 12px rgba(108, 118, 160, 0.2),
                inset -4px -4px 8px rgba(255, 255, 255, 0.42) !important;
        }

        div[data-testid="stMetric"] {
            min-height: 118px;
            height: 100%;
            padding: 1.25rem 1.3rem;
            background: linear-gradient(145deg, #ffffff, #e4e9fa);
            border: 2px solid rgba(255, 255, 255, 0.82);
            border-radius: var(--clay-radius-lg);
            box-shadow: var(--clay-shadow);
        }

        [data-testid="stMetricLabel"] {
            color: var(--clay-muted);
            font-weight: 750;
        }

        [data-testid="stMetricValue"] {
            color: var(--clay-primary-dark);
            font-weight: 900;
        }

        [data-testid="stHorizontalBlock"] {
            align-items: stretch;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            min-width: 0;
        }

        [data-testid="stForm"],
        [data-testid="stVegaLiteChart"],
        [data-testid="stArrowVegaLiteChart"],
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            padding: 1.05rem;
            background: linear-gradient(145deg, #ffffff, #e7ebf9);
            border: 2px solid rgba(255, 255, 255, 0.86);
            border-radius: var(--clay-radius-lg);
            box-shadow: var(--clay-shadow);
        }

        [data-testid="stDataFrame"] {
            overflow: hidden;
        }

        [data-testid="stVegaLiteChart"],
        [data-testid="stArrowVegaLiteChart"] {
            box-sizing: border-box;
            display: flex;
            align-items: center;
            width: calc(100% - 8px);
            max-width: calc(100% - 8px);
            min-height: 390px;
            margin: 4px;
            padding: 0.85rem 0.75rem 0.65rem;
            overflow: hidden;
            background:
                radial-gradient(circle at 92% 8%, rgba(112, 71, 235, 0.08), transparent 12rem),
                linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(235, 238, 250, 0.96));
            box-shadow:
                8px 10px 22px rgba(104, 112, 156, 0.2),
                -7px -7px 18px rgba(255, 255, 255, 0.86),
                inset 2px 2px 6px rgba(255, 255, 255, 0.76),
                inset -3px -3px 7px rgba(106, 113, 154, 0.08);
        }

        [data-testid="stVegaLiteChart"] > div,
        [data-testid="stArrowVegaLiteChart"] > div {
            width: 100%;
            min-width: 0;
            max-width: 100%;
        }

        [data-testid="stVegaLiteChart"] .vega-embed,
        [data-testid="stArrowVegaLiteChart"] .vega-embed,
        [data-testid="stVegaLiteChart"] .vega-embed > div,
        [data-testid="stArrowVegaLiteChart"] .vega-embed > div {
            width: 100%;
            min-width: 0;
            max-width: 100%;
        }

        [data-testid="stVegaLiteChart"] canvas,
        [data-testid="stVegaLiteChart"] svg,
        [data-testid="stArrowVegaLiteChart"] canvas,
        [data-testid="stArrowVegaLiteChart"] svg {
            max-width: 100% !important;
        }

        [data-testid="stDataFrame"] [role="columnheader"] {
            color: var(--clay-text);
            background: #e9e3ff;
            font-weight: 800;
        }

        [data-testid="stAlert"] {
            border: 3px solid rgba(255, 255, 255, 0.66);
            border-radius: var(--clay-radius-md);
            box-shadow: var(--clay-shadow-small);
        }

        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        [data-testid="stNumberInputContainer"],
        [data-testid="stTextInputRootElement"] {
            background: linear-gradient(145deg, #e2e9ff, #f7f8ff) !important;
            border: 2px solid rgba(255, 255, 255, 0.82) !important;
            border-radius: 16px !important;
            box-shadow:
                inset 5px 5px 10px rgba(119, 130, 173, 0.22),
                inset -5px -5px 10px rgba(255, 255, 255, 0.85),
                3px 4px 8px rgba(111, 121, 162, 0.14) !important;
        }

        input:focus,
        [data-baseweb="select"] *:focus,
        button:focus-visible {
            outline: 3px solid rgba(112, 71, 235, 0.32) !important;
            outline-offset: 2px;
        }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.65rem;
            width: fit-content;
            padding: 0.55rem;
            background: linear-gradient(145deg, #e3e8f9, #ffffff);
            border: 2px solid rgba(255, 255, 255, 0.82);
            border-radius: 18px;
            box-shadow: var(--clay-shadow-small);
        }

        [data-testid="stTabs"] button[data-baseweb="tab"] {
            min-width: 105px;
            padding: 0.62rem 1.15rem;
            border-radius: 16px;
            color: var(--clay-muted);
            font-weight: 800;
        }

        [data-testid="stTabs"] button[aria-selected="true"] {
            color: white !important;
            background: linear-gradient(145deg, #8058ed, var(--clay-primary-dark));
            box-shadow:
                6px 7px 12px rgba(79, 51, 169, 0.3),
                inset 3px 3px 7px rgba(255, 255, 255, 0.38),
                inset -4px -4px 8px rgba(55, 26, 145, 0.2);
        }

        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            display: none;
        }

        [data-testid="stSlider"] {
            padding: 0.8rem 0.9rem;
            background: linear-gradient(145deg, #d7e0fa, #f3f5ff);
            border-radius: 18px;
            box-shadow: var(--clay-shadow-small);
        }

        hr {
            border: 0;
            height: 5px;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--clay-accent), var(--clay-primary), var(--clay-accent));
            box-shadow:
                3px 3px 6px rgba(107, 116, 157, 0.26),
                inset 1px 1px 2px rgba(255, 255, 255, 0.7);
        }

        @media (max-width: 760px) {
            .block-container {
                padding-top: 1.4rem;
            }
            div[data-testid="stMetric"] {
                min-height: 108px;
            }
            [data-testid="stTabs"] button[data-baseweb="tab"] {
                min-width: auto;
                padding-inline: 0.75rem;
            }
            [data-testid="stVegaLiteChart"],
            [data-testid="stArrowVegaLiteChart"] {
                width: 100%;
                max-width: 100%;
                min-height: 370px;
                margin-inline: 0;
                padding-inline: 0.55rem;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                transition: none !important;
                animation: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
