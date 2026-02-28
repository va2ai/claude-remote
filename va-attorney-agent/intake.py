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
        tools=[{
            "name": INTAKE_SCHEMA["name"],
            "description": INTAKE_SCHEMA["description"],
            "input_schema": INTAKE_SCHEMA["schema"],
        }],
        tool_choice={"type": "tool", "name": INTAKE_SCHEMA["name"]},
    )
    return response.content[0].input
