"""Input normalization — detects format and cleans veteran input."""


def normalize_input(raw_text: str) -> tuple[str, str]:
    """Normalize raw input text. Returns (normalized_text, input_format)."""
    text = raw_text.strip()
    input_format = "plain_text"
    return text, input_format
