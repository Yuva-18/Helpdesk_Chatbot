"""Pydantic request/response models for the /chat endpoint."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's helpdesk question.")


class ChatResponse(BaseModel):
    answer: str
    is_confident: bool
    used_llm: bool
    matched_rule_id: str | None = None
    category: str | None = None
    support_email: str | None = None
    source_url: str | None = None
    reason: str
