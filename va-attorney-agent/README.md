# VA Attorney Research Agent

A multi-agent AI system for researching veterans' disability claims. Accepts a veteran's plain-text narrative and produces a comprehensive legal research memo covering regulatory analysis, case law, C&P exam critique, evidence strategy, and procedural options.

## How It Works

Three phases run sequentially:

1. **Intake** (Haiku) — parses the narrative into structured facts (condition, symptoms, ratings, appeal lanes, TDIU eligibility, etc.)
2. **Research** (5x Opus in parallel) — each specialist agent uses real BVA API tools to look up CFR regulations, BVA case law, KnowVA guidance, and Federal Register documents
3. **Synthesis** (Opus) — Senior Partner consolidates all five memos into a single unified research memo

Total runtime is typically 2–4 minutes depending on how many tool calls the specialists make.

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

# Save the memo to a file (progress goes to stderr, memo to stdout)
python main.py claim.txt > memo.md
```

## Output

Progress is printed to stderr so it doesn't pollute the memo:

```
============================================================
PHASE 1: Parsing veteran's narrative...
  Intake complete in 2.1s
  Condition: PTSD
  Current rating: 50%
  Target rating: 70%
  Symptoms: 8 identified
...
PHASE 2: Running 5 specialist agents in parallel...
  [Regulatory Analyst] Starting research...
  [Case Law Researcher] Calling tool: bva_search
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

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required |
| `BVA_API_BASE_URL` | `https://bva-api-524576132881.us-central1.run.app` | BVA API endpoint |
