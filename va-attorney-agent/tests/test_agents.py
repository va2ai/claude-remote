"""Tests for the specialist agent tool loop in agents.py."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents import run_specialist


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

    with patch("agents.dispatch_tool", new=AsyncMock(return_value='{"result": "case found"}')):
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

    with patch("agents.dispatch_tool", new=AsyncMock(return_value="{}")):
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

    with patch("agents.dispatch_tool", new=AsyncMock(return_value="{}")):
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

    with patch("agents.dispatch_tool", new=AsyncMock(return_value="{}")):
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
