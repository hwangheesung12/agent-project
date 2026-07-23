import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from views.chat import clear_openai_credentials, render_openai_settings
from views.dashboard import render_dashboard
from views.landing import render_landing


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


def auth_is_configured() -> bool:
    required_keys = {
        "redirect_uri",
        "cookie_secret",
        "client_id",
        "client_secret",
        "server_metadata_url",
    }
    try:
        auth_settings = st.secrets.get("auth", {})
    except StreamlitSecretNotFoundError:
        return False
    if not required_keys.issubset(auth_settings):
        return False

    values = [str(auth_settings[key]).strip() for key in required_keys]
    placeholder_markers = ("your_google_", "replace_with_")
    return all(values) and not any(
        value.startswith(placeholder_markers) for value in values
    )


def logout_user() -> None:
    clear_openai_credentials()
    st.logout()


load_env()
DB_PATH = os.getenv("PUBMED_DB_PATH", "pubmed.db")

st.set_page_config(
    page_title="메디톡톡",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

auth_ready = auth_is_configured()
is_logged_in = auth_ready and bool(getattr(st.user, "is_logged_in", False))

if not is_logged_in:
    render_landing(auth_ready=auth_ready)
    st.stop()

with st.sidebar:
    render_openai_settings()
    st.divider()
    user_name = st.user.get("name", "사용자")
    user_email = st.user.get("email", "")
    st.caption(f"{user_name}님")
    if user_email:
        st.caption(user_email)
    st.button("로그아웃", on_click=logout_user, width="stretch")
    st.divider()

render_dashboard(db_path=DB_PATH)
