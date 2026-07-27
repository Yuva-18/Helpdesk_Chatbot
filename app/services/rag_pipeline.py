"""Orchestrates retriever -> confidence -> prompt_builder -> llm into one pipeline call."""

from dataclasses import dataclass

from app.core.confidence import ConfidenceResult, evaluate_confidence
from app.core.llm import LLMError, generate_completion
from app.core.prompt_builder import STOP_SEQUENCES, build_prompt
from app.core.retriever import retriever
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChatResult:
    """The final result of answering a user's question end to end."""

    answer: str
    is_confident: bool
    used_llm: bool
    matched_rule_id: str | None
    category: str | None
    support_email: str | None
    source_url: str | None
    reason: str


def _build_fallback_message(confidence: ConfidenceResult) -> str:
    if confidence.category and confidence.support_email:
        return (
            "I'm not confident I have an accurate answer for this from the knowledge base. "
            f"Please contact the {confidence.category} support team at {confidence.support_email} "
            "for help with this."
        )
    return (
        "I'm not confident I have an accurate answer for this from the knowledge base, and "
        "couldn't determine which support team to route you to. Please contact the IT "
        "Computer Center helpdesk directly."
    )


def answer_query(question: str) -> ChatResult:
    """Answers a user's question: retrieve -> gate on confidence -> (if confident)
    build a grounded prompt and generate an answer, or (if not) return a fallback
    pointing to the right support team. The LLM is never called for a low-confidence
    match."""
    rules = retriever.retrieve(question)
    confidence = evaluate_confidence(rules)

    if not confidence.is_confident:
        return ChatResult(
            answer=_build_fallback_message(confidence),
            is_confident=False,
            used_llm=False,
            matched_rule_id=confidence.top_rule.rule_id if confidence.top_rule else None,
            category=confidence.category,
            support_email=confidence.support_email,
            source_url=None,
            reason=confidence.reason,
        )

    top_rule = confidence.top_rule
    prompt = build_prompt(question, top_rule)

    try:
        answer = generate_completion(prompt, stop=STOP_SEQUENCES)
        used_llm = True
    except LLMError as exc:
        logger.error(
            "LLM generation failed for rule=%s, falling back to the verified KB answer: %s",
            top_rule.rule_id,
            exc,
        )
        answer = top_rule.answer
        used_llm = False

    if top_rule.support_email in top_rule.answer and top_rule.support_email not in answer:
        logger.warning(
            "Verified answer for rule=%s references %s, but the generated answer doesn't "
            "contain it — the model may have altered it. Appending the verified email.",
            top_rule.rule_id,
            top_rule.support_email,
        )
        answer = f"{answer}\n\n(Verified contact: {top_rule.support_email})"

    return ChatResult(
        answer=answer,
        is_confident=True,
        used_llm=used_llm,
        matched_rule_id=top_rule.rule_id,
        category=top_rule.category,
        support_email=top_rule.support_email,
        source_url=top_rule.source_url or None,
        reason=confidence.reason,
    )
