
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"


# -----------------------------------------
# Authentication headers
# -----------------------------------------

def get_api_headers():
    access_token = st.session_state.get("access_token")

    return {
        "Authorization": f"Bearer {access_token}"
    }


# -----------------------------------------
# Conversation APIs
# -----------------------------------------

def get_conversations():
    response = requests.get(
        f"{API_URL}/conversations",
        headers=get_api_headers(),
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def create_new_chat():
    response = requests.post(
        f"{API_URL}/conversations",
        headers=get_api_headers(),
        json={"title": "New Chat"},
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def get_conversation_messages(conversation_id):
    response = requests.get(
        f"{API_URL}/conversations/{conversation_id}/messages",
        headers=get_api_headers(),
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def save_conversation_message(conversation_id, role, content):
    response = requests.post(
        f"{API_URL}/conversations/{conversation_id}/messages",
        headers=get_api_headers(),
        json={
            "role": role,
            "content": content,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def rename_conversation(conversation_id, title):
    response = requests.patch(
        f"{API_URL}/conversations/{conversation_id}",
        headers=get_api_headers(),
        json={"title": title[:200]},
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def delete_conversation_api(conversation_id):
    response = requests.delete(
        f"{API_URL}/conversations/{conversation_id}",
        headers=get_api_headers(),
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


# -----------------------------------------
# Share conversation APIs
# -----------------------------------------

def create_share_link_api(conversation_id):
    response = requests.post(
        f"{API_URL}/conversations/{conversation_id}/share",
        headers=get_api_headers(),
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def get_shared_conversation_api(token):
    response = requests.get(
        f"{API_URL}/conversations/shared/{token}",
        timeout=15,
    )

    response.raise_for_status()
    return response.json()


def revoke_share_link_api(conversation_id):
    response = requests.delete(
        f"{API_URL}/conversations/{conversation_id}/share",
        headers=get_api_headers(),
        timeout=15,
    )

    response.raise_for_status()
    return response.json()
