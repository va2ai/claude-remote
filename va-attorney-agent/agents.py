"""Phase 2: Specialist Agents — parallel fan-out with agentic tool-use loops."""

import asyncio
import json
import sys
import httpx
from anthropic import AsyncAnthropic

from config import SPECIALIST_MODEL, SPECIALIST_MAX_TOKENS, SPECIALIST_THINKING, MAX_TOOL_ITERATIONS
from tools.definitions import AGENT_TOOLS
from tools.handlers import dispatch_tool
from prompts.regulatory_analyst import SYSTEM_PROMPT as REGULATORY_PROMPT
from prompts.case_law_researcher import SYSTEM_PROMPT as CASE_LAW_PROMPT
from prompts.cp_exam_critic import SYSTEM_PROMPT as CP_EXAM_PROMPT
from prompts.evidence_strategist import SYSTEM_PROMPT as EVIDENCE_PROMPT
from prompts.procedural_tactician import SYSTEM_PROMPT as PROCEDURAL_PROMPT


# ── Agent Definitions ─────────────────────────────────────────────

SPECIALISTS = [
    {
        "name": "regulatory_analyst",
        "display_name": "Regulatory Analyst",
        "system_prompt": REGULATORY_PROMPT,
    },
    {
        "name": "case_law_researcher",
        "display_name": "Case Law Researcher",
        "system_prompt": CASE_LAW_PROMPT,
    },
    {
        "name": "cp_exam_critic",
        "display_name": "C&P Exam Critic",
        "system_prompt": CP_EXAM_PROMPT,
    },
    {
        "name": "evidence_strategist",
        "display_name": "Evidence Strategist",
        "system_prompt": EVIDENCE_PROMPT,
    },
    {
        "name": "procedural_tactician",
        "display_name": "Procedural Tactician",
        "system_prompt": PROCEDURAL_PROMPT,
    },
]


# ── Agentic Loop ──────────────────────────────────────────────────


async def run_specialist(
    client: AsyncAnthropic,
    http_client: httpx.AsyncClient,
    name: str,
    display_name: str,
    system_prompt: str,
    tools: list[dict],
    facts: dict,
) -> dict:
    """Run a single specialist agent with adaptive thinking and tool use.

    Loops until the model stops calling tools (end_turn), up to
    MAX_TOOL_ITERATIONS iterations. Returns {"name": ..., "memo": ...}.
    """
    user_message = (
        f"CASE FACTS:\n{json.dumps(facts, indent=2)}\n\n"
        "Complete your assigned research task. Use your tools to look up "
        "actual regulations, cases, and guidance — do not rely on memory "
        "alone. Return a structured memo in the format specified in your "
        "system prompt."
    )

    messages = [{"role": "user", "content": user_message}]
    iteration = 0

    print(f"  [{display_name}] Starting research...", file=sys.stderr)

    while iteration < MAX_TOOL_ITERATIONS:
        iteration += 1

        response = await client.messages.create(
            model=SPECIALIST_MODEL,
            max_tokens=SPECIALIST_MAX_TOKENS,
            system=system_prompt,
            thinking=SPECIALIST_THINKING,
            tools=tools,
            messages=messages,
        )

        # Log every response: iteration, stop_reason, block types, token usage
        block_summary = ", ".join(b.type for b in response.content)
        print(
            f"  [{display_name}] iter={iteration}/{MAX_TOOL_ITERATIONS} "
            f"stop={response.stop_reason} "
            f"in={response.usage.input_tokens} out={response.usage.output_tokens} "
            f"blocks=[{block_summary}]",
            file=sys.stderr,
        )

        # Check if the agent is done
        if response.stop_reason == "end_turn":
            text_parts = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
            memo = "\n".join(text_parts)
            print(
                f"  [{display_name}] Complete ({iteration} iteration(s), "
                f"{len(memo)} chars)",
                file=sys.stderr,
            )
            return {"name": display_name, "memo": memo}

        # Tool use — execute all tool calls and loop back
        # CRITICAL: Preserve full response.content (including thinking blocks)
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(
                    f"  [{display_name}]   -> tool: {block.name} input={json.dumps(block.input)[:120]}",
                    file=sys.stderr,
                )
                result = await dispatch_tool(block.name, block.input, http_client)
                result_preview = result[:120].replace("\n", " ")
                print(
                    f"  [{display_name}]   <- result: {result_preview}",
                    file=sys.stderr,
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            print(
                f"  [{display_name}] WARNING: stop_reason={response.stop_reason} "
                f"but no tool_use blocks found — breaking loop",
                file=sys.stderr,
            )
            break

    # Safety valve
    print(
        f"  [{display_name}] WARNING: Hit max iterations ({MAX_TOOL_ITERATIONS})",
        file=sys.stderr,
    )
    return {
        "name": display_name,
        "memo": "[Agent reached maximum tool iterations without completing]",
    }


# ── Parallel Fan-Out ──────────────────────────────────────────────


async def run_all_specialists(
    client: AsyncAnthropic, facts: dict
) -> list[dict]:
    """Fire all five specialist agents simultaneously via asyncio.gather().

    Total time = time of the slowest agent, not the sum of all five.
    """
    async with httpx.AsyncClient() as http_client:
        tasks = [
            run_specialist(
                client=client,
                http_client=http_client,
                name=spec["name"],
                display_name=spec["display_name"],
                system_prompt=spec["system_prompt"],
                tools=AGENT_TOOLS[spec["name"]],
                facts=facts,
            )
            for spec in SPECIALISTS
        ]

        results = await asyncio.gather(*tasks)
        return list(results)
