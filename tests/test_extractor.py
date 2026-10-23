"""Tests for safe-json."""

import pytest

from safe_json import SafeJSONError, extract, extract_or_raise


def test_clean_json():
    assert extract('{"a": 1, "b": [true, null]}') == {"a": 1, "b": [True, None]}


def test_markdown_fence():
    text = """
Some explanation.
```json
{"name": "Alice", "age": 30}
```
Done.
"""
    assert extract(text) == {"name": "Alice", "age": 30}


def test_markdown_fence_no_language():
    text = "```\n[1, 2, 3]\n```"
    assert extract(text) == [1, 2, 3]


def test_trailing_text():
    assert extract('{"ok": true} here is more text') == {"ok": True}


def test_leading_text():
    assert extract('Result: {"ok": true}') == {"ok": True}


def test_trailing_comma():
    assert extract('{"a": 1, "b": 2,}') == {"a": 1, "b": 2}
    assert extract('{"items": [1, 2, 3,]}') == {"items": [1, 2, 3]}


def test_single_quotes():
    assert extract("{'status': 'ok', 'count': 5}") == {"status": "ok", "count": 5}


def test_array():
    assert extract("[1, 2, 3]") == [1, 2, 3]


def test_nested():
    text = '{"user": {"id": 1, "tags": ["a", "b"]}, "active": true}'
    result = extract(text)
    assert result["user"]["id"] == 1
    assert result["active"] is True


def test_no_json():
    assert extract("just some plain text") is None


def test_extract_or_raise_success():
    assert extract_or_raise('{"x": 1}') == {"x": 1}


def test_extract_or_raise_failure():
    with pytest.raises(SafeJSONError) as exc:
        extract_or_raise("no json here")
    assert exc.value.original == "no json here"


def test_repair_disabled():
    # Trailing comma should fail when repair is off
    assert extract('{"a": 1,}', repair=False) is None
    # But succeed when on
    assert extract('{"a": 1,}', repair=True) == {"a": 1}


def test_empty_and_whitespace():
    assert extract("") is None
    assert extract("   \n  ") is None


def test_multiple_fences_takes_first():
    text = """
```json
{"first": true}
```
```json
{"second": true}
```
"""
    assert extract(text) == {"first": True}


def test_type_error():
    with pytest.raises(TypeError):
        extract(123)  # type: ignore
