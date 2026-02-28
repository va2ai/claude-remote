"""Phase 3: Senior Partner Synthesis — unified research memo from specialist memos."""

import json
from anthropic import AsyncAnthropic
from config import SYNTHESIS_MODEL, SYNTHESIS_MAX_TOKENS, SPECIALIST_THINKING
from prompts.senior_partner import SYSTEM_PROMPT


async def synthesize(
    client: AsyncAnthropic, facts: dict, memos: list[dict]
) -> str:
    """Synthesize five specialist memos into a unified legal research memo.

    The senior partner receives all specialist memos and produces a single
    comprehensive document. No tools — pure synthesis and legal reasoning.
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
    )

    response = await client.messages.create(
        model=SYNTHESIS_MODEL,
        max_tokens=SYNTHESIS_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        thinking=SPECIALIST_THINKING,
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "text":
            return block.text

    return "[Synthesis produced no text output]"
