"""Phase 1: Intake Parser — extracts structured facts from veteran's narrative."""

import json
from anthropic import AsyncAnthropic
from config import INTAKE_MODEL, INTAKE_MAX_TOKENS, INTAKE_SCHEMA
from prompts.intake import SYSTEM_PROMPT


async def parse_intake(client: AsyncAnthropic, raw_text: str) -> dict:
    """Parse a veteran's plain-text claim narrative into structured facts.

    Uses Claude Haiku with structured output to produce a validated JSON
    object matching INTAKE_SCHEMA. No tools, no reasoning — pure extraction.
    """
    response = await client.messages.create(
        model=INTAKE_MODEL,
        max_tokens=INTAKE_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": raw_text}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": INTAKE_SCHEMA,
            }
        },
    )
    return json.loads(response.content[0].text)
