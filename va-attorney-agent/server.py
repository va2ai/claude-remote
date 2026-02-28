"""FastAPI server — wraps the VA Attorney Research Agent for Cloud Run deployment."""

import json
import os
import sys
import traceback
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from anthropic import AsyncAnthropic
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langfuse import get_client as get_langfuse
from pydantic import BaseModel

from orchestrator import run
from structurer import structure_memo


# ── Lifespan ──────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Flush observability on shutdown
    try:
        get_langfuse().flush()
    except Exception:
        pass


# ── App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="VA Attorney Research Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────


class ResearchRequest(BaseModel):
    query: str
    depth: str = "standard"


class FollowupRequest(BaseModel):
    query: str
    initial_findings: dict
    user_response: str


# ── Endpoints ─────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/mobile/research")
async def research(req: ResearchRequest):
    """Run the full research pipeline and return structured JSON."""
    client = AsyncAnthropic()
    try:
        # Run the multi-agent pipeline
        memo_text = await run(client, req.query)

        # Structure the text memo into frontend-expected JSON
        structured = await structure_memo(client, memo_text, req.query)

        return JSONResponse(content=structured)

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        try:
            get_langfuse().flush()
        except Exception:
            pass


@app.post("/api/mobile/research/followup")
async def followup(req: FollowupRequest):
    """Run a follow-up analysis incorporating the user's response."""
    client = AsyncAnthropic()
    try:
        # Build a follow-up prompt that includes the initial findings context
        followup_query = (
            f"ORIGINAL QUERY:\n{req.query}\n\n"
            f"INITIAL ANALYSIS FINDINGS:\n{json.dumps(req.initial_findings, indent=2)}\n\n"
            f"VETERAN'S ADDITIONAL INFORMATION:\n{req.user_response}\n\n"
            f"Please refine the analysis incorporating this new information. "
            f"Focus on how the additional details change the assessment, "
            f"update any action items, and provide updated recommendations."
        )

        # Run the pipeline again with the enriched context
        memo_text = await run(client, followup_query)

        # Structure into frontend JSON
        structured = await structure_memo(client, memo_text, req.query)

        return JSONResponse(content=structured)

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        try:
            get_langfuse().flush()
        except Exception:
            pass


# ── Entrypoint ────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        timeout_keep_alive=620,
        log_level="info",
    )
