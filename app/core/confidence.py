"""Scores retrieval/answer confidence and decides whether to answer or route to fallback."""

from dataclasses import dataclass

from app.config import settings
from app.core.retriever import RetrievedRule
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConfidenceResult:
    """The outcome of evaluating retrieved rules: either confident enough to
    answer from the top match, or routed to a fallback category + support email."""

    is_confident: bool
    top_rule: RetrievedRule | None
    category: str | None
    support_email: str | None
    reason: str


def _support_email_for_category(category: str) -> str:
    if category == "Eservices":
        return settings.eservices_support_email
    if category == "Network":
        return settings.network_support_email
    logger.warning("Unknown category %r; defaulting to Eservices support email", category)
    return settings.eservices_support_email


def evaluate_confidence(retrieved_rules: list[RetrievedRule]) -> ConfidenceResult:
    """Decides whether the top retrieved rule is a good enough match to answer
    from, or whether the query should be routed to a fallback support email
    instead of letting the LLM guess."""
    if not retrieved_rules:
        logger.warning("No rules retrieved; routing to fallback with no category guess")
        return ConfidenceResult(
            is_confident=False,
            top_rule=None,
            category=None,
            support_email=None,
            reason="No matching information was found in the knowledge base.",
        )

    top_rule = retrieved_rules[0]

    if top_rule.score >= settings.confidence_threshold:
        logger.info(
            "Confident match: rule=%s score=%.3f >= threshold=%.3f",
            top_rule.rule_id,
            top_rule.score,
            settings.confidence_threshold,
        )
        return ConfidenceResult(
            is_confident=True,
            top_rule=top_rule,
            category=top_rule.category,
            support_email=top_rule.support_email,
            reason=f"Matched '{top_rule.rule_id}' with score {top_rule.score:.3f}.",
        )

    support_email = _support_email_for_category(top_rule.category)
    logger.info(
        "Low confidence: rule=%s score=%.3f < threshold=%.3f, routing to %s (%s)",
        top_rule.rule_id,
        top_rule.score,
        settings.confidence_threshold,
        top_rule.category,
        support_email,
    )
    return ConfidenceResult(
        is_confident=False,
        top_rule=top_rule,
        category=top_rule.category,
        support_email=support_email,
        reason=(
            f"The best match (score {top_rule.score:.3f}) did not meet the confidence "
            f"threshold ({settings.confidence_threshold}), so this was routed to the "
            f"{top_rule.category} support team instead of guessing."
        ),
    )
