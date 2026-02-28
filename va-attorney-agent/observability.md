# Observability for Claude API (Multi-Agent)

Anthropic has no built-in hooks/callbacks — observability is DIY or third-party.

---

## 1. SDK-Native (Zero Deps)

### Enable raw HTTP logging
```bash
ANTHROPIC_LOG=debug python main.py
```

Or programmatically:
```python
import logging
logging.getLogger("anthropic").setLevel(logging.DEBUG)
```

### Token usage from response
```python
msg = await client.messages.create(...)
print(msg.usage.input_tokens)
print(msg.usage.output_tokens)
print(msg._request_id)  # for Anthropic support escalation
```

For prompt caching, also check `usage.cache_read_input_tokens` and `usage.cache_creation_input_tokens`.

### Raw response headers (rate limits)
```python
response = await client.messages.with_raw_response.create(...)
request_id = response.headers.get("x-request-id")
remaining_tokens = response.headers.get("anthropic-ratelimit-tokens-remaining")
msg = response.parse()
```

---

## 2. httpx Transport Hook (Custom Middleware)

The SDK uses `httpx` internally — inject a custom transport to intercept every HTTP call:

```python
import time, json, logging
import httpx
from anthropic import AsyncAnthropic, DefaultAsyncHttpxClient

logger = logging.getLogger("anthropic.observability")

class ObservabilityTransport(httpx.AsyncBaseTransport):
    def __init__(self, wrapped: httpx.AsyncBaseTransport):
        self._wrapped = wrapped

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        start = time.monotonic()
        try:
            body = json.loads(request.content)
            model = body.get("model", "unknown")
            tool_count = len(body.get("tools", []))
        except Exception:
            model, tool_count = "unknown", 0

        logger.info(f"[REQUEST] {request.method} model={model} tools={tool_count}")

        response = await self._wrapped.handle_async_request(request)
        latency = time.monotonic() - start
        logger.info(
            f"[RESPONSE] {response.status_code} latency={latency:.3f}s "
            f"request_id={response.headers.get('request-id', 'N/A')}"
        )
        return response

def make_observed_client() -> AsyncAnthropic:
    transport = ObservabilityTransport(httpx.AsyncHTTPTransport())
    return AsyncAnthropic(http_client=DefaultAsyncHttpxClient(transport=transport))
```

---

## 3. Full Multi-Agent Wrapper (`observed_call`)

Zero new dependencies. Captures everything including thinking blocks and TTFB.

```python
import asyncio, time, uuid, json, logging
from dataclasses import dataclass, field
from typing import Any, Optional
from anthropic import AsyncAnthropic

logger = logging.getLogger("agent.observability")

MODEL_COSTS = {
    "claude-opus-4-6":    {"input": 15.0,  "output": 75.0},
    "claude-sonnet-4-6":  {"input": 3.0,   "output": 15.0},
    "claude-haiku-4-5":   {"input": 0.8,   "output": 4.0},
}

@dataclass
class Span:
    span_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    agent_name: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    thinking_tokens: int = 0
    latency_s: float = 0.0
    time_to_first_token_s: float = 0.0
    tool_calls: list[dict] = field(default_factory=list)
    stop_reason: str = ""
    request_id: str = ""
    error: Optional[str] = None
    cost_usd: float = 0.0

    def calculate_cost(self):
        costs = MODEL_COSTS.get(self.model, {"input": 0, "output": 0})
        self.cost_usd = (
            (self.input_tokens / 1_000_000) * costs["input"]
            + (self.output_tokens / 1_000_000) * costs["output"]
        )


class ObservabilityCollector:
    def __init__(self):
        self.spans: list[Span] = []

    def record(self, span: Span):
        span.calculate_cost()
        self.spans.append(span)
        logger.info(
            f"[SPAN] agent={span.agent_name} model={span.model} "
            f"in={span.input_tokens} out={span.output_tokens} "
            f"latency={span.latency_s:.2f}s ttfb={span.time_to_first_token_s:.2f}s "
            f"tools={len(span.tool_calls)} cost=${span.cost_usd:.6f} "
            f"stop={span.stop_reason} req_id={span.request_id}"
        )

    def summary(self) -> dict:
        return {
            "total_spans": len(self.spans),
            "total_input_tokens": sum(s.input_tokens for s in self.spans),
            "total_output_tokens": sum(s.output_tokens for s in self.spans),
            "total_cost_usd": sum(s.cost_usd for s in self.spans),
            "total_latency_s": sum(s.latency_s for s in self.spans),
            "total_tool_calls": sum(len(s.tool_calls) for s in self.spans),
            "errors": [s.error for s in self.spans if s.error],
        }


collector = ObservabilityCollector()


async def observed_call(
    client: AsyncAnthropic,
    agent_name: str,
    messages: list,
    tools: list = None,
    model: str = "claude-opus-4-6",
    max_tokens: int = 4096,
    thinking_budget: int = 0,
    parent_id: str = None,
) -> tuple[Any, Span]:
    """Wraps a single messages.stream() call with full observability."""
    span = Span(agent_name=agent_name, model=model, parent_id=parent_id)

    create_kwargs = dict(model=model, max_tokens=max_tokens, messages=messages)
    if tools:
        create_kwargs["tools"] = tools
    if thinking_budget > 0:
        create_kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}

    start = time.monotonic()
    first_token_time = None
    tool_calls = []
    current_tool = None
    thinking_chars = 0

    try:
        async with client.messages.stream(**create_kwargs) as stream:
            async for event in stream:
                if first_token_time is None and event.type in (
                    "content_block_delta", "content_block_start"
                ):
                    first_token_time = time.monotonic() - start

                if event.type == "message_start":
                    u = event.message.usage
                    span.input_tokens = u.input_tokens
                    span.cache_read_tokens = getattr(u, "cache_read_input_tokens", 0)
                    span.cache_write_tokens = getattr(u, "cache_creation_input_tokens", 0)

                elif event.type == "message_delta":
                    span.output_tokens = event.usage.output_tokens
                    span.stop_reason = event.delta.stop_reason or ""

                elif event.type == "content_block_start":
                    b = event.content_block
                    if b.type == "tool_use":
                        current_tool = {"id": b.id, "name": b.name, "raw_input": ""}

                elif event.type == "content_block_delta":
                    d = event.delta
                    if d.type == "input_json_delta" and current_tool:
                        current_tool["raw_input"] += d.partial_json
                    elif d.type == "thinking_delta":
                        thinking_chars += len(d.thinking)

                elif event.type == "content_block_stop" and current_tool:
                    try:
                        current_tool["input"] = json.loads(current_tool["raw_input"])
                    except json.JSONDecodeError:
                        current_tool["input"] = {}
                    tool_calls.append(current_tool)
                    current_tool = None

            final_msg = await stream.get_final_message()

        span.latency_s = time.monotonic() - start
        span.time_to_first_token_s = first_token_time or span.latency_s
        span.tool_calls = tool_calls
        span.request_id = final_msg._request_id or ""
        span.thinking_tokens = thinking_chars // 4  # rough estimate

        collector.record(span)
        return final_msg, span

    except Exception as exc:
        span.latency_s = time.monotonic() - start
        span.error = str(exc)
        collector.record(span)
        raise
```

