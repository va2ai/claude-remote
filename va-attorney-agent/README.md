# VA Attorney Research Agent

A multi-agent AI system for researching veterans' disability claims. Accepts a veteran's plain-text narrative and produces a calibrated legal research memo — from a 2-paragraph eligibility answer to a full multi-section legal memo with BVA citations, depending on what the query calls for.

## How It Works

Four phases run sequentially:

1. **Classify** (`claude-haiku-4-5`) — determines query type and response depth before any research begins; routes to the appropriate pipeline
2. **Intake** (`claude-haiku-4-5`) — parses the narrative into structured facts (condition, symptoms, ratings, appeal lanes, TDIU eligibility, etc.)
3. **Research** (`claude-sonnet-4-6`, parallel) — specialist agents use real BVA API tools to look up CFR regulations, BVA case law, KnowVA guidance, and Federal Register documents
4. **Synthesis** (`claude-opus-4-6` or `claude-sonnet-4-6`) — Senior Partner consolidates specialist memos into a single unified output calibrated to the requested depth

## Query Routing

The classifier determines both the pipeline and output depth before research starts.

### Query Types

| Type | Specialists | Synthesis | Description |
|------|-------------|-----------|-------------|
| `rating_increase` | All 5 | opus | Full claim narrative with denied increase |
| `eligibility_check` | Regulatory + Procedural | sonnet | "Do I qualify for TDIU/SMC/etc.?" |
| `appeal_strategy` | Case Law + Procedural | sonnet | Which appeal lane to file |
| `cue_claim` | Regulatory + Case Law | opus | Clear and Unmistakable Error research |
| `quick_question` | None | None | Simple factual VA law question |
| `benefits_overview` | None | None | Educational overview with no claim details |

### Response Depth

| Depth | Output | Trigger signals |
|-------|--------|-----------------|
| `brief` | 2–4 paragraphs, direct answer | "Do I qualify?", "Am I eligible?", yes/no questions |
| `standard` | Structured sections, key citations | "How do I apply?", "What are my options?" |
| `comprehensive` | Full legal memo with all citations, tables, BVA cases | "Analyze my claim", detailed narrative + explicit analysis asks |

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

Progress is printed to stderr so it does not pollute the memo:

```
============================================================
CLASSIFYING query...
  Query type  : eligibility_check
  Confidence  : 0.95
  Quick path  : False
  Specialists : ['regulatory_analyst', 'procedural_tactician']
  Depth       : brief
...
PHASE 2: Running 2 specialist agent(s) in parallel...
  [Regulatory Analyst] Starting research...
  [Regulatory Analyst] iter=1/6 stop=tool_use in=1234 out=456 blocks=[thinking, tool_use]
  [Regulatory Analyst]   -> tool: cfr_section input={"part": "4", "section": "16a"}
  [Regulatory Analyst] Complete (2 iteration(s), 1843 chars)
...
PHASE 3: Synthesizing final memo...
TOTAL TIME: 42.1s
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
| Classifier/Intake model | `claude-haiku-4-5-20251001` | Fast and cheap |
| Specialist model | `claude-sonnet-4-6` | Was opus-4-6; 5x cheaper |
| Synthesis model | `claude-opus-4-6` | Full pipeline only |
| Eligibility/Appeal synthesis | `claude-sonnet-4-6` | Lighter model for focused queries |
| Specialist max tokens | 4096 | |
| Synthesis max tokens | 8000 | |
| Max tool iterations | 5 | Safety valve per specialist |

## Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/test_agents.py -v
```

| Test | What it verifies |
|------|-----------------|
| `test_exits_immediately_on_end_turn` | Returns memo on first `end_turn` with no tool calls |
| `test_tool_call_then_end_turn` | One tool call round-trip; tool_result included in second request |
| `test_no_empty_user_message_when_no_tool_blocks` | No empty user message when stop is not `end_turn` but no tool_use blocks exist (prevents 400 error) |
| `test_multiple_tool_calls_in_one_response` | All tool_use blocks in a single response are batched together |
| `test_hits_max_iterations` | Safety valve returns fallback memo after `MAX_TOOL_ITERATIONS` |
| `test_run_selected_specialists_uses_prompt_overrides` | Query-type-specific prompts are injected per specialist |
| `test_run_selected_specialists_falls_back_to_default_prompt` | Default prompts used when no override exists |
| `test_synthesis_accepts_model_param` | Synthesis model override is passed through correctly |

## Implementation Notes

- **Classifier-first routing** — Haiku classifies query type and response depth before intake runs; `quick_question` and `benefits_overview` skip intake and all specialists entirely
- **Response depth calibration** — `response_depth` flows from classifier → specialists → synthesis; each layer appends a depth hint to its user message so output scales to `brief` / `standard` / `comprehensive`
- **Intake structured output** — uses `tool_choice: {type: "tool"}` to force the schema tool; result read from `response.content[0].input`
- **Empty tool result guard** — if `stop_reason` is not `end_turn` but no `tool_use` blocks are present, the loop breaks rather than appending an empty user message (prevents 400)
- **Thinking blocks** — full `response.content` (including thinking) is preserved as the assistant message before tool results are appended; stripping thinking blocks causes API errors with extended thinking models

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required |
| `BVA_API_BASE_URL` | `https://bva-api-524576132881.us-central1.run.app` | BVA API endpoint |
