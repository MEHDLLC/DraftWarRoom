"""
Anthropic (Claude) adapter.

Provides streaming and non-streaming chat interfaces using the official
``anthropic`` Python SDK.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from anthropic import AsyncAnthropic

from ..config import get_settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


def _get_client() -> AsyncAnthropic:
    """Return a configured ``AsyncAnthropic`` client."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set.  Add it to your .env file."
        )
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


# ---------------------------------------------------------------------------
# Streaming chat
# ---------------------------------------------------------------------------

async def chat_stream(
    messages: list[dict],
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    """Async generator that yields text chunks from Claude's streaming response.

    Parameters
    ----------
    messages:
        A list of message dicts, each with ``"role"`` and ``"content"`` keys
        (e.g. ``[{"role": "user", "content": "hello"}]``).
    system_prompt:
        The system-level instruction prepended to the conversation.

    Yields
    ------
    str
        Incremental text chunks as they arrive from the model.

    Raises
    ------
    RuntimeError
        If the API key is missing or the request fails catastrophically.
    """
    client = _get_client()
    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as exc:
        logger.error("Anthropic streaming error: %s", exc)
        yield f"\n[Error communicating with Claude: {exc}]"


# ---------------------------------------------------------------------------
# Non-streaming chat
# ---------------------------------------------------------------------------

async def chat(
    messages: list[dict],
    system_prompt: str,
) -> str:
    """Send a non-streaming chat request and return the full text response.

    Parameters
    ----------
    messages:
        A list of message dicts (same format as :func:`chat_stream`).
    system_prompt:
        The system-level instruction.

    Returns
    -------
    str
        The complete assistant response text.  Returns an error string
        (rather than raising) if the API call fails.
    """
    client = _get_client()
    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        )
        # The response content is a list of content blocks; join all text blocks.
        parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "".join(parts)
    except Exception as exc:
        logger.error("Anthropic chat error: %s", exc)
        return f"[Error communicating with Claude: {exc}]"
