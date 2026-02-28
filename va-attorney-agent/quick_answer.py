"""Quick answer engine — single-pass response for simple questions and overviews."""

import sys
import json
from anthropic import AsyncAnthropic
from langfuse import observe

from config import QUICK_ANSWER_MODEL, QUICK_ANSWER_MAX_TOKENS, QUICK_ANSWER_MAX_TOOL_ITERATIONS
from tools.definitions import CFR_SEARCH, CFR_SECTION, RAG_SEARCH, KNOWVA_SEARCH
from prompts.quick_answer import QUICK_QUESTION_PROMPT, BENEFITS_OVERVIEW_PROMPT

import httpx
from tools.handlers import dispatch_tool

QUICK_ANSWER_TOOLS = [CFR_SEARCH, CFR_SECTION, RAG_SEARCH, KNOWVA_SEARCH]


@observe(name="quick_answer")
async def answer_quick(
    client: AsyncAnthropic,
    raw_text: str,
    classification: dict,
) -> str:
    """Answer a simple factual question or benefits overview in a single agentic pass.

    Uses Haiku with tools. Loops up to QUICK_ANSWER_MAX_TOOL_ITERATIONS.
    Returns a plain-text answer (not memo format).
    """
    query_type = classification.get("query_type", "quick_question")
    system_prompt = (
        BENEFITS_OVERVIEW_PROMPT
        if query_type == "benefits_overview"
        else QUICK_QUESTION_PROMPT
    )

    messages = [{"role": "user", "content": raw_text}]
    iteration = 0

    async with httpx.AsyncClient() as http_client:
        while iteration < QUICK_ANSWER_MAX_TOOL_ITERATIONS:
            iteration += 1

            response = await client.messages.create(
                model=QUICK_ANSWER_MODEL,
                max_tokens=QUICK_ANSWER_MAX_TOKENS,
                system=system_prompt,
                tools=QUICK_ANSWER_TOOLS,
                messages=messages,
            )

            print(
                f"  [QuickAnswer] iter={iteration} stop={response.stop_reason} "
                f"in={response.usage.input_tokens} out={response.usage.output_tokens}",
                file=sys.stderr,
            )

            if response.stop_reason == "end_turn":
                text_parts = [b.text for b in response.content if b.type == "text"]
                return "\n".join(text_parts)

            # Tool use
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [QuickAnswer]   -> {block.name}", file=sys.stderr)
                    result = await dispatch_tool(block.name, block.input, http_client)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                break

    # Fallback: extract any text from last response
    text_parts = [b.text for b in response.content if b.type == "text"]
    return "\n".join(text_parts) if text_parts else "[No answer generated]"
