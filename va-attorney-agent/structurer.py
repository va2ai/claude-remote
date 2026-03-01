"""Structurer — converts a plain-text research memo into the structured JSON
format expected by the frontend."""

import json
from anthropic import AsyncAnthropic
from langfuse import observe

STRUCTURER_MODEL = "claude-haiku-4-5-20251001"
STRUCTURER_MAX_TOKENS = 4096

STRUCTURER_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "structured_research",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "headline": {
                    "type": "string",
                    "description": "One-line summary of the key finding or recommendation (50-100 chars)",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Overall confidence in the analysis",
                },
                "win_probability": {
                    "type": ["integer", "null"],
                    "description": "Estimated probability of success (0-100), or null if not applicable",
                },
                "cfr_sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section": {"type": "string", "description": "CFR reference, e.g. '38 CFR § 4.130'"},
                            "title": {"type": "string", "description": "Short title of the section"},
                            "text": {"type": "string", "description": "Brief summary of relevance (1-2 sentences)"},
                        },
                        "required": ["section", "title", "text"],
                        "additionalProperties": False,
                    },
                    "description": "Key CFR sections referenced in the memo",
                },
                "bva_cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "citation": {"type": "string", "description": "Case citation"},
                            "summary": {"type": "string", "description": "One-line summary of relevance"},
                            "outcome": {"type": "string", "enum": ["grant", "deny", "remand"]},
                            "year": {"type": "string", "description": "Year of the decision"},
                        },
                        "required": ["citation", "summary", "outcome", "year"],
                        "additionalProperties": False,
                    },
                    "description": "Key BVA cases or precedent cited",
                },
                "action_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                            "text": {"type": "string", "description": "Specific action the veteran should take"},
                        },
                        "required": ["priority", "text"],
                        "additionalProperties": False,
                    },
                    "description": "Recommended actions in priority order",
                },
                "memo": {
                    "type": "string",
                    "description": "Condensed research summary (3-5 paragraphs, ~500 words). Use **bold** for emphasis.",
                },
                "follow_up_questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "A follow-up question to ask the veteran"},
                        },
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                    "description": "1-3 follow-up questions that would help refine the analysis",
                },
            },
            "required": [
                "headline",
                "confidence",
                "win_probability",
                "cfr_sections",
                "bva_cases",
                "action_items",
                "memo",
                "follow_up_questions",
            ],
            "additionalProperties": False,
        },
    },
}

SYSTEM_PROMPT = """You are a legal document structurer. You receive a detailed VA disability law research memo and extract its key components into a structured JSON format.

RULES:
- Extract ONLY information that is explicitly stated in the memo. Do NOT fabricate citations, case names, or CFR sections.
- For win_probability: estimate based on the memo's overall tone and explicit assessments. Use null if the memo doesn't assess likelihood of success.
- For confidence: "high" if the memo is thorough with strong supporting evidence, "medium" if there are gaps or mixed signals, "low" if the analysis is uncertain.
- For cfr_sections: extract only CFR sections explicitly cited in the memo with their section numbers.
- For bva_cases: extract only cases explicitly cited. Include CAVC and Federal Circuit cases too. Use "grant" for cases favorable to veterans, "deny" for unfavorable, "remand" for remands.
- For action_items: extract specific recommended actions. "critical" = do immediately, "high" = do soon, "medium" = should do, "low" = consider.
- For memo: condense the full research into 3-5 readable paragraphs. Preserve key findings and recommendations.
- For follow_up_questions: generate 1-3 questions that would help refine the analysis based on gaps identified in the memo."""


@observe(name="structure_memo")
async def structure_memo(
    client: AsyncAnthropic,
    memo_text: str,
    query: str,
) -> dict:
    """Parse a plain-text research memo into the structured frontend JSON format."""
    response = await client.messages.create(
        model=STRUCTURER_MODEL,
        max_tokens=STRUCTURER_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"ORIGINAL QUERY:\n{query}\n\n"
                    f"RESEARCH MEMO TO STRUCTURE:\n{memo_text}"
                ),
            }
        ],
        output_config={"format": STRUCTURER_SCHEMA},
    )

    text = response.content[0].text
    return json.loads(text)
