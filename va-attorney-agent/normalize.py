"""Input normalization — detect format and clean up raw text."""

import re


def normalize_input(raw_text: str) -> tuple[str, str]:
    """Normalize raw input text and detect its format.

    Returns (normalized_text, input_format) where input_format is one of:
    - "structured" — input contains clear section headers or form fields
    - "plain_text" — freeform narrative
    """
    text = raw_text.strip()

    # Collapse excessive whitespace / blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    # Detect structured input (has form-like headers or key: value lines)
    structured_signals = [
        r"^(?:condition|rating|symptoms|denial)\s*:",
        r"^(?:current rating|target rating|claimed condition)\s*:",
        r"^\d+\.\s+\w+",  # numbered list
    ]
    is_structured = any(
        re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        for pattern in structured_signals
    )

    input_format = "structured" if is_structured else "plain_text"
    return text, input_format
