"""Shared pytest fixtures for the test suite."""

import pytest

from app.core.retriever import RetrievedRule, retriever


def make_retrieved_rule(
    *,
    rule_id: str = "rule_01",
    category: str = "Eservices",
    question: str = "A sample question?",
    answer: str = "A sample answer.",
    support_email: str = "support@example.com",
    source_url: str | None = None,
    keywords: str = "",
    score: float = 0.9,
) -> RetrievedRule:
    return RetrievedRule(
        rule_id=rule_id,
        category=category,
        question=question,
        answer=answer,
        support_email=support_email,
        source_url=source_url,
        keywords=keywords,
        score=score,
    )


@pytest.fixture
def rule_factory():
    """Factory for building RetrievedRule test fixtures without repeating every field."""
    return make_retrieved_rule


@pytest.fixture(scope="session")
def require_ingested_kb():
    """Skip dependent tests with a clear message if the knowledge base hasn't
    been ingested into ChromaDB yet, instead of letting every test in the
    file fail confusingly."""
    count = retriever._vectorstore._collection.count()
    if count == 0:
        pytest.skip("Knowledge base not ingested — run `python scripts/ingest.py` first.")
    return count
