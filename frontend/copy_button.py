
import json
import streamlit.components.v1 as components


def show_copy_button(answer, button_id):
    """
    Display a button that copies the supplied answer.
    """

    # Safely convert the Python answer into JavaScript format.
    answer_json = json.dumps(answer).replace("<", "\\u003c")

    components.html(
        f"""
        <button
            id="{button_id}"
            style="
                padding: 8px 14px;
                border: 1px solid #888;
                border-radius: 8px;
                background: transparent;
                cursor: pointer;
                font-size: 14px;
                color: white;
            "
        >
            📋 Copy Answer
        </button>

        <span
            id="copy_status"
            style="margin-left: 10px;"
        ></span>

        <script>
            const answer = {answer_json};

            document.getElementById("{button_id}").onclick = async function() {{
                try {{
                    await navigator.clipboard.writeText(answer);

                    document.getElementById("copy_status").textContent =
                        "Copied!";

                }} catch (error) {{

                    document.getElementById("copy_status").textContent =
                        "Copy failed. Please select the answer manually.";
                }}
            }};
        </script>
        """,
        height=50,
    )
