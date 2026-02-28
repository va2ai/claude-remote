#!/usr/bin/env python3
"""VA Attorney Research Agent — Multi-agent legal research system.

Architecture:
  Phase 1: Intake Parser (Haiku) — extracts structured facts
  Phase 2: 5 Specialist Agents (Opus) — parallel research with real tools
  Phase 3: Senior Partner (Opus) — synthesizes unified legal research memo

Usage:
  python main.py                          # uses example_input.txt
  python main.py claim.txt                # reads from file
  echo "My PTSD claim..." | python main.py  # reads from stdin
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from anthropic import AsyncAnthropic

from intake import parse_intake
from agents import run_all_specialists
from synthesis import synthesize

load_dotenv()


def read_input() -> str:
    """Read veteran's claim text from file arg, stdin, or example file."""
    # File argument
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)
        return path.read_text().strip()

    # Stdin (if piped)
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    # Default to example
    example = Path(__file__).parent / "example_input.txt"
    if example.exists():
        print(
            "No input provided. Using example_input.txt\n",
            file=sys.stderr,
        )
        return example.read_text().strip()

    print(
        "Usage: python main.py [input_file]\n"
        "       echo 'claim text' | python main.py",
        file=sys.stderr,
    )
    sys.exit(1)


async def main():
    raw_input = read_input()
    client = AsyncAnthropic()

    # ── Phase 1: Intake Parsing ───────────────────────────────────
    print("=" * 60, file=sys.stderr)
    print("PHASE 1: Parsing veteran's narrative...", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    t0 = time.time()
    facts = await parse_intake(client, raw_input)
    t1 = time.time()

    print(
        f"  Intake complete in {t1 - t0:.1f}s",
        file=sys.stderr,
    )
    print(
        f"  Condition: {facts.get('claimed_condition', 'unknown')}",
        file=sys.stderr,
    )
    print(
        f"  Current rating: {facts.get('current_rating', '?')}%",
        file=sys.stderr,
    )
    print(
        f"  Target rating: {facts.get('target_rating', '?')}%",
        file=sys.stderr,
    )
    print(
        f"  Symptoms: {len(facts.get('symptoms', []))} identified",
        file=sys.stderr,
    )
    print(
        f"  Missing facts: {len(facts.get('missing_facts', []))} flagged",
        file=sys.stderr,
    )

    # ── Phase 2: Parallel Specialist Research ─────────────────────
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(
        "PHASE 2: Running 5 specialist agents in parallel...",
        file=sys.stderr,
    )
    print("=" * 60, file=sys.stderr)

    t2 = time.time()
    memos = await run_all_specialists(client, facts)
    t3 = time.time()

    print(f"\n  All specialists complete in {t3 - t2:.1f}s", file=sys.stderr)
    for m in memos:
        print(f"    {m['name']}: {len(m['memo'])} chars", file=sys.stderr)

    # ── Phase 3: Senior Partner Synthesis ─────────────────────────
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(
        "PHASE 3: Senior Partner synthesizing final memo...",
        file=sys.stderr,
    )
    print("=" * 60, file=sys.stderr)

    t4 = time.time()
    final_memo = await synthesize(client, facts, memos)
    t5 = time.time()

    print(f"  Synthesis complete in {t5 - t4:.1f}s", file=sys.stderr)

    # ── Output ────────────────────────────────────────────────────
    total = t5 - t0
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"TOTAL TIME: {total:.1f}s", file=sys.stderr)
    print(
        f"  Phase 1 (Intake):     {t1 - t0:.1f}s",
        file=sys.stderr,
    )
    print(
        f"  Phase 2 (Research):   {t3 - t2:.1f}s",
        file=sys.stderr,
    )
    print(
        f"  Phase 3 (Synthesis):  {t5 - t4:.1f}s",
        file=sys.stderr,
    )
    print("=" * 60, file=sys.stderr)

    # Final memo goes to stdout (can be piped/redirected)
    print(final_memo)


if __name__ == "__main__":
    asyncio.run(main())
