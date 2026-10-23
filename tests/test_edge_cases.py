"""Additional edge-case and robustness tests."""

import pytest

from safe_json import SafeJSONError, extract, extract_or_raise


def test_unicode():
    assert extract('{"emoji": "🚀", "name": "café"}') == {"emoji": "🚀", "name": "café"}


def test_nested_fences_and_text():
    text = """
Here's the plan:
```json
{
  "steps": ["a", "b"],
  "count": 2
}
```
Then do this.
"""
    result = extract(text)
    assert result["count"] == 2
    assert result["steps"] == ["a", "b"]


def test_json_with_newlines_and_indent():
    text = """
```json
{
  "user": {
    "id": 42,
    "active": true
  }
}
```
"""
    result = extract(text)
    assert result["user"]["id"] == 42


def test_only_array_in_fence():
    assert extract("```json\n[null, false, \"ok\"]\n```") == [None, False, "ok"]


def test_repair_multiple_trailing_commas():
    assert extract('{"a": 1, "b": [1, 2,], "c": 3,}') == {"a": 1, "b": [1, 2], "c": 3}


def test_numbers_and_bools():
    assert extract('{"n": 1.5, "neg": -3, "b": false}') == {"n": 1.5, "neg": -3, "b": False}


def test_empty_object_and_array():
    assert extract("{}") == {}
    assert extract("[]") == []


def test_extract_or_raise_preserves_original():
    original = "not json at all"
    with pytest.raises(SafeJSONError) as exc:
        extract_or_raise(original)
    assert exc.value.original == original
    assert "not json" in str(exc.value)


def test_long_trailing_text():
    text = '{"ok": true}' + " " * 1000 + "end"
    assert extract(text) == {"ok": True}


def test_fence_with_extra_whitespace():
    text = "```json\n\n  {\"x\": 1}  \n\n```"
    assert extract(text) == {"x": 1}


def test_no_repair_still_handles_fences():
    text = "```json\n{\"a\": 1}\n```"
    assert extract(text, repair=False) == {"a": 1}


def test_invalid_after_repair():
    # Something that can't be repaired into valid JSON
    assert extract("{invalid: syntax") is None
