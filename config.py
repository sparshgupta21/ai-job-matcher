"""
AI Job Matcher — Configuration
Central configuration for LLM models, job search filters, and app settings.
"""

# ─────────────────────────────────────────────
# Curated LLM Models (small params only)
# ─────────────────────────────────────────────

AVAILABLE_MODELS = [
    {
        "id": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
        "display_name": "SmolLM2 1.7B (Fast & Light)",
        "params": "1.7B",
        "mode": "inference_api",
        "description": "Ultra-lightweight, great for quick analysis",
    },
    {
        "id": "meta-llama/Llama-3.2-1B-Instruct",
        "display_name": "Llama 3.2 1B (Fastest)",
        "params": "1B",
        "mode": "inference_api",
        "description": "Meta's fastest model, excellent for simple tasks",
    },
    {
        "id": "google/gemma-2-2b-it",
        "display_name": "Gemma 2 2B (Balanced)",
        "params": "2B",
        "mode": "inference_api",
        "description": "Google's efficient model with strong instruction following",
    },
    {
        "id": "Qwen/Qwen2.5-1.5B-Instruct",
        "display_name": "Qwen 2.5 1.5B (Multilingual)",
        "params": "1.5B",
        "mode": "inference_api",
        "description": "Excellent multilingual support, good reasoning",
    },
    {
        "id": "Qwen/Qwen2.5-3B-Instruct",
        "display_name": "Qwen 2.5 3B (Best Quality)",
        "params": "3B",
        "mode": "inference_api",
        "description": "Best quality-to-size ratio, strong analysis",
    },
    {
        "id": "microsoft/Phi-3.5-mini-instruct",
        "display_name": "Phi 3.5 Mini (Strong Reasoning)",
        "params": "3.8B",
        "mode": "inference_api",
        "description": "Microsoft's reasoning-optimized model",
    },
]

# Build display name → model ID mapping
MODEL_CHOICES = [m["display_name"] for m in AVAILABLE_MODELS]
MODEL_MAP = {m["display_name"]: m["id"] for m in AVAILABLE_MODELS}
MODEL_INFO = {m["display_name"]: m for m in AVAILABLE_MODELS}

# ─────────────────────────────────────────────
# Job Search Filter Options
# ─────────────────────────────────────────────

EXPERIENCE_LEVELS = [
    "Any",
    "Internship / Entry Level (0-1 years)",
    "Junior (1-3 years)",
    "Mid-Level (3-5 years)",
    "Senior (5-10 years)",
    "Lead / Principal (10+ years)",
    "Executive / C-Level",
]

JOB_TYPES = [
    "Any",
    "Full-Time",
    "Part-Time",
    "Contract",
    "Internship",
    "Freelance / Gig",
]

WORK_MODES = [
    "Any",
    "Remote",
    "Hybrid",
    "On-site",
]

EDUCATION_LEVELS = [
    "Any",
    "High School",
    "Associate's Degree",
    "Bachelor's Degree",
    "Master's Degree",
    "PhD / Doctorate",
    "Professional Certification",
]

SALARY_RANGES = [
    "Any",
    "$0 - $30,000",
    "$30,000 - $50,000",
    "$50,000 - $75,000",
    "$75,000 - $100,000",
    "$100,000 - $150,000",
    "$150,000 - $200,000",
    "$200,000+",
]

DATE_POSTED_OPTIONS = [
    "Any time",
    "Past 24 hours",
    "Past 3 days",
    "Past week",
    "Past month",
]

# ─────────────────────────────────────────────
# Application Settings
# ─────────────────────────────────────────────

MAX_FILE_SIZE_MB = 5
ALLOWED_FILE_TYPES = [".pdf", ".docx", ".doc"]
MAX_JOBS_TO_DISPLAY = 10
MAX_CV_TEXT_LENGTH = 15000  # characters
SESSION_RATE_LIMIT = 20  # max requests per session

# ─────────────────────────────────────────────
# API Settings
# ─────────────────────────────────────────────

JSEARCH_API_URL = "https://jsearch.p.rapidapi.com/search"
JSEARCH_API_HOST = "jsearch.p.rapidapi.com"

ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs"
