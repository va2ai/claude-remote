import os

# ── API Configuration ─────────────────────────────────────────────
BVA_API_BASE_URL = os.getenv(
    "BVA_API_BASE_URL",
    "https://bva-api-524576132881.us-central1.run.app",
)

# ── Model Configuration ───────────────────────────────────────────
INTAKE_MODEL = "claude-haiku-4-5-20251001"
SPECIALIST_MODEL = "claude-sonnet-4-6"   # was opus-4-6 (5x cheaper)
SYNTHESIS_MODEL = "claude-opus-4-6"      # keep opus for final memo quality

# ── Token Limits ──────────────────────────────────────────────────
INTAKE_MAX_TOKENS = 2048
SPECIALIST_MAX_TOKENS = 4096   # was 8192
SYNTHESIS_MAX_TOKENS = 8000    # was 16000

# ── Thinking Configuration ────────────────────────────────────────
SPECIALIST_THINKING = {"type": "adaptive"}

# ── Safety Valve ──────────────────────────────────────────────────
MAX_TOOL_ITERATIONS = 5   # was 15

# ── Quick Answer Configuration ────────────────────────────────────
QUICK_ANSWER_MODEL = "claude-haiku-4-5-20251001"
QUICK_ANSWER_MAX_TOKENS = 2048
QUICK_ANSWER_MAX_TOOL_ITERATIONS = 3

# ── Classification Schema ─────────────────────────────────────────
CLASSIFICATION_SCHEMA = {
    "name": "classify_query",
    "description": "Classify the incoming VA query to determine routing strategy",
    "schema": {
        "type": "object",
        "properties": {
            "query_type": {
                "type": "string",
                "enum": [
                    "rating_increase",
                    "quick_question",
                    "eligibility_check",
                    "cue_claim",
                    "appeal_strategy",
                    "benefits_overview",
                ],
                "description": "The query type that best matches the input",
            },
            "confidence": {
                "type": "number",
                "description": "Classification confidence 0.0-1.0",
            },
            "classification_rationale": {
                "type": "string",
                "description": "Brief explanation of why this type was chosen",
            },
            "topic_keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key terms extracted from the query",
            },
            "skip_intake": {
                "type": "boolean",
                "description": "True if structured intake parsing can be skipped",
            },
            "quick_answer": {
                "type": "boolean",
                "description": "True if the full specialist pipeline can be bypassed",
            },
            "response_depth": {
                "type": "string",
                "enum": ["brief", "standard", "comprehensive"],
                "description": "brief = 2-4 paragraphs; standard = structured sections; comprehensive = full legal memo with all citations",
            },
        },
        "required": [
            "query_type",
            "confidence",
            "classification_rationale",
            "topic_keywords",
            "skip_intake",
            "quick_answer",
            "response_depth",
        ],
        "additionalProperties": False,
    },
}

# ── Routing Profiles ──────────────────────────────────────────────
# Defines which specialists run, iteration cap, and models per query type.
ROUTING_PROFILES = {
    "rating_increase": {
        "specialists": [
            "regulatory_analyst",
            "case_law_researcher",
            "cp_exam_critic",
            "evidence_strategist",
            "procedural_tactician",
        ],
        "max_tool_iterations": MAX_TOOL_ITERATIONS,
        "specialist_model": SPECIALIST_MODEL,
        "synthesis_model": SYNTHESIS_MODEL,
        "run_synthesis": True,
        "quick_answer": False,
    },
    "quick_question": {
        "specialists": [],
        "max_tool_iterations": QUICK_ANSWER_MAX_TOOL_ITERATIONS,
        "specialist_model": QUICK_ANSWER_MODEL,
        "synthesis_model": None,
        "run_synthesis": False,
        "quick_answer": True,
    },
    "eligibility_check": {
        "specialists": ["regulatory_analyst", "procedural_tactician"],
        "max_tool_iterations": 6,
        "specialist_model": SPECIALIST_MODEL,
        "synthesis_model": SPECIALIST_MODEL,
        "run_synthesis": True,
        "quick_answer": False,
    },
    "cue_claim": {
        "specialists": ["regulatory_analyst", "case_law_researcher"],
        "max_tool_iterations": MAX_TOOL_ITERATIONS,
        "specialist_model": SPECIALIST_MODEL,
        "synthesis_model": SYNTHESIS_MODEL,
        "run_synthesis": True,
        "quick_answer": False,
    },
    "appeal_strategy": {
        "specialists": ["case_law_researcher", "procedural_tactician"],
        "max_tool_iterations": 6,
        "specialist_model": SPECIALIST_MODEL,
        "synthesis_model": SPECIALIST_MODEL,
        "run_synthesis": True,
        "quick_answer": False,
    },
    "benefits_overview": {
        "specialists": [],
        "max_tool_iterations": QUICK_ANSWER_MAX_TOOL_ITERATIONS,
        "specialist_model": QUICK_ANSWER_MODEL,
        "synthesis_model": None,
        "run_synthesis": False,
        "quick_answer": True,
    },
}