---

## 4. Third-Party Integrations

### Langfuse (Recommended — open source, self-hostable)

```bash
pip install langfuse
```

```python
from langfuse.anthropic import anthropic  # drop-in replacement
from langfuse.decorators import observe, langfuse_context

client = anthropic.AsyncAnthropic()

@observe()
async def run_specialist(facts: dict):
    # auto-traces tokens, cost, latency, tool calls
    msg = await client.messages.create(...)
    return msg

@observe()
async def orchestrator(query: str):
    langfuse_context.update_current_trace(name="va-attorney-agent", tags=["prod"])
    return await run_specialist(query)
```

### Helicone (Zero code change — proxy-based)

```python
client = AsyncAnthropic(
    base_url="https://anthropic.helicone.ai",
    default_headers={
        "Helicone-Auth": f"Bearer {HELICONE_API_KEY}",
        "Helicone-Property-Agent": "researcher",
        "Helicone-Session-Id": "session-abc",
    },
)
# All existing code works unchanged
```

### W&B Weave

```bash
pip install weave
```

```python
import weave
from anthropic import AsyncAnthropic

weave.init("va-attorney-agent")
client = AsyncAnthropic()

@weave.op()
async def run_specialist(facts: dict):
    return await client.messages.create(...)
```

### OpenTelemetry

```bash
pip install opentelemetry-sdk opentelemetry-instrumentation-anthropic
```

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry import trace
from opentelemetry_instrumentation_anthropic import AnthropicInstrumentor

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

AnthropicInstrumentor().instrument()  # must be before creating client

from anthropic import AsyncAnthropic
client = AsyncAnthropic()
```

---

## 5. Capability Comparison

| | Token usage | Latency | Tool calls | Thinking | Cost | TTFB | Self-host |
|---|---|---|---|---|---|---|---|
| SDK native | Yes | Manual | Manual | Manual | Manual | Manual | N/A |
| httpx hook | Parse | Auto | No | No | No | No | N/A |
| `observed_call` | Yes | Auto | Yes | Yes | Calc | Yes | N/A |
| Langfuse | Auto | Auto | Auto | No | Auto | No | Yes |
| Helicone | Auto | Auto | Auto | No | Auto | No | No |
| W&B Weave | Auto | Auto | Partial | No | Auto | No | No |
| OpenTelemetry | Auto | Auto | Auto | No | Partial | No | Yes |

**Thinking blocks + TTFB require manual stream event capture** — no third-party tool handles these yet.

---

## 6. Recommendation for va-attorney-agent

**Development:** `ANTHROPIC_LOG=debug` + `msg._request_id` logged on every call.

**Production:** Add `observed_call()` wrapper (Section 3) for full per-agent telemetry with zero new deps, then layer **Langfuse** for a UI and long-term storage.
