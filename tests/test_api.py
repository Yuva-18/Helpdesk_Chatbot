"""End-to-end tests for the FastAPI routes."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.rag_pipeline import ChatResult

client = TestClient(app)


def _sample_confident_result() -> ChatResult:
    return ChatResult(
        answer="You can submit a batch job using the qsub command.",
        is_confident=True,
        used_llm=True,
        matched_rule_id="rule_16",
        category="Hpce",
        support_email="helpdeskhpce@iitm.ac.in",
        source_url=None,
        reason="Matched 'rule_16' with score 1.000.",
    )


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.api.routes.chat.answer_query")
def test_chat_returns_the_pipeline_result_shape(mock_answer_query):
    mock_answer_query.return_value = _sample_confident_result()

    response = client.post("/chat", json={"question": "How do I submit a batch job?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == _sample_confident_result().answer
    assert body["is_confident"] is True
    assert body["category"] == "Hpce"
    assert body["support_email"] == "helpdeskhpce@iitm.ac.in"
    mock_answer_query.assert_called_once_with("How do I submit a batch job?")


def test_chat_rejects_empty_question():
    response = client.post("/chat", json={"question": ""})

    assert response.status_code == 422


def test_chat_rejects_missing_question():
    response = client.post("/chat", json={})

    assert response.status_code == 422


@patch("app.api.routes.chat.answer_query")
def test_chat_unexpected_exception_returns_generic_500(mock_answer_query):
    mock_answer_query.side_effect = RuntimeError("boom: a secret internal detail")

    response = client.post("/chat", json={"question": "anything"})

    assert response.status_code == 500
    body = response.json()
    assert "boom" not in body["detail"]
    assert "secret" not in body["detail"]
