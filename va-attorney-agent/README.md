# VA Attorney Research Agent

A multi-agent AI system for researching veterans' disability claims. Accepts a veteran's plain-text narrative and produces a comprehensive legal research memo covering regulatory analysis, case law, C&P exam critique, evidence strategy, and procedural options.

## How It Works

Three phases run sequentially:

1. **Intake** (`claude-haiku-4-5`) — parses the narrative into structured facts using tool-forced structured output (condition, symptoms, ratings, appeal lanes, TDIU eligibility, etc.)
2. **Research** (`claude-sonnet-4-6`, 5x in parallel) — each specialist agent uses real BVA API tools to look up CFR regulations, BVA case law, KnowVA guidance, and Federal Register documents; capped at 5 tool iterations each
3. **Synthesis** (`claude-opus-4-6`) — Senior Partner consolidates all five memos into a single unified research memo

Total runtime is typically 2-4 minutes depending on API latency.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in ANTHROPIC_API_KEY in .env
```

## Usage

```bash
# Run with the included example (PTSD rating increase)
python main.py

# Run with a claim file
python main.py claim.txt

# Pipe claim text directly
echo "I'm at 50% for PTSD and was denied an increase..." | python main.py

# Save memo to file (progress logs go to stderr, memo to stdout)
python main.py claim.txt > memo.md

# Capture full logs for debugging
python main.py 2>&1 | tee run.log
```

## Output

Progress is printed to stderr (verbose per-iteration) so it does not pollute the memo:

```
============================================================
PHASE 1: Parsing veteran's narrative...
  Intake complete in 2.1s
  Condition: PTSD
  Current rating: 50%
  Target rating: 70%
...
PHASE 2: Running 5 specialist agents in parallel...
  [Regulatory Analyst] Starting research...
  [Regulatory Analyst] iter=1/5 stop=tool_use in=1234 out=456 blocks=[thinking, tool_use]
  [Regulatory Analyst]   -> tool: bva_cfr_section input={"title": "38", "part": "4"}
  [Regulatory Analyst]   <- result: ...
  [Regulatory Analyst] iter=2/5 stop=end_turn in=... out=... blocks=[thinking, text]
  [Regulatory Analyst] Complete (2 iteration(s), 3241 chars)
...
TOTAL TIME: 187.3s
```

The final memo goes to stdout in markdown format.

## Specialist Agents

| Agent | Responsibility |
|-------|---------------|
| Regulatory Analyst | 38 CFR rating criteria, diagnostic codes, Federal Register |
| Case Law Researcher | BVA decisions with similar fact patterns |
| C&P Exam Critic | Adequacy of the exam, grounds to challenge |
| Evidence Strategist | Evidence gaps, nexus letters, buddy statements |
| Procedural Tactician | HLR vs. BVA appeal lane analysis, TDIU, deadlines |

## Model & Token Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Intake model | `claude-haiku-4-5-20251001` | Structured extraction only |
| Specialist model | `claude-sonnet-4-6` | Was opus-4-6; 5x cheaper |
| Synthesis model | `claude-opus-4-6` | Kept for final memo quality |
| Specialist max tokens | 4096 | Was 8192 |
| Synthesis max tokens | 8000 | Was 16000 |
| Max tool iterations | 5 | Was 15; safety valve per specialist |

## Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/test_agents.py -v
```

| Test | What it verifies |
|------|-----------------|
| `test_exits_immediately_on_end_turn` | Returns memo on first `end_turn` with no tool calls |
| `test_tool_call_then_end_turn` | One tool call round-trip; tool_result included in second request |
| `test_no_empty_user_message_when_no_tool_blocks` | No empty user message appended when stop is not `end_turn` but no tool_use blocks exist (prevents 400 error) |
| `test_multiple_tool_calls_in_one_response` | All tool_use blocks in a single response are batched and returned together |
| `test_hits_max_iterations` | Safety valve returns fallback memo after `MAX_TOOL_ITERATIONS` |

## Implementation Notes

- **Intake structured output** — uses `tool_choice: {type: "tool"}` to force the schema tool, ensuring Haiku always returns valid JSON matching `INTAKE_SCHEMA`; result is read from `response.content[0].input`
- **Empty tool result guard** — if `stop_reason` is not `end_turn` but no `tool_use` blocks are present, the loop breaks rather than appending an empty user message (which causes a 400 from the API)
- **Thinking blocks** — specialist responses include thinking blocks; the full `response.content` (including thinking) is preserved as the assistant message before tool results are appended

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required |
| `BVA_API_BASE_URL` | `https://bva-api-524576132881.us-central1.run.app` | BVA API endpoint |
