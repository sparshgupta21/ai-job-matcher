"""
AI Job Matcher v2.0 — Pydantic Data Contracts
Typed data models for inter-agent communication.
All agents exchange data ONLY through these validated schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class ExperienceLevel(str, Enum):
    ENTRY = "Entry Level"
    JUNIOR = "Junior"
    MID = "Mid-Level"
    SENIOR = "Senior"
    LEAD = "Lead / Principal"
    EXECUTIVE = "Executive / C-Level"
    UNKNOWN = "Unknown"


class JobType(str, Enum):
    FULL_TIME = "Full-Time"
    PART_TIME = "Part-Time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"
    FREELANCE = "Freelance"
    ANY = "Any"


class WorkMode(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "On-site"
    ANY = "Any"


class SearchSource(str, Enum):
    TAVILY = "tavily"
    DUCKDUCKGO = "duckduckgo"
    SERPER = "serper"
    JSEARCH = "jsearch"
    ADZUNA = "adzuna"
    DEMO = "demo"


# ─────────────────────────────────────────────
# Agent 1 Output: CV Profile
# ─────────────────────────────────────────────

class ContactInfo(BaseModel):
    """Candidate contact information extracted from CV."""
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if v and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            return ""  # silently drop invalid
        return v


class EducationEntry(BaseModel):
    """Single education record."""
    degree: str = ""
    institution: str = ""
    year: str = ""
    field_of_study: str = ""


class WorkEntry(BaseModel):
    """Single work history record."""
    title: str = ""
    company: str = ""
    duration: str = ""
    description: str = ""


class CVProfile(BaseModel):
    """
    Agent 1 (CV Ingestor) output.
    Consumed by Agent 2 (Job Hunter) and Agent 3 (Application Helper).
    """
    contact: ContactInfo = Field(default_factory=ContactInfo)
    skills: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN
    education: list[EducationEntry] = Field(default_factory=list)
    work_history: list[WorkEntry] = Field(default_factory=list)
    summary: str = ""
    raw_text: str = ""
    certifications: list[str] = Field(default_factory=list)
    file_name: str = ""

    # Legacy compat — expose sections like the old cv_data dict
    sections: dict[str, str] = Field(default_factory=dict)

    @field_validator("skills")
    @classmethod
    def deduplicate_skills(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for s in v:
            key = s.strip().lower()
            if key and key not in seen:
                seen.add(key)
                deduped.append(s.strip())
        return deduped


# ─────────────────────────────────────────────
# User Preferences (Dashboard Inputs)
# ─────────────────────────────────────────────

class UserPreferences(BaseModel):
    """
    User-provided search preferences from the dashboard.
    Consumed by Agent 2 (Job Hunter).
    """
    location: str = ""
    target_role: str = ""
    key_skills: list[str] = Field(default_factory=list)
    experience_level: str = "Any"
    job_type: str = "Any"
    work_mode: str = "Any"
    education_level: str = "Any"
    salary_range: str = "Any"
    date_posted: str = "Any time"


# ─────────────────────────────────────────────
# Agent 2 Output: Job Listings
# ─────────────────────────────────────────────

class JobListing(BaseModel):
    """
    A single job listing found by Agent 2 (Job Hunter).
    Consumed by Agent 3 (Application Helper).
    """
    title: str = "N/A"
    company: str = "N/A"
    location: str = "N/A"
    description: str = ""
    salary: str = "Not specified"
    job_type: str = "N/A"
    apply_url: str = "#"
    source: str = "unknown"
    match_score: float = Field(default=0.0, ge=0.0, le=100.0)
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    posted_date: str = ""
    skills_required: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Agent 3 Output: Application Packages
# ─────────────────────────────────────────────

class ApplicationPackage(BaseModel):
    """
    Agent 3 (Application Helper) output for each matched job.
    Contains everything a user needs to apply.
    """
    job: JobListing
    apply_url: str = "#"
    auto_fill_data: dict[str, str] = Field(default_factory=dict)
    cover_letter_snippet: str = ""
    application_tips: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Shared Agent Memory
# ─────────────────────────────────────────────

class PipelineStatus(str, Enum):
    IDLE = "idle"
    AGENT1_RUNNING = "agent1_running"
    AGENT1_DONE = "agent1_done"
    AGENT2_RUNNING = "agent2_running"
    AGENT2_DONE = "agent2_done"
    AGENT3_RUNNING = "agent3_running"
    AGENT3_DONE = "agent3_done"
    COMPLETED = "completed"
    ERROR = "error"


class AgentMemory(BaseModel):
    """
    Central shared memory for the agent pipeline.
    Each agent reads from and writes to this store via Pydantic.
    """
    cv_profile: Optional[CVProfile] = None
    preferences: Optional[UserPreferences] = None
    job_results: list[JobListing] = Field(default_factory=list)
    applications: list[ApplicationPackage] = Field(default_factory=list)
    pipeline_status: PipelineStatus = PipelineStatus.IDLE
    errors: list[str] = Field(default_factory=list)

    # Per-session API tokens (NEVER stored in os.environ)
    # These are unique per user request, isolating concurrent users.
    hf_token: str = ""
    tavily_api_key: str = ""

    # Agent timing (for dashboard display)
    agent1_time: float = 0.0
    agent2_time: float = 0.0
    agent3_time: float = 0.0

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.pipeline_status = PipelineStatus.ERROR

    def is_healthy(self) -> bool:
        return self.pipeline_status != PipelineStatus.ERROR
