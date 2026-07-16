"""POST /chat endpoint: receives a user question, returns an answer or a fallback."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.api.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.rag_pipeline import answer_query
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    logger.info("Received chat request: %r", request.question)
    try:
        result = answer_query(request.question)
    except Exception:
        logger.exception("Unexpected error while answering chat request: %r", request.question)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing your question. Please try again.",
        )
    return ChatResponse(**asdict(result))
