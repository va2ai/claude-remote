#!/usr/bin/env python3
"""VA Attorney Research Agent — Multi-agent legal research system.

Architecture:
  Classifier (Haiku) — routes query to appropriate pipeline
  Quick path — single Haiku call for simple Q&A and overviews
  Full pipeline:
    Phase 1: Intake Parser (Haiku) — extracts structured facts
    Phase 2: Specialist Agents (Sonnet, parallel) — research with real tools
    Phase 3: Senior Partner (Opus) — synthesizes unified legal research memo

Usage:
  python main.py                          # uses example_input.txt
  python main.py claim.txt                # reads from file
  echo "My PTSD claim..." | python main.py  # reads from stdin
  echo "What is SMC?" | python main.py    # quick answer path
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from anthropic import AsyncAnthropic

from orchestrator import run

load_dotenv()


def read_input() -> str:
    """Read veteran's claim text from file arg, stdin, or example file."""
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)
        return path.read_text().strip()

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    example = Path(__file__).parent / "example_input.txt"
    if example.exists():
        print("No input provided. Using example_input.txt\n", file=sys.stderr)
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
    result = await run(client, raw_input)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
