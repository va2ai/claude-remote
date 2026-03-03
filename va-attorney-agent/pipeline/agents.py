"""Phase 2: Specialist Agents — parallel fan-out with agentic tool-use loops."""

import asyncio
import json
import sys
import httpx
from anthropic import AsyncAnthropic
from langfuse import observe, get_client as get_langfuse

from config import SPECIALIST_MODEL, SPECIALIST_MAX_TOKENS, SPECIALIST_THINKING, MAX_TOOL_ITERATIONS, ROUTING_PROFILES
from tools.definitions import AGENT_TOOLS
from tools.handlers import dispatch_tool
from prompts.regulatory_analyst import SYSTEM_PROMPT as REGULATORY_PROMPT
from prompts.case_law_researcher import SYSTEM_PROMPT as CASE_LAW_PROMPT
from prompts.cp_exam_critic import SYSTEM_PROMPT as CP_EXAM_PROMPT
from prompts.evidence_strategist import SYSTEM_PROMPT as EVIDENCE_PROMPT
from prompts.procedural_tactician import SYSTEM_PROMPT as PROCEDURAL_PROMPT
from prompts.cue_claim import REGULATORY_PROMPT as CUE_REGULATORY_PROMPT, CASE_LAW_PROMPT as CUE_CASE_LAW_PROMPT
from prompts.eligibility_check import REGULATORY_PROMPT as ELIGIBILITY_REGULATORY_PROMPT, PROCEDURAL_PROMPT as ELIGIBILITY_PROCEDURAL_PROMPT
from prompts.appeal_strategy import CASE_LAW_PROMPT as APPEAL_CASE_LAW_PROMPT, PROCEDURAL_PROMPT as APPEAL_PROCEDURAL_PROMPT


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


# ── Per-Query-Type Prompt Overrides ───────────────────────────────
# Maps query_type -> {agent_name -> system_prompt}.
# When run_selected_specialists() is called with a query_type that has
# an entry here, each named specialist uses the override prompt instead
# of its default SPECIALISTS entry prompt.

SPECIALIST_PROMPT_OVERRIDES = {
    "cue_claim": {
        "regulatory_analyst": CUE_REGULATORY_PROMPT,
        "case_law_researcher": CUE_CASE_LAW_PROMPT,
    },
    "eligibility_check": {
        "regulatory_analyst": ELIGIBILITY_REGULATORY_PROMPT,
        "procedural_tactician": ELIGIBILITY_PROCEDURAL_PROMPT,
    },
    "appeal_strategy": {
        "case_law_researcher": APPEAL_CASE_LAW_PROMPT,
        "procedural_tactician": APPEAL_PROCEDURAL_PROMPT,
    },
}


# ── Agentic Loop ──────────────────────────────────────────────────


@observe()
async def run_specialist(
    client: AsyncAnthropic,
    http_client: httpx.AsyncClient,
    name: str,
    display_name: str,
    system_prompt: str,
    tools: list[dict],
    facts: dict,
    max_iterations: int = MAX_TOOL_ITERATIONS,
    model: str = SPECIALIST_MODEL,
    response_depth: str = "standard",
) -> dict:
    """Run a single specialist agent with adaptive thinking and tool use.

    Loops until the model stops calling tools (end_turn), up to
    max_iterations iterations. Returns {"name": ..., "memo": ...}.
    """
    get_langfuse().update_current_span(name=f"specialist:{name}")
    user_message = (
        f"CASE FACTS:\n{json.dumps(facts, indent=2)}\n\n"
        "Complete your assigned research task. Use your tools to look up "
        "actual regulations, cases, and guidance — do not rely on memory "
        "alone. Return a structured memo in the format specified in your "
        "system prompt."
        f"\n\nRESPONSE DEPTH: {response_depth.upper()}\n"
        "brief = 2-4 paragraph memo with key facts only\n"
        "standard = structured memo with labeled sections\n"
        "comprehensive = full legal memo with all citations, tables, and edge cases"
    )

    messages = [{"role": "user", "content": user_message}]
    iteration = 0

    print(f"  [{display_name}] Starting research...", file=sys.stderr)

    while iteration < max_iterations:
        iteration += 1

        response = await client.messages.create(
            model=model,
            max_tokens=SPECIALIST_MAX_TOKENS,
            system=system_prompt,
            thinking=SPECIALIST_THINKING,
            tools=tools,
            messages=messages,
        )

        # Log every response: iteration, stop_reason, block types, token usage
        block_summary = ", ".join(b.type for b in response.content)
        print(
            f"  [{display_name}] iter={iteration}/{max_iterations} "
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
        f"  [{display_name}] WARNING: Hit max iterations ({max_iterations})",
        file=sys.stderr,
    )
    return {
        "name": display_name,
        "memo": "[Agent reached maximum tool iterations without completing]",
    }


# ── Parallel Fan-Out ──────────────────────────────────────────────


async def run_selected_specialists(
    client: AsyncAnthropic,
    facts: dict,
    specialist_names: list[str],
    max_tool_iterations: int = MAX_TOOL_ITERATIONS,
    model: str = SPECIALIST_MODEL,
    query_type: str = None,
    response_depth: str = "standard",
) -> list[dict]:
    """Run a subset of specialist agents in parallel.

    specialist_names: list of agent name keys (e.g. ["regulatory_analyst", "procedural_tactician"])
    max_tool_iterations: per-type iteration cap from routing profile
    model: model override for this run
    query_type: when provided, looks up SPECIALIST_PROMPT_OVERRIDES to swap in
                type-specific prompts for any matching specialists

    Total time = slowest selected agent (asyncio.gather).
    """
    selected = [s for s in SPECIALISTS if s["name"] in specialist_names]
    overrides = SPECIALIST_PROMPT_OVERRIDES.get(query_type, {}) if query_type else {}

    async with httpx.AsyncClient() as http_client:
        tasks = [
            run_specialist(
                client=client,
                http_client=http_client,
                name=spec["name"],
                display_name=spec["display_name"],
                system_prompt=overrides.get(spec["name"], spec["system_prompt"]),
                tools=AGENT_TOOLS[spec["name"]],
                facts=facts,
                max_iterations=max_tool_iterations,
                model=model,
                response_depth=response_depth,
            )
            for spec in selected
        ]
        return list(await asyncio.gather(*tasks))


async def run_all_specialists(
    client: AsyncAnthropic, facts: dict, response_depth: str = "standard"
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
                response_depth=response_depth,
            )
            for spec in SPECIALISTS
        ]

        results = await asyncio.gather(*tasks)
        return list(results)
