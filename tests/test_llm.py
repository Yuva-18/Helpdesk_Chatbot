"""Unit tests for app/core/llm.py."""

from unittest.mock import Mock, patch

import pytest
import requests

from app.core.llm import LLMError, generate_completion


def _mock_response(json_data: dict, http_error: bool = False) -> Mock:
    response = Mock()
    response.json.return_value = json_data
    if http_error:
        response.raise_for_status.side_effect = requests.HTTPError("500 error")
    else:
        response.raise_for_status.return_value = None
    return response


@patch("app.core.llm.requests.post")
def test_generate_completion_returns_stripped_content_on_success(mock_post):
    mock_post.return_value = _mock_response({"content": "  the answer  ", "tokens_predicted": 5, "stop": True})

    result = generate_completion("some prompt")

    assert result == "the answer"


@patch("app.core.llm.requests.post")
def test_generate_completion_includes_stop_sequences_when_given(mock_post):
    mock_post.return_value = _mock_response({"content": "answer"})

    generate_completion("prompt", stop=["<|eot_id|>"])

    _, kwargs = mock_post.call_args
    assert kwargs["json"]["stop"] == ["<|eot_id|>"]


@patch("app.core.llm.requests.post")
def test_generate_completion_omits_stop_key_when_not_given(mock_post):
    mock_post.return_value = _mock_response({"content": "answer"})

    generate_completion("prompt")

    _, kwargs = mock_post.call_args
    assert "stop" not in kwargs["json"]


@patch("app.core.llm.requests.post")
def test_generate_completion_raises_llm_error_on_connection_failure(mock_post):
    mock_post.side_effect = requests.ConnectionError("connection refused")

    with pytest.raises(LLMError):
        generate_completion("prompt")


@patch("app.core.llm.requests.post")
def test_generate_completion_raises_llm_error_on_http_error(mock_post):
    mock_post.return_value = _mock_response({}, http_error=True)

    with pytest.raises(LLMError):
        generate_completion("prompt")


@patch("app.core.llm.requests.post")
def test_generate_completion_raises_llm_error_when_content_missing(mock_post):
    mock_post.return_value = _mock_response({"tokens_predicted": 0})

    with pytest.raises(LLMError):
        generate_completion("prompt")
