
import os
from pathlib import Path
import hashlib
import secrets
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


project_root = Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")


def get_database_engine():
    """Create a connection to the Supabase PostgreSQL database."""

    database_url = os.getenv("SUPABASE_DATABASE_URL")

    if not database_url:
        raise ValueError(
            "SUPABASE_DATABASE_URL is missing from .env"
        )

    return create_engine(database_url)


def create_conversation(
    user_id: str,
    title: str = "New Chat",
) -> str:
    """Create a new conversation and return its ID."""

    if not user_id:
        raise ValueError("user_id is required.")

    engine = get_database_engine()

    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO chat_conversations (
                        user_id,
                        title
                    )
                    VALUES (
                        :user_id,
                        :title
                    )
                    RETURNING id
                """),
                {
                    "user_id": user_id,
                    "title": title,
                },
            )

            conversation_id = result.scalar_one()

            return str(conversation_id)

    finally:
        engine.dispose()


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    user_id: str,
) -> None:
    """Save a user or assistant message to a conversation."""

    if not conversation_id:
        raise ValueError("conversation_id is required.")

    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role.")

    if not content.strip():
        raise ValueError("Message content cannot be empty.")

    engine = get_database_engine()

    try:
        with engine.begin() as connection:

            # Verify that this conversation belongs to the user.
            result = connection.execute(
                text("""
                    SELECT id
                    FROM chat_conversations
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

            if result.scalar_one_or_none() is None:
                raise ValueError(
                    "Conversation not found or access denied."
                )

            # Save the message.
            connection.execute(
                text("""
                    INSERT INTO chat_messages (
                        conversation_id,
                        role,
                        content
                    )
                    VALUES (
                        :conversation_id,
                        :role,
                        :content
                    )
                """),
                {
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                },
            )

            # Update the conversation's last-updated time.
            connection.execute(
                text("""
                    UPDATE chat_conversations
                    SET updated_at = NOW()
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

    finally:
        engine.dispose()


def get_user_conversations(user_id: str) -> list[dict]:
    """Get all conversations belonging to one user."""

    if not user_id:
        raise ValueError("user_id is required.")

    engine = get_database_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT id, title, created_at, updated_at
                    FROM chat_conversations
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                """),
                {
                    "user_id": user_id,
                },
            )

            return [
                {
                    "id": str(row.id),
                    "title": row.title,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
                for row in result
            ]

    finally:
        engine.dispose()


def get_conversation_messages(
    conversation_id: str,
    user_id: str,
) -> list[dict]:
    """Get messages from a conversation owned by the user."""

    if not conversation_id or not user_id:
        raise ValueError(
            "conversation_id and user_id are required."
        )

    engine = get_database_engine()

    try:
        with engine.connect() as connection:
                        # Verify that the conversation belongs to the user.
            ownership_result = connection.execute(
                text("""
                    SELECT id
                    FROM chat_conversations
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

            if ownership_result.scalar_one_or_none() is None:
                raise ValueError(
                    "Conversation not found or access denied."
                )
            result = connection.execute(
                text("""
                    SELECT
                        m.id,
                        m.role,
                        m.content,
                        m.created_at
                    FROM chat_messages AS m
                    JOIN chat_conversations AS c
                        ON m.conversation_id = c.id
                    WHERE c.id = :conversation_id
                      AND c.user_id = :user_id
                    ORDER BY m.created_at ASC
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

            return [
                {
                    "id": str(row.id),
                    "role": row.role,
                    "content": row.content,
                    "created_at": row.created_at,
                }
                for row in result
            ]

    finally:
        engine.dispose()

def update_conversation_title(
    conversation_id: str,
    user_id: str,
    title: str,
) -> None:

    if not conversation_id or not user_id:
        raise ValueError("Conversation ID and user ID are required.")

    title = title.strip()

    if not title:
        raise ValueError("Conversation title cannot be empty.")

    # Keep the title within the database/API limit.
    title = title[:200]

    engine = get_database_engine()

    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    UPDATE chat_conversations
                    SET title = :title,
                        updated_at = NOW()
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                    RETURNING id
                """),
                {
                    "title": title,
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

            if result.scalar_one_or_none() is None:
                raise ValueError("Conversation not found or access denied.")

    finally:
        engine.dispose()

def delete_conversation(
    conversation_id: str,
    user_id: str,
) -> None:

    if not conversation_id or not user_id:
        raise ValueError(
            "Conversation ID and user ID are required."
        )

    engine = get_database_engine()

    try:
        with engine.begin() as connection:

            # Check that this conversation belongs to the user.
            result = connection.execute(
                text("""
                    SELECT id
                    FROM chat_conversations
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

            if result.scalar_one_or_none() is None:
                raise ValueError(
                    "Conversation not found or access denied."
                )

            # Delete all messages belonging to this conversation.
            connection.execute(
                text("""
                    DELETE FROM chat_messages
                    WHERE conversation_id = :conversation_id
                """),
                {
                    "conversation_id": conversation_id,
                },
            )

            # Delete the conversation itself.
            connection.execute(
                text("""
                    DELETE FROM chat_conversations
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

    finally:
        engine.dispose()


def create_share_link(
    conversation_id: str,
    user_id: str,
) -> str:

    if not conversation_id or not user_id:
        raise ValueError(
            "Conversation ID and user ID are required."
        )

    # Generate a secure random token.
    token = secrets.token_urlsafe(32)

    # Convert the token into a SHA-256 hash.
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    engine = get_database_engine()

    try:
        with engine.begin() as connection:

            # Check that the conversation belongs to this user.
            result = connection.execute(
                text("""
                    SELECT id
                    FROM chat_conversations
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

            if result.scalar_one_or_none() is None:
                raise ValueError(
                    "Conversation not found or access denied."
                )

            # Revoke any previous active share links.
            connection.execute(
                text("""
                    UPDATE chat_share_links
                    SET revoked_at = NOW()
                    WHERE conversation_id = :conversation_id
                      AND revoked_at IS NULL
                """),
                {
                    "conversation_id": conversation_id,
                },
            )

            # Store the hash, never the original token.
            connection.execute(
                text("""
                    INSERT INTO chat_share_links (
                        conversation_id,
                        created_by,
                        token_hash
                    )
                    VALUES (
                        :conversation_id,
                        :user_id,
                        :token_hash
                    )
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "token_hash": token_hash,
                },
            )

            # Return the original token only once.
            return token

    finally:
        engine.dispose()

def get_shared_conversation(token: str) -> dict:
    if not token:
        raise ValueError("Share token is required.")

    # Convert the received token into its SHA-256 hash.
    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    engine = get_database_engine()

    try:
        with engine.connect() as connection:

            # Find a valid, non-revoked, non-expired share link.
            result = connection.execute(
                text("""
                    SELECT
                        c.id,
                        c.title
                    FROM chat_share_links AS s
                    JOIN chat_conversations AS c
                        ON s.conversation_id = c.id
                    WHERE s.token_hash = :token_hash
                      AND s.revoked_at IS NULL
                      AND (
                          s.expires_at IS NULL
                          OR s.expires_at > NOW()
                      )
                """),
                {"token_hash": token_hash},
            )

            conversation = result.mappings().one_or_none()

            if conversation is None:
                raise ValueError(
                    "Share link is invalid, expired, or revoked."
                )

            # Retrieve the conversation messages.
            message_result = connection.execute(
                text("""
                    SELECT role, content, created_at
                    FROM chat_messages
                    WHERE conversation_id = :conversation_id
                    ORDER BY created_at ASC
                """),
                {"conversation_id": conversation["id"]},
            )

            messages = [
                {
                    "role": row.role,
                    "content": row.content,
                    "created_at": row.created_at.isoformat(),
                }
                for row in message_result
            ]

            return {
                "conversation_id": str(conversation["id"]),
                "title": conversation["title"],
                "messages": messages,
            }

    finally:
        engine.dispose()


def revoke_share_link(
    conversation_id: str,
    user_id: str,
) -> None:

    if not conversation_id or not user_id:
        raise ValueError(
            "Conversation ID and user ID are required."
        )

    engine = get_database_engine()

    try:
        with engine.begin() as connection:

            # Check that this conversation belongs to the user.
            result = connection.execute(
                text("""
                    SELECT id
                    FROM chat_conversations
                    WHERE id = :conversation_id
                      AND user_id = :user_id
                """),
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                },
            )

            if result.scalar_one_or_none() is None:
                raise ValueError(
                    "Conversation not found or access denied."
                )

            # Revoke all active share links for this conversation.
            connection.execute(
                text("""
                    UPDATE chat_share_links
                    SET revoked_at = NOW()
                    WHERE conversation_id = :conversation_id
                      AND revoked_at IS NULL
                """),
                {
                    "conversation_id": conversation_id,
                },
            )

    finally:
        engine.dispose()
