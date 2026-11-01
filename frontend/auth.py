
import os
import streamlit as st

from pathlib import Path
from dotenv import load_dotenv

from supabase import create_client
from supabase.lib.client_options import SyncClientOptions


# -----------------------------------------
# Load environment variables
# -----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")


# -----------------------------------------
# Browser-side Google OAuth component
# -----------------------------------------

google_auth_component = st.components.v2.component(
    name="studymate_google_auth",

    html="""
        <div>
            <button id="google-login-button" type="button">
                <span class="google-logo">G</span>
                <span>Continue with Google</span>
            </button>

            <p id="google-login-status" role="status"></p>
        </div>
    """,

    css="""
        #google-login-button {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            padding: 12px 16px;
            border: 1px solid #dadce0;
            border-radius: 8px;
            background: #ffffff;
            color: #3c4043;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
        }

        #google-login-button:hover {
            background: #f8f9fa;
        }

        #google-login-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .google-logo {
            font-family: Arial, sans-serif;
            font-size: 22px;
            font-weight: bold;
            color: #4285F4;
        }

        #google-login-status {
            color: var(--st-text-color);
            font-size: 0.9rem;
            text-align: center;
        }
    """,

    js="""
        export default function ({data, parentElement, setStateValue}) {

            const button = parentElement.querySelector(
                "#google-login-button"
            );

            const status = parentElement.querySelector(
                "#google-login-status"
            );

            if (!button || button.dataset.bound === "true") return;

            button.dataset.bound = "true";

            let clientPromise;

            async function getClient() {

                if (!clientPromise) {

                    clientPromise = import(
                        "https://esm.sh/@supabase/supabase-js@2"
                    ).then(({createClient}) => {

                        return createClient(data.url, data.key, {
                            auth: {
                                flowType: "pkce",
                                persistSession: true,
                                autoRefreshToken: true,
                                detectSessionInUrl: true
                            }
                        });

                    });
                }

                return clientPromise;
            }

            async function publishSession(client) {

                const {data: result, error} =
                    await client.auth.getSession();

                if (error) {
                    status.textContent = error.message;
                    return;
                }

                if (result.session) {

                    setStateValue("session", {

                        access_token: result.session.access_token,

                        refresh_token: result.session.refresh_token,

                        user: {
                            id: result.session.user.id,
                            email: result.session.user.email
                        }

                    });
                }
            }

            button.onclick = async () => {

                button.disabled = true;

                status.textContent = "Connecting to Google...";

                try {

                    const client = await getClient();

                    const {error} =
                        await client.auth.signInWithOAuth({

                            provider: "google",

                            options: {
                                redirectTo: window.location.origin
                            }

                        });

                    if (error) {

                        status.textContent = error.message;

                        button.disabled = false;
                    }

                } catch (error) {

                    status.textContent =
                        error.message || "Google login failed.";

                    button.disabled = false;
                }
            };

            getClient()

                .then(async (client) => {

                    // Handle logout.
                    if (data.logout_requested) {

                        const {error} = await client.auth.signOut();

                        if (error) {

                            status.textContent =
                                "Logout failed: " + error.message;

                            return;
                        }

                        setStateValue("session", null);

                        setStateValue("logout_complete", true);

                        status.textContent = "You have been logged out.";

                        return;
                    }

                    // Restore existing login session.
                    await publishSession(client);

                    client.auth.onAuthStateChange(
                        (event, session) => {

                            if (session) {

                                setStateValue("session", {

                                    access_token: session.access_token,

                                    refresh_token: session.refresh_token,

                                    user: {
                                        id: session.user.id,
                                        email: session.user.email
                                    }

                                });

                            }
                        }
                    );

                })

                .catch((error) => {

                    status.textContent =
                        "Could not initialize Google login: " +
                        error.message;

                });
        }
    """
)


# -----------------------------------------
# Supabase client
# -----------------------------------------

def get_supabase_client():

    """Create and reuse the Supabase client."""

    if "supabase_client" not in st.session_state:

        url = os.getenv("SUPABASE_URL")

        key = os.getenv("SUPABASE_KEY")

        if not url or not key:

            st.error(
                "SUPABASE_URL or SUPABASE_KEY is missing "
                "from the root .env file."
            )

            st.stop()

        st.session_state["supabase_client"] = create_client(
            url,
            key,
            options=SyncClientOptions(flow_type="pkce"),
        )

    return st.session_state["supabase_client"]


# -----------------------------------------
# Save authenticated user session
# -----------------------------------------

def save_user_session(response):

    """Save user information and access token."""

    if not response.user or not response.session:

        st.error(
            "Authentication did not return a valid session."
        )

        return False

    st.session_state["user"] = {
        "id": str(response.user.id),
        "email": response.user.email,
    }

    st.session_state["access_token"] = (
        response.session.access_token
    )

    st.session_state["refresh_token"] = (
        response.session.refresh_token
    )

    return True


# -----------------------------------------
# Handle Google OAuth callback
# -----------------------------------------

def handle_oauth_callback():

    """Exchange Google OAuth code for a Supabase session."""

    error = st.query_params.get("error")

    error_description = st.query_params.get(
        "error_description"
    )

    if error:

        st.error(
            f"Google OAuth error: {error} - "
            f"{error_description or 'No details provided'}"
        )

        return

    code = st.query_params.get("code")

    if not code:
        return

    supabase = get_supabase_client()

    try:

        response = supabase.auth.exchange_code_for_session(
            {"auth_code": code}
        )

        if save_user_session(response):

            st.query_params.clear()

            st.rerun()

        else:

            st.error(
                "Google login returned no valid session."
            )

    except Exception:

        st.error("Google login failed.")

        st.exception(Exception("Could not exchange OAuth code"))


# -----------------------------------------
# Google login interface
# -----------------------------------------

def google_login():

    """Display Google login and handle browser-side logout."""

    url = os.getenv("SUPABASE_URL")

    key = os.getenv("SUPABASE_KEY")

    if not url or not key:

        st.error(
            "Supabase URL or public key is missing."
        )

        return

    logout_requested = st.session_state.get(
        "logout_requested",
        False,
    )

    result = google_auth_component(

        data={
            "url": url,
            "key": key,
            "logout_requested": logout_requested,
        },

        key="google_auth",
    )

    # Wait for browser-side logout confirmation.
    if logout_requested:

        if getattr(result, "logout_complete", False):

            st.session_state["logout_requested"] = False

            st.rerun()

        return

    # Receive Google login session.
    session = getattr(result, "session", None)

    if (
        session
        and session.get("access_token")
        and session.get("user")
    ):

        st.session_state["user"] = session["user"]

        st.session_state["access_token"] = (
            session["access_token"]
        )

        st.session_state["refresh_token"] = (
            session.get("refresh_token")
        )

        st.rerun()


# -----------------------------------------
# Authentication entry point
# -----------------------------------------

def show_authentication():

    """Allow users to log in only through Google."""

    handle_oauth_callback()

    if st.session_state.get("user"):

        return True

    st.title("📚 StudyMate")

    st.subheader("Your personal PDF learning assistant")

    st.write(
        "Sign in with your Google account to access StudyMate."
    )

    st.divider()

    google_login()

    return False


# -----------------------------------------
# Logout
# -----------------------------------------

def logout():
    """Sign out from Google authentication session."""
    st.session_state["logout_requested"] = True
    st.session_state.pop("user", None)
    st.session_state.pop("access_token", None)
    st.session_state.pop("refresh_token", None)
    st.rerun()
