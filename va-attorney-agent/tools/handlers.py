import json
import httpx
from config import BVA_API_BASE_URL


async def dispatch_tool(
    tool_name: str, tool_input: dict, http_client: httpx.AsyncClient
) -> str:
    """Route a tool call to the appropriate BVA API endpoint.

    Returns a JSON string of the API response, or an error message string.
    """
    try:
        handler = TOOL_ROUTES.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        return await handler(tool_input, http_client)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": f"API returned {e.response.status_code}",
            "detail": e.response.text[:500],
        })
    except httpx.RequestError as e:
        return json.dumps({"error": f"Request failed: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Tool execution error: {str(e)}"})


# ── Individual Tool Handlers ──────────────────────────────────────


async def _cfr_section(inp: dict, client: httpx.AsyncClient) -> str:
    resp = await client.get(
        f"{BVA_API_BASE_URL}/cfr/section",
        params={"part": inp["part"], "section": inp["section"]},
        timeout=30.0,
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


async def _cfr_search(inp: dict, client: httpx.AsyncClient) -> str:
    params = {"q": inp["q"]}
    if inp.get("part"):
        params["part"] = inp["part"]
    if inp.get("per_page"):
        params["per_page"] = inp["per_page"]
    resp = await client.get(
        f"{BVA_API_BASE_URL}/cfr/search", params=params, timeout=30.0
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


async def _cfr_diagnostic_code(inp: dict, client: httpx.AsyncClient) -> str:
    resp = await client.get(
        f"{BVA_API_BASE_URL}/cfr/dc/{inp['code']}", timeout=30.0
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


async def _bva_search(inp: dict, client: httpx.AsyncClient) -> str:
    body = {"query": inp["query"]}
    if inp.get("year"):
        body["year"] = inp["year"]
    if inp.get("per_page"):
        body["per_page"] = inp["per_page"]
    resp = await client.post(
        f"{BVA_API_BASE_URL}/search", json=body, timeout=30.0
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


async def _bva_get_case(inp: dict, client: httpx.AsyncClient) -> str:
    resp = await client.get(
        f"{BVA_API_BASE_URL}/case",
        params={"url": inp["url"], "full_text": "true"},
        timeout=60.0,
    )
    resp.raise_for_status()
    data = resp.json()
    # Truncate full_text if extremely long to stay within context limits
    if data.get("full_text") and len(data["full_text"]) > 15000:
        data["full_text"] = data["full_text"][:15000] + "\n\n[...TRUNCATED...]"
    return json.dumps(data)


async def _bva_analyze(inp: dict, client: httpx.AsyncClient) -> str:
    params = {"url": inp["url"]}
    if inp.get("keywords"):
        params["keywords"] = inp["keywords"]
    if inp.get("context"):
        params["context"] = "true"
    resp = await client.get(
        f"{BVA_API_BASE_URL}/analyze/text", params=params, timeout=30.0
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


async def _federal_register_search(inp: dict, client: httpx.AsyncClient) -> str:
    params = {"q": inp["q"]}
    if inp.get("type"):
        params["type"] = inp["type"]
    if inp.get("cfr_title"):
        params["cfr_title"] = inp["cfr_title"]
    if inp.get("cfr_part"):
        params["cfr_part"] = inp["cfr_part"]
    resp = await client.get(
        f"{BVA_API_BASE_URL}/federal-register/search",
        params=params,
        timeout=30.0,
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


async def _knowva_search(inp: dict, client: httpx.AsyncClient) -> str:
    params = {"q": inp["q"]}
    if inp.get("pagesize"):
        params["pagesize"] = inp["pagesize"]
    resp = await client.get(
        f"{BVA_API_BASE_URL}/knowva/search", params=params, timeout=30.0
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


async def _knowva_article(inp: dict, client: httpx.AsyncClient) -> str:
    resp = await client.get(
        f"{BVA_API_BASE_URL}/knowva/article/{inp['article_id']}",
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    # Truncate very long articles
    if data.get("content") and len(data["content"]) > 10000:
        data["content"] = data["content"][:10000] + "\n\n[...TRUNCATED...]"
    return json.dumps(data)


async def _rag_search(inp: dict, client: httpx.AsyncClient) -> str:
    params = {"q": inp["q"]}
    if inp.get("content_type"):
        params["content_type"] = inp["content_type"]
    if inp.get("part"):
        params["part"] = inp["part"]
    if inp.get("source"):
        params["source"] = inp["source"]
    if inp.get("top_k"):
        params["top_k"] = inp["top_k"]
    resp = await client.get(
        f"{BVA_API_BASE_URL}/rag/search", params=params, timeout=30.0
    )
    resp.raise_for_status()
    return json.dumps(resp.json())


# ── Route Table ───────────────────────────────────────────────────

TOOL_ROUTES = {
    "cfr_section": _cfr_section,
    "cfr_search": _cfr_search,
    "cfr_diagnostic_code": _cfr_diagnostic_code,
    "bva_search": _bva_search,
    "bva_get_case": _bva_get_case,
    "bva_analyze": _bva_analyze,
    "federal_register_search": _federal_register_search,
    "knowva_search": _knowva_search,
    "knowva_article": _knowva_article,
    "rag_search": _rag_search,
}
