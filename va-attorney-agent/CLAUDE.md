# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

VA Attorney Research Agent — a multi-agent legal research system that analyzes veterans' disability claims and produces comprehensive legal research memos. It is a pure Python CLI tool in the `va-attorney-agent/` subdirectory of the `claude-remote` monorepo.

## Setup & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run with example input
python main.py

# Run with a file
python main.py claim.txt

# Run with stdin
echo "My PTSD claim..." | python main.py
```

Progress is printed to stderr; the final memo goes to stdout (can be piped/redirected).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required. Anthropic API key. |
| `BVA_API_BASE_URL` | BVA API base URL. Defaults to `https://bva-api-524576132881.us-central1.run.app` |

## Architecture — Three-Phase Pipeline

### Phase 1: Intake (`pipeline/intake.py`)
- Model: `claude-haiku-4-5` (fast, cheap)
- Parses the veteran's free-text narrative into a strict JSON schema (`INTAKE_SCHEMA` in `config.py`)
- Uses structured output (`output_config.format.json_schema`) — no tools, no reasoning

### Phase 2: Specialist Agents (`pipeline/agents.py`)
- Model: `claude-opus-4-6` with adaptive thinking
- Five agents run **in parallel** via `asyncio.gather()` — total time = slowest agent
- Each agent has a curated subset of BVA API tools (see `tools/definitions.py`)
- Agentic tool-use loop: loops until `stop_reason == "end_turn"` or hits `MAX_TOOL_ITERATIONS` (15)
- **Critical:** Full `response.content` (including thinking blocks) is preserved when appending to messages, not just text

### Phase 3: Synthesis (`pipeline/synthesis.py`)
- Model: `claude-opus-4-6` with adaptive thinking
- Senior Partner receives all five specialist memos and produces one unified legal research memo
- No tools — pure synthesis

## Specialist Agents

| Agent | Tools |
|-------|-------|
| Regulatory Analyst | `cfr_section`, `cfr_search`, `cfr_diagnostic_code`, `federal_register_search`, `rag_search` |
| Case Law Researcher | `bva_search`, `bva_get_case`, `bva_analyze`, `rag_search` |
| C&P Exam Critic | `cfr_section`, `bva_search`, `bva_get_case` |
| Evidence Strategist | `cfr_section`, `cfr_search`, `cfr_diagnostic_code`, `bva_search`, `knowva_search`, `knowva_article` |
| Procedural Tactician | `cfr_section`, `cfr_search`, `bva_search`, `federal_register_search` |

## Key Files

- `config.py` — all model names, token limits, thinking config, `INTAKE_SCHEMA`, and `BVA_API_BASE_URL`
- `pipeline/` — all pipeline stages: `orchestrator.py`, `classifier.py`, `intake.py`, `agents.py`, `synthesis.py`, `quick_answer.py`, `normalize.py`
- `tools/definitions.py` — Anthropic-format tool definitions and per-agent assignments (`AGENT_TOOLS`)
- `tools/handlers.py` — async HTTP handlers for each BVA API endpoint; `dispatch_tool()` routes calls
- `prompts/` — one file per agent with its `SYSTEM_PROMPT`

## BVA API Tools

All tool calls go to the BVA REST API (`BVA_API_BASE_URL`). Tools and their endpoints:

| Tool | Method | Endpoint |
|------|--------|----------|
| `cfr_section` | GET | `/cfr/section?part=&section=` |
| `cfr_search` | GET | `/cfr/search?q=` |
| `cfr_diagnostic_code` | GET | `/cfr/dc/{code}` |
| `bva_search` | POST | `/search` |
| `bva_get_case` | GET | `/case?url=&full_text=true` |
| `bva_analyze` | GET | `/analyze/text?url=` |
| `federal_register_search` | GET | `/federal-register/search?q=` |
| `knowva_search` | GET | `/knowva/search?q=` |
| `knowva_article` | GET | `/knowva/article/{id}` |
| `rag_search` | GET | `/rag/search?q=` |

`bva_get_case` truncates `full_text` at 15,000 chars; `knowva_article` truncates `content` at 10,000 chars to stay within context limits.

## Bugs & Decisions

- Thinking blocks must be included in the assistant message when looping through tool calls — stripping them causes API errors with extended thinking models.
- Intake uses `output_config` structured output (not `tools`) for clean schema enforcement without tool overhead.
