
import os
import streamlit as st
import requests

from pathlib import Path
from dotenv import load_dotenv
from auth import show_authentication
from api_client import get_shared_conversation_api
from sidebar import render_sidebar
from pdf_upload import render_pdf_upload
from chat import render_chat


# -----------------------------------------
# Application configuration
# -----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

st.set_page_config(
    page_title="StudyMate RAG",
    page_icon="📚",
    layout="wide",
)

# Frontend URL used when creating share links.
st.session_state["frontend_base_url"] = os.getenv(
    "FRONTEND_BASE_URL",
    "http://localhost:8501",
).rstrip("/")


# -----------------------------------------
# Shared conversation view
# -----------------------------------------

share_token = st.query_params.get("share")

if share_token:

    st.title("StudyMate - Shared Conversation")

    st.caption(
        "You are viewing a read-only shared conversation."
    )

    try:
        shared_chat = get_shared_conversation_api(share_token)

        st.subheader(shared_chat["title"])

        st.divider()

        for message in shared_chat["messages"]:

            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        st.info(
            "This is a shared conversation. "
            "You cannot send messages or modify the original chat."
        )

    except requests.exceptions.HTTPError:

        st.error(
            "This share link is invalid, expired, or revoked."
        )

    except requests.exceptions.RequestException:

        st.error(
            "Could not load the shared conversation. "
            "Please try again."
        )

    st.stop()


# -----------------------------------------
# Authentication
# -----------------------------------------

if not show_authentication():
    st.stop()


# -----------------------------------------
# Initialize user session
# -----------------------------------------

user_id = st.session_state["user"]["id"]

# Reset chat data when a different user logs in.
if st.session_state.get("chat_owner_id") != user_id:

    st.session_state["chat_owner_id"] = user_id

    st.session_state["chat_messages"] = []

    st.session_state["conversation_id"] = None

    st.session_state["conversation_is_new"] = False


# Initialize required session variables.
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

if "conversation_is_new" not in st.session_state:
    st.session_state["conversation_is_new"] = False


# -----------------------------------------
# Main application interface
# -----------------------------------------

st.title("📚 StudyMate RAG")

st.write(
    "Your personal PDF question-answering assistant."
)


# -----------------------------------------
# Sidebar
# -----------------------------------------

render_sidebar()


# -----------------------------------------
# PDF upload
# -----------------------------------------

render_pdf_upload()


# -----------------------------------------
# Chat interface
# -----------------------------------------

render_chat()
