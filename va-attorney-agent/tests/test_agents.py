"""Tests for the specialist agent tool loop in agents.py."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from pipeline.agents import run_specialist, run_selected_specialists, SPECIALIST_PROMPT_OVERRIDES


# ── Helpers ───────────────────────────────────────────────────────

def make_text_block(text="Here is my memo."):
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def make_tool_use_block(name="bva_search", tool_id="tool_1", input_data=None):
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.id = tool_id
    block.input = input_data or {"query": "PTSD"}
    return block


def make_response(stop_reason, content_blocks):
    response = MagicMock()
    response.stop_reason = stop_reason
    response.content = content_blocks
    return response


def make_client(*responses):
    """Return a mock AsyncAnthropic client that yields responses in order."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(side_effect=list(responses))
    return client


def make_http_client():
    return MagicMock()


FACTS = {"claimed_condition": "PTSD", "current_rating": 50}
TOOLS = [{"name": "bva_search", "description": "search", "input_schema": {}}]


# ── Tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_exits_immediately_on_end_turn():
    """Agent returns memo on the first end_turn without any tool calls."""
    response = make_response("end_turn", [make_text_block("My memo text.")])
    client = make_client(response)

    result = await run_specialist(
        client=client,
        http_client=make_http_client(),
        name="case_law_researcher",
        display_name="Case Law Researcher",
        system_prompt="You are a researcher.",
        tools=TOOLS,
        facts=FACTS,
    )

    assert result["name"] == "Case Law Researcher"
    assert result["memo"] == "My memo text."
    assert client.messages.create.call_count == 1


@pytest.mark.asyncio
async def test_tool_call_then_end_turn():
    """Agent makes one tool call, gets result, then returns memo on end_turn."""
    tool_response = make_response("tool_use", [make_tool_use_block()])
    final_response = make_response("end_turn", [make_text_block("Final memo.")])
    client = make_client(tool_response, final_response)

    with patch("pipeline.agents.dispatch_tool", new=AsyncMock(return_value='{"result": "case found"}')):
        result = await run_specialist(
            client=client,
            http_client=make_http_client(),
            name="case_law_researcher",
            display_name="Case Law Researcher",
            system_prompt="You are a researcher.",
            tools=TOOLS,
            facts=FACTS,
        )

    assert result["memo"] == "Final memo."
    assert client.messages.create.call_count == 2

    # Second call must include the tool_result user message
    second_call_messages = client.messages.create.call_args_list[1][1]["messages"]
    user_msgs = [m for m in second_call_messages if m["role"] == "user"]
    tool_result_msgs = [
        m for m in user_msgs
        if isinstance(m["content"], list)
        and any(c.get("type") == "tool_result" for c in m["content"])
    ]
    assert len(tool_result_msgs) == 1


@pytest.mark.asyncio
async def test_no_empty_user_message_when_no_tool_blocks():
    """If stop_reason != end_turn but content has no tool_use blocks,
    no empty user message is appended (fixes the 400 error)."""
    # Response has a text block but stop_reason is not end_turn (edge case)
    weird_response = make_response("max_tokens", [make_text_block("partial")])
    end_response = make_response("end_turn", [make_text_block("done")])
    client = make_client(weird_response, end_response)

    with patch("pipeline.agents.dispatch_tool", new=AsyncMock(return_value="{}")):
        result = await run_specialist(
            client=client,
            http_client=make_http_client(),
            name="regulatory_analyst",
            display_name="Regulatory Analyst",
            system_prompt="You are an analyst.",
            tools=TOOLS,
            facts=FACTS,
        )

    # Verify no message with empty content was ever sent
    for call in client.messages.create.call_args_list:
        messages = call[1]["messages"]
        for msg in messages:
            content = msg.get("content")
            assert content != [], f"Empty content list sent in message: {msg}"
            assert content is not None


@pytest.mark.asyncio
async def test_multiple_tool_calls_in_one_response():
    """All tool_use blocks in a single response are executed and returned together."""
    tool_block_1 = make_tool_use_block(name="bva_search", tool_id="t1")
    tool_block_2 = make_tool_use_block(name="cfr_section", tool_id="t2")
    tool_response = make_response("tool_use", [tool_block_1, tool_block_2])
    final_response = make_response("end_turn", [make_text_block("memo")])
    client = make_client(tool_response, final_response)

    with patch("pipeline.agents.dispatch_tool", new=AsyncMock(return_value="{}")):
        result = await run_specialist(
            client=client,
            http_client=make_http_client(),
            name="evidence_strategist",
            display_name="Evidence Strategist",
            system_prompt="You are a strategist.",
            tools=TOOLS,
            facts=FACTS,
        )

    assert result["memo"] == "memo"
    second_call_messages = client.messages.create.call_args_list[1][1]["messages"]
    tool_result_content = next(
        m["content"] for m in second_call_messages
        if isinstance(m.get("content"), list)
        and any(c.get("type") == "tool_result" for c in m["content"])
    )
    assert len(tool_result_content) == 2
    assert {c["tool_use_id"] for c in tool_result_content} == {"t1", "t2"}


