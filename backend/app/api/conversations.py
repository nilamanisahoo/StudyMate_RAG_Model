import time
import traceback
from fastapi import APIRouter, Depends, HTTPException, status,Request
from .dependencies import get_current_user_id, limiter
from ..schemas.chat import (
    ConversationCreateRequest,
    ConversationResponse,
    ChatMessageResponse,
    ConversationMessagesResponse,
    ChatMessageCreateRequest,
    ConversationTitleUpdateRequest
)
from ..services.chat_service import (
    create_conversation,
    get_user_conversations,
    get_conversation_messages,
    save_message,
    update_conversation_title,
    delete_conversation,
    create_share_link,
    get_shared_conversation,
    revoke_share_link
)
from .dependencies import get_current_user_id


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_conversation(
    request: ConversationCreateRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        conversation_id = create_conversation(
            user_id=user_id,
            title=request.title,
        )

        return ConversationResponse(
            id=conversation_id,
            title=request.title,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation.",
        )


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def list_conversations(
    user_id: str = Depends(get_current_user_id),
):
    start_time = time.time()

    print("1. Conversations endpoint started.")

    try:
        print("2. Calling get_user_conversations().")

        conversations = get_user_conversations(
            user_id=user_id,
        )

        print(
            f"3. Database query completed in "
            f"{time.time() - start_time:.2f} seconds."
        )

        return [
            ConversationResponse(
                id=conversation["id"],
                title=conversation["title"],
            )
            for conversation in conversations
        ]

    except Exception:
        print("4. Error while retrieving conversations:")
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations.",
        )

@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
def list_conversation_messages(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        messages = get_conversation_messages(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        return ConversationMessagesResponse(
            conversation_id=conversation_id,
            messages=[
                ChatMessageResponse(
                    id=message["id"],
                    role=message["role"],
                    content=message["content"],
                    created_at=message["created_at"].isoformat(),
                )
                for message in messages
            ],
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation messages.",
        )

@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def create_conversation_message(
    conversation_id: str,
    request: ChatMessageCreateRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        save_message(
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            user_id=user_id,
        )

        return {"message": "Message saved successfully."}

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to save message.",
        )

@router.patch("/{conversation_id}")
def rename_conversation(
    conversation_id: str,
    request: ConversationTitleUpdateRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        update_conversation_title(
            conversation_id=conversation_id,
            user_id=user_id,
            title=request.title,
        )

        return {
            "message": "Conversation title updated successfully.",
            "title": request.title,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to update conversation title.",
        )

@router.delete("/{conversation_id}")
def remove_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        return {
            "message": "Conversation deleted successfully."
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation.",
        )

@router.post("/{conversation_id}/share")
def share_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        token = create_share_link(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        return {
            "message": "Share link created successfully.",
            "share_token": token,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to create share link.",
        )

@router.get("/shared/{token}")
@limiter.limit("30/minute")
def view_shared_conversation(
    request:Request,
    token: str):
    try:
        return get_shared_conversation(token=token)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve shared conversation.",
        )

@router.delete("/{conversation_id}/share")
def remove_share_link(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        revoke_share_link(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        return {
            "message": "Share link revoked successfully."
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke share link.",
        )