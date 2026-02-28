# ── Tool Definitions (Anthropic format) ───────────────────────────
# Each tool maps to a real endpoint on the BVA API.

CFR_SECTION = {
    "name": "cfr_section",
    "description": (
        "Look up the exact text of a specific 38 CFR section. "
        "Returns the full regulatory text in markdown format. "
        "Example: part='4', section='130' returns the General Rating "
        "Formula for Mental Disorders."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "CFR part number (e.g. '3', '4', '17')",
            },
            "section": {
                "type": "string",
                "description": "Section number within the part (e.g. '130', '16', '310')",
            },
        },
        "required": ["part", "section"],
    },
}

CFR_SEARCH = {
    "name": "cfr_search",
    "description": (
        "Search across all 38 CFR sections for a query term. "
        "Returns matching sections with snippets. Useful for finding "
        "relevant regulations when you don't know the exact section number."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "q": {
                "type": "string",
                "description": "Search query (e.g. 'PTSD rating criteria', 'secondary service connection')",
            },
            "part": {
                "type": "string",
                "description": "Optional: filter to a specific CFR part (e.g. '4')",
            },
            "per_page": {
                "type": "integer",
                "description": "Results per page (max 100, default 20)",
            },
        },
        "required": ["q"],
    },
}

CFR_DIAGNOSTIC_CODE = {
    "name": "cfr_diagnostic_code",
    "description": (
        "Look up a VA diagnostic code to find the condition name and "
        "CFR citation. Example: code='9411' returns PTSD information."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "VA diagnostic code (e.g. '9411' for PTSD, '6847' for sleep apnea)",
            },
        },
        "required": ["code"],
    },
}

BVA_SEARCH = {
    "name": "bva_search",
    "description": (
        "Search Board of Veterans' Appeals decisions. Returns case titles, "
        "snippets, URLs, and dates. Use specific legal terms and fact patterns "
        "for best results. Example: 'PTSD 70 percent increase panic attacks "
        "occupational impairment'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for BVA decisions",
            },
            "year": {
                "type": "integer",
                "description": "Optional: filter to a specific year (1992-2025)",
            },
            "per_page": {
                "type": "integer",
                "description": "Results per page (max 20, default 20)",
            },
        },
        "required": ["query"],
    },
}

BVA_GET_CASE = {
    "name": "bva_get_case",
    "description": (
        "Retrieve the full text and metadata of a specific BVA decision "
        "by its URL. Use this after finding a case via bva_search to read "
        "the complete decision."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The case URL from bva_search results",
            },
        },
        "required": ["url"],
    },
}

BVA_ANALYZE = {
    "name": "bva_analyze",
    "description": (
        "Analyze a BVA decision text for specific keywords and VA legal terms. "
        "Returns keyword counts, contexts, and readability metrics. Useful for "
        "finding how specific legal standards were applied in a case."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The case URL to analyze",
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Keywords to search for in the case text (e.g. ['Mauerhan', 'occupational impairment'])",
            },
        },
        "required": ["url"],
    },
}

FEDERAL_REGISTER_SEARCH = {
    "name": "federal_register_search",
    "description": (
        "Search Federal Register documents for VA rulemaking, proposed rules, "
        "and notices. Useful for finding proposed regulatory changes like the "
        "2026 mental health rating criteria update."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "q": {
                "type": "string",
                "description": "Search query",
            },
            "type": {
                "type": "string",
                "enum": ["Rule", "Proposed Rule", "Notice"],
                "description": "Optional: filter by document type",
            },
            "cfr_title": {
                "type": "integer",
                "description": "Optional: CFR title number (e.g. 38)",
            },
            "cfr_part": {
                "type": "string",
                "description": "Optional: CFR part (e.g. '4')",
            },
        },
        "required": ["q"],
    },
}

KNOWVA_SEARCH = {
    "name": "knowva_search",
    "description": (
        "Search the KnowVA knowledge base for VA policy guidance, "
        "adjudication procedures, and training materials. Returns article "
        "summaries with IDs that can be retrieved in full via knowva_article."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "q": {
                "type": "string",
                "description": "Search query (e.g. 'PTSD rating criteria', 'C&P exam adequacy')",
            },
            "pagesize": {
                "type": "integer",
                "description": "Number of results (max 100, default 30)",
            },
        },
        "required": ["q"],
    },
}

KNOWVA_ARTICLE = {
    "name": "knowva_article",
    "description": (
        "Retrieve the full content of a KnowVA article by its ID. "
        "Use after knowva_search to read complete policy guidance."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "article_id": {
                "type": "integer",
                "description": "The article ID from knowva_search results",
            },
        },
        "required": ["article_id"],
    },
}

RAG_SEARCH = {
    "name": "rag_search",
    "description": (
        "Semantic search across VA rating criteria, adjudication guidance, "
        "and KnowVA content. Uses embeddings for meaning-based retrieval. "
        "Best for conceptual queries like 'what constitutes occupational "
        "impairment for mental health ratings'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "q": {
                "type": "string",
                "description": "Semantic search query",
            },
            "content_type": {
                "type": "string",
                "enum": ["rating_criteria", "adjudication", "guidance"],
                "description": "Optional: filter by content type",
            },
            "part": {
                "type": "string",
                "description": "Optional: filter to specific CFR part",
            },
            "source": {
                "type": "string",
                "enum": ["cfr", "knowva"],
                "description": "Optional: filter by source",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results (max 20, default 5)",
            },
        },
        "required": ["q"],
    },
}

# ── All Tools ─────────────────────────────────────────────────────
ALL_TOOLS = [
    CFR_SECTION,
    CFR_SEARCH,
    CFR_DIAGNOSTIC_CODE,
    BVA_SEARCH,
    BVA_GET_CASE,
    BVA_ANALYZE,
    FEDERAL_REGISTER_SEARCH,
    KNOWVA_SEARCH,
    KNOWVA_ARTICLE,
    RAG_SEARCH,
]

# ── Per-Agent Tool Assignments ────────────────────────────────────
AGENT_TOOLS = {
    "regulatory_analyst": [
        CFR_SECTION,
        CFR_SEARCH,
        CFR_DIAGNOSTIC_CODE,
        FEDERAL_REGISTER_SEARCH,
        RAG_SEARCH,
    ],
    "case_law_researcher": [
        BVA_SEARCH,
        BVA_GET_CASE,
        BVA_ANALYZE,
        RAG_SEARCH,
    ],
    "cp_exam_critic": [
        CFR_SECTION,
        BVA_SEARCH,
        BVA_GET_CASE,
    ],
    "evidence_strategist": [
        CFR_SECTION,
        CFR_SEARCH,
        CFR_DIAGNOSTIC_CODE,
        BVA_SEARCH,
        KNOWVA_SEARCH,
        KNOWVA_ARTICLE,
    ],
    "procedural_tactician": [
        CFR_SECTION,
        CFR_SEARCH,
        BVA_SEARCH,
        FEDERAL_REGISTER_SEARCH,
    ],
}
