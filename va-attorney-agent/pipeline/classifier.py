"""Query classifier — determines routing strategy before the main pipeline runs."""

import sys
from anthropic import AsyncAnthropic
from langfuse import observe

from config import INTAKE_MODEL, CLASSIFICATION_SCHEMA, ROUTING_PROFILES
from prompts.classifier import SYSTEM_PROMPT


def _default_classification() -> dict:
    """Safe fallback — always routes to full rating_increase pipeline."""
    return {
        "query_type": "rating_increase",
        "confidence": 0.0,
        "classification_rationale": "Fallback: classifier failed or returned low confidence",
        "topic_keywords": [],
        "skip_intake": False,
        "quick_answer": False,
        "response_depth": "standard",
        "routing": ROUTING_PROFILES["rating_increase"],
    }


def _enrich(result: dict) -> dict:
    """Attach the routing profile and enforce consistency."""
    query_type = result.get("query_type", "rating_increase")

    # Low confidence -> fall back to full pipeline
    if result.get("confidence", 0) < 0.7:
        query_type = "rating_increase"
        result["query_type"] = query_type
        result["classification_rationale"] += " [confidence too low, defaulting to rating_increase]"

    result["routing"] = ROUTING_PROFILES[query_type]

    # Enforce consistency
    if result["quick_answer"]:
        result["routing"] = {**result["routing"], "specialists": []}
        result["skip_intake"] = True

    return result


@observe(name="classify_query")
async def classify_query(client: AsyncAnthropic, raw_text: str) -> dict:
    """Classify the incoming query to determine routing strategy.

    Uses Haiku with forced tool call. Returns enriched classification dict.
    Never raises — returns rating_increase defaults on any failure.
    """
    try:
        response = await client.messages.create(
            model=INTAKE_MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": raw_text[:4000]}],  # cap input
            tools=[{
                "name": CLASSIFICATION_SCHEMA["name"],
                "description": CLASSIFICATION_SCHEMA["description"],
                "input_schema": CLASSIFICATION_SCHEMA["schema"],
            }],
            tool_choice={"type": "tool", "name": CLASSIFICATION_SCHEMA["name"]},
        )

        result = response.content[0].input
        enriched = _enrich(result)

        print(
            f"  [Classifier] type={enriched['query_type']} "
            f"confidence={enriched['confidence']:.2f} "
            f"quick={enriched['quick_answer']}",
            file=sys.stderr,
        )
        return enriched

    except Exception as e:
        print(f"  [Classifier] ERROR: {e} — falling back to rating_increase", file=sys.stderr)
        return _default_classification()
