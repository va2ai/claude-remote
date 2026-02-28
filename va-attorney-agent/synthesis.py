"""Phase 3: Senior Partner Synthesis — unified research memo from specialist memos."""

import json
from anthropic import AsyncAnthropic
from langfuse import observe
from config import SYNTHESIS_MODEL, SYNTHESIS_MAX_TOKENS, SPECIALIST_THINKING
from prompts.senior_partner import SYSTEM_PROMPT


@observe(name="synthesis")
async def synthesize(
    client: AsyncAnthropic,
    facts: dict,
    memos: list[dict],
    model: str = SYNTHESIS_MODEL,
    response_depth: str = "standard",
) -> str:
    """Synthesize specialist memos into a unified legal research memo.

    The senior partner receives all specialist memos and produces a single
    comprehensive document. No tools — pure synthesis and legal reasoning.

    model: override the synthesis model (e.g. use a lighter model for certain
           query types where full opus-level synthesis is unnecessary).
    response_depth: calibrates output length and detail level.
    """
    memo_block = "\n\n" + "=" * 60 + "\n\n"
    memo_block = memo_block.join(
        f"MEMO FROM: {m['name'].upper()}\n\n{m['memo']}" for m in memos
    )

    user_message = (
        f"CASE FACTS:\n{json.dumps(facts, indent=2)}\n\n"
        f"SPECIALIST MEMOS FROM YOUR RESEARCH TEAM:\n\n{memo_block}\n\n"
        "Write the final unified research memo for this veteran's claim. "
        "This is the document that goes to the client and guides the "
        "entire appeal strategy."
        f"\n\nRESPONSE DEPTH REQUIRED: {response_depth.upper()}\n"
        "brief = 2-4 cohesive paragraphs; direct answer; no tables or citation lists\n"
        "standard = structured sections with headers; moderate detail; key citations only\n"
        "comprehensive = full legal memo with all regulatory text, tables, BVA cases, and edge cases"
    )

    response = await client.messages.create(
        model=model,
        max_tokens=SYNTHESIS_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        thinking=SPECIALIST_THINKING,
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "text":
            return block.text

    return "[Synthesis produced no text output]"
