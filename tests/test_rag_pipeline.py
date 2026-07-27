"""Integration tests for app/services/rag_pipeline.py.

Exercises the real retriever + confidence gate (against the ingested
knowledge base) but mocks the LLM call, so these tests don't require
llama-server to be running.
"""

from unittest.mock import patch

from app.core.llm import LLMError
from app.services.rag_pipeline import answer_query, logger as rag_pipeline_logger

ESERVICES_LDAP_QUESTION = "My LDAP is not working and I cannot access the internet or WiFi."
OFF_TOPIC_QUESTION = "What's a good recipe for chocolate cake?"


@patch("app.services.rag_pipeline.generate_completion")
def test_confident_query_uses_the_llm_and_returns_its_answer(mock_generate, require_ingested_kb):
    mock_generate.return_value = (
        "Your LDAP account may be expired; email helpdeskeservices@iitm.ac.in to renew it."
    )

    result = answer_query(ESERVICES_LDAP_QUESTION)

    assert result.is_confident is True
    assert result.used_llm is True
    assert result.answer == mock_generate.return_value
    assert result.category == "Eservices"
    assert result.matched_rule_id == "rule_01"
    assert result.support_email == "helpdeskeservices@iitm.ac.in"
    mock_generate.assert_called_once()


@patch("app.services.rag_pipeline.generate_completion")
def test_llm_failure_falls_back_to_the_verified_kb_answer(mock_generate, require_ingested_kb):
    mock_generate.side_effect = LLMError("llama-server unreachable")

    result = answer_query(ESERVICES_LDAP_QUESTION)

    assert result.is_confident is True
    assert result.used_llm is False
    assert "helpdeskeservices@iitm.ac.in" in result.answer  # the verified rule's raw answer


@patch("app.services.rag_pipeline.generate_completion")
def test_low_confidence_query_never_calls_the_llm(mock_generate, require_ingested_kb):
    result = answer_query(OFF_TOPIC_QUESTION)

    assert result.is_confident is False
    assert result.used_llm is False
    mock_generate.assert_not_called()
    assert result.support_email in result.answer


def test_empty_retrieval_returns_a_generic_fallback_message():
    with patch("app.services.rag_pipeline.retriever") as mock_retriever:
        mock_retriever.retrieve.return_value = []
        result = answer_query("anything")

    assert result.is_confident is False
    assert result.category is None
    assert result.support_email is None
    assert "helpdesk" in result.answer.lower()


@patch("app.services.rag_pipeline.generate_completion")
def test_drift_appends_verified_email_when_generated_answer_drops_it(mock_generate, require_ingested_kb, caplog):
    """Regression test for a real failure mode found during evaluation: the
    LLM occasionally drops/alters the verified support email. The pipeline
    self-corrects by appending the verified email rather than only logging."""
    mock_generate.return_value = "Your LDAP account might be expired, please renew it with your ID card."

    rag_pipeline_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level("WARNING"):
            result = answer_query(ESERVICES_LDAP_QUESTION)
    finally:
        rag_pipeline_logger.removeHandler(caplog.handler)

    assert result.answer.startswith(mock_generate.return_value)  # LLM's answer kept intact
    assert "helpdeskeservices@iitm.ac.in" in result.answer  # verified email appended
    assert any("Appending the verified email" in message for message in caplog.messages)
