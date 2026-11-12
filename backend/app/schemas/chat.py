
from pydantic import BaseModel, Field,field_validator


class ConversationCreateRequest(BaseModel):
    title: str = Field(
        default="New Chat",
        min_length=1,
        max_length=200,
        description="Title of the new conversation.",
    )


class ConversationResponse(BaseModel):
    id: str
    title: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationMessagesResponse(BaseModel):
    conversation_id: str
    messages: list[ChatMessageResponse]


class ChatMessageCreateRequest(BaseModel):
    role: str = Field(
        default="user",
        description="Only user messages can be submitted through this endpoint.",
    )

    content: str = Field(
        min_length=1,
        description="Message content.",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, value):
        if value not in ("user", "assistant"):
            raise ValueError(
            "Only user and assistant messages are allowed."
            )
        return value

class ConversationTitleUpdateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
        description="New title for the conversation.",
    )