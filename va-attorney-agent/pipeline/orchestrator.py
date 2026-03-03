"""Orchestrator — routes queries to the appropriate pipeline based on classification."""

import json
import sys
import time
from anthropic import AsyncAnthropic
from langfuse import observe, get_client as get_langfuse

from .normalize import normalize_input
from .classifier import classify_query
from .quick_answer import answer_quick
from .intake import parse_intake
from .agents import run_all_specialists, run_selected_specialists
from .synthesis import synthesize
from config import ROUTING_PROFILES


def _format_memos(memos: list[dict], query_type: str) -> str:
    """Format specialist memos without synthesis for lightweight paths."""
    header = {
        "eligibility_check": "# VA ELIGIBILITY ASSESSMENT",
        "appeal_strategy": "# VA APPEAL STRATEGY ANALYSIS",
    }.get(query_type, "# VA RESEARCH SUMMARY")

    sections = []
    for m in memos:
        if m["memo"] and not m["memo"].startswith("[Agent reached"):
            sections.append(f"## {m['name']}\n\n{m['memo']}")

    if not sections:
        return f"{header}\n\n*Specialists were unable to complete research within the iteration limit.*"

    return header + "\n\n---\n\n" + "\n\n---\n\n".join(sections)


@observe(name="va-attorney-agent")
async def run(client: AsyncAnthropic, raw_text: str) -> str:
    """Top-level orchestration entry point. Returns the final output string."""

    # ── Step 0: Normalize ─────────────────────────────────────────
    normalized_text, input_format = normalize_input(raw_text)

    # ── Step 1: Classify ──────────────────────────────────────────
    print("=" * 60, file=sys.stderr)
    print("CLASSIFYING query...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    t_start = time.time()
    classification = await classify_query(client, normalized_text)
    classification["input_format"] = input_format

    query_type = classification["query_type"]
    routing = classification["routing"]
    response_depth = classification.get("response_depth", "standard")

    get_langfuse().update_current_trace(
        tags=[query_type, response_depth],
        metadata={"query_type": query_type, "input_format": input_format},
    )

    print(f"  Query type  : {query_type}", file=sys.stderr)
    print(f"  Confidence  : {classification.get('confidence', 0):.2f}", file=sys.stderr)
    print(f"  Quick path  : {routing['quick_answer']}", file=sys.stderr)
    print(f"  Specialists : {routing['specialists'] or 'none'}", file=sys.stderr)
    print(f"  Keywords    : {', '.join(classification.get('topic_keywords', []))}", file=sys.stderr)
    print(f"  Depth       : {response_depth}", file=sys.stderr)

    # ── Quick path (quick_question / benefits_overview) ───────────
    if routing["quick_answer"]:
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"QUICK ANSWER ({query_type})", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

        t0 = time.time()
        answer = await answer_quick(client, normalized_text, classification)
        print(f"  Done in {time.time() - t0:.1f}s | TOTAL: {time.time() - t_start:.1f}s", file=sys.stderr)
        return answer

    # ── Intake (all non-quick paths) ──────────────────────────────
    print(f"\n{'=' * 60}", file=sys.stderr)
    print("PHASE 1: Parsing veteran's narrative...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    t0 = time.time()
    facts = await parse_intake(client, normalized_text)
    t1 = time.time()

    print(f"  Intake complete in {t1 - t0:.1f}s", file=sys.stderr)
    print(f"  Condition: {facts.get('claimed_condition', 'unknown')}", file=sys.stderr)
    print(f"  Current rating: {facts.get('current_rating', '?')}%", file=sys.stderr)
    print(f"  Target rating: {facts.get('target_rating', '?')}%", file=sys.stderr)
    print(f"  Symptoms: {len(facts.get('symptoms', []))} identified", file=sys.stderr)

    facts["_query_type"] = query_type

    # ── Specialist research ───────────────────────────────────────
    specialist_names = routing["specialists"]
    n = len(specialist_names)
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"PHASE 2: Running {n} specialist agent(s) in parallel...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    t2 = time.time()

    if query_type == "rating_increase":
        memos = await run_all_specialists(client, facts, response_depth=response_depth)
    else:
        memos = await run_selected_specialists(
            client=client,
            facts=facts,
            specialist_names=specialist_names,
            max_tool_iterations=routing["max_tool_iterations"],
            model=routing["specialist_model"],
            query_type=query_type,
            response_depth=response_depth,
        )

    t3 = time.time()
    print(f"\n  Specialists complete in {t3 - t2:.1f}s", file=sys.stderr)
    for m in memos:
        print(f"    {m['name']}: {len(m['memo'])} chars", file=sys.stderr)

    # ── Synthesis (conditional) ───────────────────────────────────
    if routing["run_synthesis"]:
        print(f"\n{'=' * 60}", file=sys.stderr)
        print("PHASE 3: Synthesizing final memo...", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

        t4 = time.time()
        synthesis_model = routing.get("synthesis_model")
        final_memo = await synthesize(
            client,
            facts,
            memos,
            response_depth=response_depth,
            **({"model": synthesis_model} if synthesis_model else {}),
        )
        t5 = time.time()

        print(f"  Synthesis complete in {t5 - t4:.1f}s", file=sys.stderr)
    else:
        # No synthesis — format memos directly
        t4 = t5 = t3
        final_memo = _format_memos(memos, query_type)

    # ── Timing summary ────────────────────────────────────────────
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"TOTAL TIME: {t5 - t_start:.1f}s", file=sys.stderr)
    print(f"  Classification: {t0 - t_start:.1f}s", file=sys.stderr)
    print(f"  Intake:         {t1 - t0:.1f}s", file=sys.stderr)
    print(f"  Research:       {t3 - t2:.1f}s", file=sys.stderr)
    if routing["run_synthesis"]:
        print(f"  Synthesis:      {t5 - t4:.1f}s", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    return final_memo
