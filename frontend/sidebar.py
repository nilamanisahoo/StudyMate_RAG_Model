
import streamlit as st
import requests

from auth import logout

from api_client import (
    get_conversations,
    create_new_chat,
    get_conversation_messages,
    create_share_link_api,
    revoke_share_link_api,
    delete_conversation_api,
)


def render_sidebar():
    """Render the StudyMate sidebar and handle chat management."""

    with st.sidebar:

        st.write("Logged in as:")
        st.write(st.session_state["user"]["email"])
        if st.button("Log out", use_container_width=True):
            logout()
        st.divider()

        # -----------------------------------------
        # New Chat
        # -----------------------------------------

        if st.button("➕ New Chat", use_container_width=True):

            try:
                new_chat = create_new_chat()

                st.session_state["conversation_id"] = new_chat["id"]
                st.session_state["chat_messages"] = []
                st.session_state["conversation_is_new"] = True

                st.rerun()

            except requests.exceptions.RequestException as error:
                st.error(f"Could not create a new chat: {error}")

        # -----------------------------------------
        # Chat History
        # -----------------------------------------

        st.subheader("Chat History")

        try:
            conversations = get_conversations()

            if conversations:

                for conversation in conversations:

                    conversation_id = conversation["id"]
                    title = conversation["title"]

                    # Open existing conversation.
                    if st.button(
                        title,
                        key=f"chat_{conversation_id}",
                        use_container_width=True,
                    ):

                        try:
                            result = get_conversation_messages(
                                conversation_id
                            )

                            st.session_state["conversation_id"] = conversation_id
                            st.session_state["chat_messages"] = result["messages"]
                            st.session_state["conversation_is_new"] = False

                            st.rerun()

                        except requests.exceptions.RequestException as error:
                            st.error(f"Could not load this chat: {error}")

                    # -----------------------------------------
                    # Share Conversation
                    # -----------------------------------------

                    if st.button(
                        "🔗 Share",
                        key=f"share_{conversation_id}",
                    ):

                        try:
                            result = create_share_link_api(conversation_id)

                            # Check the actual response before using its token.
                            token = result["share_token"]

                            frontend_base_url = st.session_state.get(
                                "frontend_base_url",
                                "http://localhost:8501",
                            ).rstrip("/")

                            share_url = (
                                f"{frontend_base_url}/?share={token}"
                            )

                            st.session_state["share_url"] = share_url
                            st.session_state["share_conversation_id"] = conversation_id
                            st.session_state["confirm_revoke_id"] = None

                        except (KeyError, TypeError) as error:
                            st.error(
                                f"Unexpected share API response: {error}"
                            )
                            print("SHARE API RESPONSE:", result)

                        except requests.exceptions.RequestException as error:
                            st.error(f"Could not create share link: {error}")

                    # -----------------------------------------
                    # Revoke Share
                    # -----------------------------------------

                    if st.button(
                        "🚫 Revoke Share",
                        key=f"revoke_{conversation_id}",
                    ):
                        st.session_state["confirm_revoke_id"] = conversation_id

                    # -----------------------------------------
                    # Delete Conversation
                    # -----------------------------------------

                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_{conversation_id}",
                    ):
                        st.session_state["confirm_delete_id"] = conversation_id

            else:
                st.caption("No previous conversations yet.")

        except requests.exceptions.RequestException as error:
            st.warning(f"Could not load chat history: {error}")

        # -----------------------------------------
        # Delete Confirmation
        # -----------------------------------------

        confirm_delete_id = st.session_state.get("confirm_delete_id")

        if confirm_delete_id:

            st.warning(
                "Are you sure you want to delete this conversation?"
            )

            if st.button("Yes, delete", key="confirm_delete"):

                try:
                    delete_conversation_api(confirm_delete_id)

                    if st.session_state.get("conversation_id") == confirm_delete_id:
                        st.session_state["conversation_id"] = None
                        st.session_state["chat_messages"] = []
                        st.session_state["conversation_is_new"] = False

                    if st.session_state.get("share_conversation_id") == confirm_delete_id:
                        st.session_state.pop("share_url", None)
                        st.session_state.pop("share_conversation_id", None)

                    st.session_state["confirm_delete_id"] = None

                    st.rerun()

                except requests.exceptions.RequestException as error:
                    st.error(f"Could not delete conversation: {error}")

            if st.button("Cancel", key="cancel_delete"):
                st.session_state["confirm_delete_id"] = None
                st.rerun()

        # -----------------------------------------
        # Revoke Confirmation
        # -----------------------------------------

        confirm_revoke_id = st.session_state.get("confirm_revoke_id")

        if confirm_revoke_id:

            st.warning(
                "Are you sure you want to disable this share link?"
            )

            if st.button("Yes, revoke", key="confirm_revoke"):

                try:
                    revoke_share_link_api(confirm_revoke_id)

                    if st.session_state.get("share_conversation_id") == confirm_revoke_id:
                        st.session_state.pop("share_url", None)
                        st.session_state.pop("share_conversation_id", None)

                    st.session_state["confirm_revoke_id"] = None

                    st.success("Share link revoked successfully.")

                    st.rerun()

                except requests.exceptions.RequestException as error:
                    st.error(f"Could not revoke share link: {error}")

            if st.button("Cancel", key="cancel_revoke"):
                st.session_state["confirm_revoke_id"] = None
                st.rerun()

        # -----------------------------------------
        # Display Share Link
        # -----------------------------------------

        if st.session_state.get("share_url"):

            st.divider()

            st.write("🔗 Your share link:")

            st.caption("Copy this link and send it to your friend:")

            st.code(
                st.session_state["share_url"],
                language=None,
            )

        st.divider()

        # -----------------------------------------
        # Logout
        # -----------------------------------------

        