@pytest.mark.asyncio
async def test_hits_max_iterations():
    """Agent returns the safety-valve memo after MAX_TOOL_ITERATIONS."""
    from config import MAX_TOOL_ITERATIONS

    # Always return tool_use — never end_turn
    tool_response = make_response("tool_use", [make_tool_use_block()])
    client = make_client(*[tool_response] * (MAX_TOOL_ITERATIONS + 1))

    with patch("pipeline.agents.dispatch_tool", new=AsyncMock(return_value="{}")):
        result = await run_specialist(
            client=client,
            http_client=make_http_client(),
            name="procedural_tactician",
            display_name="Procedural Tactician",
            system_prompt="You are a tactician.",
            tools=TOOLS,
            facts=FACTS,
        )

    assert "maximum tool iterations" in result["memo"]
    assert client.messages.create.call_count == MAX_TOOL_ITERATIONS


# ── Phase 3 Tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_selected_specialists_uses_prompt_overrides():
    """When query_type='cue_claim' is passed, the regulatory_analyst specialist
    is called with the CUE-specific prompt, not its default prompt."""
    from pipeline.agents import SPECIALISTS, SPECIALIST_PROMPT_OVERRIDES
    from prompts.cue_claim import REGULATORY_PROMPT as CUE_REGULATORY_PROMPT

    # Build a response that immediately ends the loop
    response = make_response("end_turn", [make_text_block("CUE memo.")])
    client = make_client(response)

    captured_prompts = {}

    async def fake_run_specialist(**kwargs):
        captured_prompts[kwargs["name"]] = kwargs["system_prompt"]
        return {"name": kwargs["display_name"], "memo": "CUE memo."}

    with patch("pipeline.agents.run_specialist", side_effect=fake_run_specialist):
        await run_selected_specialists(
            client=client,
            facts=FACTS,
            specialist_names=["regulatory_analyst"],
            query_type="cue_claim",
        )

    # The regulatory_analyst must have received the CUE override prompt
    assert "regulatory_analyst" in captured_prompts
    assert captured_prompts["regulatory_analyst"] == CUE_REGULATORY_PROMPT

    # Confirm it differs from the default prompt
    default_prompt = next(
        s["system_prompt"] for s in SPECIALISTS if s["name"] == "regulatory_analyst"
    )
    assert captured_prompts["regulatory_analyst"] != default_prompt


@pytest.mark.asyncio
async def test_run_selected_specialists_falls_back_to_default_prompt():
    """When no query_type is passed, the default specialist prompt is used."""
    from pipeline.agents import SPECIALISTS

    response = make_response("end_turn", [make_text_block("Default memo.")])
    client = make_client(response)

    captured_prompts = {}

    async def fake_run_specialist(**kwargs):
        captured_prompts[kwargs["name"]] = kwargs["system_prompt"]
        return {"name": kwargs["display_name"], "memo": "Default memo."}

    with patch("pipeline.agents.run_specialist", side_effect=fake_run_specialist):
        await run_selected_specialists(
            client=client,
            facts=FACTS,
            specialist_names=["regulatory_analyst"],
            # no query_type passed — should fall back to default
        )

    default_prompt = next(
        s["system_prompt"] for s in SPECIALISTS if s["name"] == "regulatory_analyst"
    )
    assert captured_prompts["regulatory_analyst"] == default_prompt


@pytest.mark.asyncio
async def test_synthesis_accepts_model_param():
    """synthesize() accepts a model param and passes it to the API call."""
    from pipeline.synthesis import synthesize

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Final memo text."

    response = MagicMock()
    response.content = [text_block]

    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(return_value=response)

    custom_model = "claude-sonnet-4-6"
    result = await synthesize(
        client=client,
        facts=FACTS,
        memos=[{"name": "Regulatory Analyst", "memo": "Memo content."}],
        model=custom_model,
    )

    assert result == "Final memo text."
    # Verify the custom model was passed to the API
    call_kwargs = client.messages.create.call_args[1]
    assert call_kwargs["model"] == custom_model
