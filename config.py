"""
AI Job Matcher v2.0 — Configuration
Central configuration for LLM models, search APIs, agent settings, and app controls.
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
    "₹0 - ₹5 LPA",
    "₹5 - ₹10 LPA",
    "₹10 - ₹15 LPA",
    "₹15 - ₹25 LPA",
    "₹25 - ₹40 LPA",
    "₹40 - ₹60 LPA",
    "₹60 LPA+",
    "$0 - $30,000",
    "$30,000 - $50,000",
    "$50,000 - $75,000",
    "$75,000 - $100,000",
    "$100,000 - $150,000",
    "$150,000+",
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

APP_VERSION = "2.0.0"

# ─────────────────────────────────────────────
# Search API Settings
# ─────────────────────────────────────────────

# Tavily (primary for AI agent search)
TAVILY_API_URL = "https://api.tavily.com/search"

# JSearch (RapidAPI)
JSEARCH_API_URL = "https://jsearch.p.rapidapi.com/search"
JSEARCH_API_HOST = "jsearch.p.rapidapi.com"

# Adzuna
ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs"

# Job portals to target via web search (India-first, then global)
JOB_PORTAL_SITES_INDIA = [
    "naukri.com",
    "linkedin.com/jobs",
    "iimjobs.com",
    "foundit.in",        # formerly monster.in
    "shine.com",
    "instahyre.com",
    "glassdoor.co.in",
]

JOB_PORTAL_SITES_GLOBAL = [
    "linkedin.com/jobs",
    "indeed.com",
    "glassdoor.com",
    "monster.com",
    "ziprecruiter.com",
]

# ─────────────────────────────────────────────
# Agent-Specific Settings
# ─────────────────────────────────────────────

AGENT_TOKEN_BUDGETS = {
    "cv_ingestor": 2048,
    "job_hunter": 3000,
    "application_helper": 2000,
}

# Search result limits per source
MAX_TAVILY_RESULTS = 8
MAX_DUCKDUCKGO_RESULTS = 10
MAX_JSEARCH_RESULTS = 10
MAX_ADZUNA_RESULTS = 10

# Search provider priority (tried in order)
SEARCH_PROVIDER_PRIORITY = [
    "tavily",
    "duckduckgo",
    "jsearch",
    "adzuna",
    "demo",
]
