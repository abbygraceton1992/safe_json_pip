"""safe-json: Robustly extract and lightly repair JSON from messy LLM responses."""

from safe_json.extractor import SafeJSONError, extract, extract_or_raise

__all__ = ["extract", "extract_or_raise", "SafeJSONError"]
__version__ = "1.0.0"
