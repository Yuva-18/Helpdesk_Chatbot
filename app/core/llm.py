"""Calls the local llama-server /completion endpoint with a raw prompt string."""

import requests

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_N_PREDICT = 512
DEFAULT_TEMPERATURE = 0.2


class LLMError(RuntimeError):
    """Raised when the local llama-server request fails or returns an unusable response."""


def generate_completion(
    prompt: str,
    *,
    n_predict: int = DEFAULT_N_PREDICT,
    temperature: float = DEFAULT_TEMPERATURE,
    stop: list[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Sends a raw prompt string to the local llama-server /completion endpoint
    and returns the generated text."""
    payload = {
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": temperature,
    }
    if stop:
        payload["stop"] = stop

    logger.info("Calling llama-server (%d char prompt, n_predict=%d)", len(prompt), n_predict)
    try:
        response = requests.post(settings.llama_server_url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("llama-server request failed: %s", exc)
        raise LLMError(f"Failed to reach llama-server at {settings.llama_server_url}: {exc}") from exc

    data = response.json()
    content = data.get("content")
    if content is None:
        logger.error("llama-server response missing 'content' field: %s", data)
        raise LLMError("llama-server response did not include generated content")

    logger.info(
        "llama-server responded (%d tokens predicted, stop=%s)",
        data.get("tokens_predicted", -1),
        data.get("stop"),
    )
    return content.strip()
