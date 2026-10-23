"""Core extraction and light repair logic."""

from __future__ import annotations

import json
import re
from typing import Any


class SafeJSONError(Exception):
    """Raised when no valid JSON can be extracted."""

    def __init__(self, message: str, original: str | None = None):
        self.original = original
        super().__init__(message)


_FENCE_RE = re.compile(
    r"```(?:json)?\s*([\s\S]*?)```",
    re.IGNORECASE,
)

# Common LLM artifacts
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
_SINGLE_QUOTE_RE = re.compile(r"(?<!\\)'")


def _try_parse(candidate: str) -> Any | None:
    """Attempt to parse a candidate string as JSON. Returns None on failure."""
    candidate = candidate.strip()
    if not candidate:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _light_repair(text: str) -> str:
    """Apply conservative repairs that are safe for most LLM output."""
    # Remove trailing commas before } or ]
    text = _TRAILING_COMMA_RE.sub(r"\1", text)
    # Replace unescaped single quotes with double quotes (common in some models)
    # Only do this if there are no double quotes already dominating
    if text.count('"') < text.count("'") / 2:
        text = _SINGLE_QUOTE_RE.sub('"', text)
    return text


def _extract_candidates(text: str) -> list[str]:
    """Generate candidate JSON strings from the input, ordered by likelihood."""
    candidates: list[str] = []

    # 1. Markdown fences (highest priority)
    for match in _FENCE_RE.finditer(text):
        candidates.append(match.group(1))

    # 2. Entire text
    candidates.append(text)

    # 3. First {...} or [...] block (greedy-ish by finding balanced regions)
    # Simple approach: find first { or [ and try progressively larger slices
    start_chars = ["{", "["]
    for start_char in start_chars:
        idx = text.find(start_char)
        if idx == -1:
            continue
        # Try from the start character to the end, and also to the last matching closer
        closer = "}" if start_char == "{" else "]"
        last_closer = text.rfind(closer)
        if last_closer > idx:
            candidates.append(text[idx : last_closer + 1])
        candidates.append(text[idx:])

    # Deduplicate while preserving order
    seen = set()
    unique: list[str] = []
    for c in candidates:
        key = c.strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def extract(text: str, repair: bool = True) -> Any | None:
    """Extract the first valid JSON value from *text*.

    Returns the parsed Python object (dict, list, str, int, etc.) or None
    if nothing could be parsed.

    Args:
        text: The raw string (typically an LLM response).
        repair: If True, attempt light repairs (trailing commas, simple quote fixes)
                on candidates that fail initial parsing.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    for candidate in _extract_candidates(text):
        result = _try_parse(candidate)
        if result is not None:
            return result

        if repair:
            repaired = _light_repair(candidate)
            result = _try_parse(repaired)
            if result is not None:
                return result

    return None


def extract_or_raise(text: str, repair: bool = True) -> Any:
    """Like :func:`extract`, but raises :class:`SafeJSONError` on failure."""
    result = extract(text, repair=repair)
    if result is None:
        preview = text[:200] + ("..." if len(text) > 200 else "")
        raise SafeJSONError(
            f"Could not extract valid JSON. Preview: {preview!r}",
            original=text,
        )
    return result
