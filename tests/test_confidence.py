"""Unit tests for app/core/confidence.py."""

import pytest

from app.config import settings
from app.core.confidence import evaluate_confidence


def test_empty_retrieval_is_not_confident_with_no_category():
    result = evaluate_confidence([])

    assert result.is_confident is False
    assert result.top_rule is None
    assert result.category is None
    assert result.support_email is None


def test_confident_match_uses_the_rule_own_support_email(rule_factory):
    rule = rule_factory(
        category="Hpce",
        support_email="rule-specific@example.com",
        score=settings.confidence_threshold + 0.1,
    )

    result = evaluate_confidence([rule])

    assert result.is_confident is True
    assert result.top_rule is rule
    assert result.category == "Hpce"
    assert result.support_email == "rule-specific@example.com"


def test_score_exactly_at_threshold_counts_as_confident(rule_factory):
    rule = rule_factory(score=settings.confidence_threshold)

    result = evaluate_confidence([rule])

    assert result.is_confident is True


@pytest.mark.parametrize(
    "category, expected_email_attr",
    [
        ("Eservices", "eservices_support_email"),
        ("Network", "network_support_email"),
        ("Hpce", "hpce_support_email"),
    ],
)
def test_low_confidence_routes_to_the_correct_category_email(rule_factory, category, expected_email_attr):
    rule = rule_factory(
        category=category,
        support_email="should-not-be-used@example.com",
        score=settings.confidence_threshold - 0.1,
    )

    result = evaluate_confidence([rule])

    assert result.is_confident is False
    assert result.category == category
    assert result.support_email == getattr(settings, expected_email_attr)


def test_low_confidence_unknown_category_defaults_to_eservices_email(rule_factory):
    rule = rule_factory(category="SomeNewCategory", score=settings.confidence_threshold - 0.1)

    result = evaluate_confidence([rule])

    assert result.is_confident is False
    assert result.support_email == settings.eservices_support_email
