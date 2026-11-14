
import html
import streamlit.components.v1 as components


def show_elapsed_timer(label):
    """Display a live elapsed-time counter."""

    safe_label = html.escape(label)

    components.html(
        f"""
        <div style="
            font-family: Arial, sans-serif;
            padding: 8px 0;
            color: inherit;
        ">
            <span style="font-size: 14px;">
                {safe_label}
            </span>

            <span id="elapsed"
                style="
                    font-size: 22px;
                    font-weight: bold;
                    margin-left: 10px;
                    font-variant-numeric: tabular-nums;
                ">
                00:00
            </span>
        </div>

        <script>
            const startTime = Date.now();

            function updateTimer() {{
                const elapsed = Math.floor(
                    (Date.now() - startTime) / 1000
                );

                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;

                document.getElementById("elapsed").textContent =
                    String(minutes).padStart(2, "0") + ":" +
                    String(seconds).padStart(2, "0");
            }}

            updateTimer();
            setInterval(updateTimer, 1000);
        </script>
        """,
        height=65,
    )
