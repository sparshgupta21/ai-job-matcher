"""
AI Job Matcher v2.0 — Agent 1: CV Ingestor
Parses CV files, extracts structured data, and stores CVProfile in shared memory.
"""

import logging
from agents.base import BaseAgent
from models import (
    AgentMemory, CVProfile, ContactInfo, EducationEntry,
    WorkEntry, ExperienceLevel, PipelineStatus,
)
from guardrails import wrap_user_content_safely, sanitize_text
from prompts import AGENT1_CV_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class CVIngestorAgent(BaseAgent):
    """
    Agent 1: CV Ingestor
    - Takes uploaded CV file (PDF/DOCX)
    - Extracts text, contact info, skills, sections
    - Uses LLM to enhance extraction (summary, experience level)
    - Outputs CVProfile Pydantic model to shared memory
    """

    agent_name = "cv_ingestor"
    agent_description = "Parses CV and extracts structured career data"

    def run(self, memory: AgentMemory) -> AgentMemory:
        """Execute CV ingestion pipeline."""
        memory.pipeline_status = PipelineStatus.AGENT1_RUNNING

        # The CV file should already be parsed by the time we get here
        # (cv_parser.py handles the raw extraction)
        # This agent enhances with LLM analysis

        if memory.cv_profile is None:
            memory.add_error("No CV data available. Please upload a CV first.")
            return memory

        cv_profile = memory.cv_profile

        # Skip LLM enhancement if no raw text
        if not cv_profile.raw_text or len(cv_profile.raw_text.strip()) < 50:
            memory.add_error("CV text too short for analysis.")
            return memory

        # Call LLM for enhanced analysis
        try:
            safe_content = wrap_user_content_safely(cv_profile.raw_text)
            llm_analysis = self.call_model(
                system_prompt=AGENT1_CV_SYSTEM_PROMPT,
                user_content=safe_content,
                max_tokens=2048,
            )

            # Enhance the profile with LLM insights
            cv_profile = self._enhance_profile(cv_profile, llm_analysis)
            memory.cv_profile = cv_profile

        except Exception as e:
            logger.warning(f"LLM enhancement failed, using regex-only profile: {e}")
            # Profile is still usable from regex extraction

        memory.pipeline_status = PipelineStatus.AGENT1_DONE
        logger.info(
            f"[{self.agent_name}] CV processed: "
            f"{len(cv_profile.skills)} skills, "
            f"{cv_profile.experience_level.value} level"
        )

        return memory

    def _enhance_profile(self, profile: CVProfile, llm_text: str) -> CVProfile:
        """Enhance CV profile with LLM-extracted insights."""
        text_lower = llm_text.lower()

        # Try to extract experience level from LLM output
        level_map = {
            "entry level": ExperienceLevel.ENTRY,
            "entry-level": ExperienceLevel.ENTRY,
            "junior": ExperienceLevel.JUNIOR,
            "mid-level": ExperienceLevel.MID,
            "mid level": ExperienceLevel.MID,
            "senior": ExperienceLevel.SENIOR,
            "lead": ExperienceLevel.LEAD,
            "principal": ExperienceLevel.LEAD,
            "executive": ExperienceLevel.EXECUTIVE,
            "c-level": ExperienceLevel.EXECUTIVE,
        }

        for key, level in level_map.items():
            if key in text_lower:
                profile.experience_level = level
                break

        # Try to extract years of experience
        import re
        year_patterns = [
            r"(\d+)\+?\s*years?\s*(of)?\s*experience",
            r"experience[:\s]*(\d+)\+?\s*years?",
            r"(\d+)\+?\s*yrs",
        ]
        for pattern in year_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    profile.experience_years = int(match.group(1))
                except (ValueError, IndexError):
                    pass
                break

        # Extract summary if missing
        if not profile.summary and "summary" in text_lower:
            lines = llm_text.split("\n")
            capture = False
            summary_lines = []
            for line in lines:
                if "summary" in line.lower() and ("**" in line or ":" in line):
                    capture = True
                    continue
                if capture:
                    if line.strip().startswith("**") or line.strip().startswith("#"):
                        break
                    if line.strip():
                        summary_lines.append(line.strip())
                    if len(summary_lines) >= 3:
                        break
            if summary_lines:
                profile.summary = " ".join(summary_lines)[:500]

        # Store the LLM analysis in sections for display
        profile.sections["llm_analysis"] = llm_text

        return profile


def parse_cv_to_profile(file_path: str) -> CVProfile:
    """
    Parse a CV file into a CVProfile Pydantic model.
    Uses the existing cv_parser module for text extraction,
    then structures into the Pydantic model.
    """
    from cv_parser import parse_cv

    cv_data = parse_cv(file_path)

    contact = ContactInfo(
        name=cv_data.get("contact", {}).get("name", ""),
        email=cv_data.get("contact", {}).get("email", ""),
        phone=cv_data.get("contact", {}).get("phone", ""),
        linkedin=cv_data.get("contact", {}).get("linkedin", ""),
    )

    return CVProfile(
        contact=contact,
        skills=cv_data.get("skills", []),
        raw_text=cv_data.get("raw_text", ""),
        sections=cv_data.get("sections", {}),
        file_name=cv_data.get("file_name", ""),
    )
