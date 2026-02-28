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
