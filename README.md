# safe-json

[![PyPI version](https://shields.io)](https://pypi.org)
[![License: MIT](https://shields.io)](https://opensource.org)
[![Python Support](https://shields.io)](https://pypi.org)

**Extract and safely repair JSON payloads from messy, conversational Large Language Model (LLM) responses.**

LLMs are notoriously bad at outputting *strictly raw* JSON. Even when instructed otherwise, they often bury payloads inside markdown code fences, inject conversational preambles/postambles, mix up single and double quotes, or append invalid trailing commas. 

`safe-json` provides a fast, lightweight, and **zero-dependency** toolkit to gracefully locate, conservatively repair, and safely parse these structures back into standard Python objects.

---

## Key Features

*   **Smart Extraction** — Prefers explicit markdown code blocks, but falls back to finding the outermost balanced structural bounds (`{...}` or `[...]`) if the model didn't format it cleanly.
*   **Conservative Multi-pass Repairs** — Safely repairs systemic structural errors (like JavaScript/Python style trailing commas or unescaped single quotes) only if initial strict JSON validation fails.
*   **Zero Dependencies** — Built completely around the native standard library (`json` and `re`), adding negligible runtime footprint to web apps or edge servers.
*   **Production Resilient** — Includes a `None`-safe fallback engine as well as deterministic error tracking featuring full raw string payload context capture.

---

## Installation

Install using `pip` from PyPI:

```bash
pip install safe-json
```

---

## Quick Start

```python
from safe_json import extract, extract_or_raise, SafeJSONError

# 1. Non-raising extraction (returns None on absolute failure)
data = extract("Some chatbot text... ```json\n{'id': 1,}\n```")
# -> {'id': 1}

# 2. Strict raising extraction (with context payload protection)
try:
    data = extract_or_raise("Sorry, I cannot process your request.")
except SafeJSONError as e:
    print(f"Extraction failed! Raw output was: {e.original}")
```

---

## Practical Usage Examples

### 1. Stripping Markdown & Conversational Text
LLMs frequently sandwich JSON payloads between conversational text and markdown formatting code blocks. `safe-json` extracts the underlying collection reliably.

```python
from safe_json import extract

llm_output = """
Certainly! Here is the metadata blueprint you requested for your system:

```json
{
  "project_name": "Phoenix Alpha",
  "tags": ["cloud", "serverless"]
}
```
Please let me know if you need changes to this setup!
"""

blueprint = extract(llm_output)
print(blueprint["project_name"])  # Output: Phoenix Alpha
```

### 2. Auto-Repairing Common Syntax Hallucinations
When generative token limits are hit or models act lazily, they routinely break compliance rules by leaving Python dict trailing commas or applying weak single quotes.

```python
from safe_json import extract

# Example A: Messy trailing commas inside arrays and objects
bad_commas = '{"items": [10, 20, 30,], "status": "active",}'
print(extract(bad_commas))  
# Output: {'items': [10, 20, 30], 'status': 'active'}

# Example B: Out-of-spec single quote string literals
bad_quotes = "{'error_code': 'UNAUTHORIZED', 'retry': true}"
print(extract(bad_quotes))  
# Output: {'error_code': 'UNAUTHORIZED', 'retry': True}
```

### 3. Real-World Integration (e.g., OpenAI Chat Completion)
Easily plug `safe-json` into your standard agent loops or LLM extraction flows to act as your sanitisation layer.

```python
import os
from openai import OpenAI
from safe_json import extract_or_raise

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Output user schema metrics in JSON."}]
)

raw_content = response.choices.message.content

# Guard the application logic with robust parsing
try:
    metrics = extract_or_raise(raw_content)
    print(f"Active Users: {metrics['active_users']}")
except Exception as err:
    print(f"Failed to safely structuralise agent response: {err}")
```

### 4. Running in Strict Mode (Disabling Repairs)
If you are leveraging strict model structured outputs (e.g., JSON Mode) and want to intentionally fail if the string deviates from JSON standards, you can disable the correction heuristics.

```python
from safe_json import extract

text_with_syntax_errors = "```json\n{'id': 101,}\n```"

# Passing repair=False forces regular strict standard parsing constraints
strict_data = extract(text_with_syntax_errors, repair=False)

print(strict_data)  # Output: None
```

---

## API Architecture Reference

### `extract(text: str, repair: bool = True) -> Any | None`
Attempts to match structural boundaries and convert content into native collection formats. 
*   **`text`**: The raw string target input to search across.
*   **`repair`**: If `True`, runs deep string cleanup iterations (trailing commas, single quote modifications) on validation failures.
*   **Returns**: Parsed Python `dict`, `list`, or primitive scalars if valid; otherwise returns `None`.

### `extract_or_raise(text: str, repair: bool = True) -> Any`
Works identically to `extract`, but instead of yielding `None` on unresolvable payloads, throws a traceable `SafeJSONError`.

### `SafeJSONError`
Custom wrapper exception raised by failures.
*   **`.original`**: A property attribute exposing the *exact, complete input string* passed into the function, enabling system fallback logs to save the unparsed data for debugging or telemetry.

---

## Performance & Extraction Design Matrix

The extraction parsing pipeline operates via structural multi-pass analysis:

