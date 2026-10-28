
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


# Find the StudyMate project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables from the root .env file.
load_dotenv(PROJECT_ROOT / ".env")


def verify_access_token(access_token: str) -> str:
    """
    Verify a Supabase access token and return the verified user ID.
    """

    if not access_token or not access_token.strip():
        raise ValueError("Access token is missing.")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "SUPABASE_URL or SUPABASE_KEY is missing from .env."
        )

    supabase = create_client(supabase_url, supabase_key)

    try:
        response = supabase.auth.get_user(access_token)
        user = response.user

        if user is None or not user.id:
            raise ValueError("Access token is invalid.")

        return str(user.id)

    except ValueError:
        raise
    except Exception as error:
        raise ValueError("Invalid or expired access token.") from error