# ── Intake Schema ─────────────────────────────────────────────────
INTAKE_SCHEMA = {
    "name": "veteran_claim_intake",
    "description": "Structured extraction of veteran's disability claim facts",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "current_rating": {
                "type": ["integer", "null"],
                "description": "Current disability rating percentage",
            },
            "target_rating": {
                "type": ["integer", "null"],
                "description": "Rating percentage the veteran is seeking",
            },
            "claimed_condition": {
                "type": "string",
                "description": "Primary condition being claimed (e.g. PTSD, TBI)",
            },
            "symptoms": {
                "type": "array",
                "items": {"type": "string"},
                "description": "All symptoms mentioned by the veteran",
            },
            "impairment_domains": {
                "type": "object",
                "properties": {
                    "work": {
                        "type": "string",
                        "description": "What veteran said about work impairment",
                    },
                    "family_social": {
                        "type": "string",
                        "description": "What veteran said about family/social impairment",
                    },
                    "mood": {
                        "type": "string",
                        "description": "What veteran said about mood disturbance",
                    },
                    "stress_adaptation": {
                        "type": "string",
                        "description": "Difficulty adapting to stressful circumstances",
                    },
                    "cognition": {
                        "type": "string",
                        "description": "Cognitive impairment described",
                    },
                    "navigation": {
                        "type": "string",
                        "description": "Ability to navigate environments",
                    },
                    "self_care": {
                        "type": "string",
                        "description": "Self-care ability described",
                    },
                },
                "required": [
                    "work",
                    "family_social",
                    "mood",
                    "stress_adaptation",
                    "cognition",
                    "navigation",
                    "self_care",
                ],
                "additionalProperties": False,
            },
            "comorbid_conditions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Other service-connected or claimed conditions",
            },
            "employment_status": {
                "type": "string",
                "description": "Current employment situation",
            },
            "denial_date": {
                "type": ["string", "null"],
                "description": "Date of denial if mentioned",
            },
            "denial_language": {
                "type": "string",
                "description": "Exact or paraphrased denial rationale from VA",
            },
            "denial_lane_available": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "SC",
                        "HLR",
                        "BVA_direct",
                        "BVA_evidence",
                        "BVA_hearing",
                    ],
                },
                "description": "Appeal lanes potentially available",
            },
            "bankhead_trigger": {
                "type": "boolean",
                "description": "Whether suicidal ideation is present or mentioned",
            },
            "mittleider_trigger": {
                "type": "boolean",
                "description": "Whether comorbid condition overlap is present that cannot be medically separated",
            },
            "tdiu_threshold_check": {
                "type": "string",
                "enum": ["eligible", "borderline", "not_eligible", "unknown"],
                "description": "TDIU eligibility based on rating thresholds",
            },
            "current_treatment": {
                "type": "string",
                "description": "Current medications and treatment providers",
            },
            "cp_exam_details": {
                "type": "string",
                "description": "What the veteran said about the C&P exam",
            },
            "missing_facts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key facts not provided that would be needed for full analysis",
            },
        },
        "required": [
            "current_rating",
            "target_rating",
            "claimed_condition",
            "symptoms",
            "impairment_domains",
            "comorbid_conditions",
            "employment_status",
            "denial_date",
            "denial_language",
            "denial_lane_available",
            "bankhead_trigger",
            "mittleider_trigger",
            "tdiu_threshold_check",
            "current_treatment",
            "cp_exam_details",
            "missing_facts",
        ],
        "additionalProperties": False,
    },
}
