
import requests
import streamlit as st
from frontend.timer import show_elapsed_timer
from api_client import (
    API_URL,
    get_api_headers,
    create_new_chat,
    rename_conversation,
    save_conversation_message,
)

from copy_button import show_copy_button


def render_chat():
    """Display chat history and handle PDF question answering."""

    st.divider()
    st.subheader("💬 Chat with your PDFs")

    # -----------------------------------------
    # Step 1: Display existing messages
    # -----------------------------------------

    for index, message in enumerate(
        st.session_state["chat_messages"]
    ):

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            # Copy button for assistant answers.
            if message["role"] == "assistant":

                show_copy_button(
                    answer=message["content"],
                    button_id=f"copy_history_{index}",
                )

            # Display source references.
            if message.get("sources"):

                with st.expander("Sources"):

                    for source in message["sources"]:
                        st.write(source)

    # -----------------------------------------
    # Step 2: Accept a new question
    # -----------------------------------------

    question = st.chat_input(
        "Ask a question about your PDFs..."
    )

    if not question:
        return

    access_token = st.session_state.get("access_token")

    if not access_token:

        st.error(
            "Your login session has expired. Please log in again."
        )
        st.stop()

    # -----------------------------------------
    # Step 3: Create conversation if needed
    # -----------------------------------------

    if not st.session_state.get("conversation_id"):

        try:
            new_chat = create_new_chat()

            st.session_state["conversation_id"] = new_chat["id"]
            st.session_state["conversation_is_new"] = True

        except requests.exceptions.RequestException as error:

            st.error(
                f"Could not create conversation: {error}"
            )
            st.stop()

    conversation_id = st.session_state["conversation_id"]

    # -----------------------------------------
    # Step 4: Set title from first question
    # -----------------------------------------

    if st.session_state.get("conversation_is_new", False):

        try:
            rename_conversation(
                conversation_id=conversation_id,
                title=question,
            )

            st.session_state["conversation_is_new"] = False

        except requests.exceptions.RequestException as error:

            st.warning(
                f"Could not update chat title: {error}"
            )

    # -----------------------------------------
    # Step 5: Save user's question
    # -----------------------------------------

    try:
        save_conversation_message(
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

    except requests.exceptions.RequestException as error:

        st.error(
            f"Could not save your question: {error}"
        )
        st.stop()

    st.session_state["chat_messages"].append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # -----------------------------------------
    # Step 6: Get answer from RAG API
    # -----------------------------------------
    timer_placeholder=None
    try:

        with st.chat_message("assistant"):

            timer_placeholder = st.empty()

            with timer_placeholder.container():

                show_elapsed_timer("Searching PDFs and generating answer...")

            response = requests.post(
                    f"{API_URL}/ask",
                    headers=get_api_headers(),
                    json={
                        "question": question,
                    },
                    timeout=90,
                )
            timer_placeholder.empty()
            # Handle expired login session.
            if response.status_code == 401:

                answer = (
                    "Your login token is invalid or expired. "
                    "Please log out and log in again."
                )

                sources = []

                st.warning(answer)

            else:

                response.raise_for_status()

                result = response.json()

                answer = result.get(
                    "answer",
                    "The API did not return an answer.",
                )

                sources = result.get("sources", [])

                st.markdown(answer)

                # Copy button for the new answer.
                show_copy_button(
                    answer=answer,
                    button_id=(
                        f"copy_{conversation_id}_"
                        f"{len(st.session_state['chat_messages'])}"
                    ),
                )

                # Display source references.
                if sources:

                    with st.expander("Sources"):

                        for source in sources:
                            st.write(source)

        # -----------------------------------------
        # Step 7: Save assistant's answer
        # -----------------------------------------

        save_conversation_message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        st.session_state["chat_messages"].append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
            }
        )

        # Refresh to display saved messages and copy button.
        st.rerun()

    except requests.exceptions.ConnectionError:

        st.error(
            "Cannot connect to FastAPI. Start the backend."
        )

    except requests.exceptions.Timeout:

        st.error(
            "The request took too long. Please try again."
        )

    except requests.exceptions.HTTPError as error:

        st.error(
            f"API error (HTTP {response.status_code}): {error}. "
            "Please check the backend logs."
        )

    except requests.exceptions.RequestException as error:

        st.error(
            f"Could not complete the chat request: {error}"
        )

    except ValueError:

        st.error(
            "The API returned an invalid response."
        )
    finally:
        if timer_placeholder is not None:
            timer_placeholder.empty()