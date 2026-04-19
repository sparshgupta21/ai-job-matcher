"""
AI Job Matcher v2.0 — Agent 2: Job Hunter
Searches for jobs across multiple portals, scores matches against CV profile.
"""

import logging
from agents.base import BaseAgent
from models import (
    AgentMemory, JobListing, PipelineStatus,
)
from guardrails import wrap_user_content_safely
from prompts import AGENT2_JOB_SEARCH_PROMPT, AGENT2_QUERY_GENERATION_PROMPT
from job_search import search_jobs

logger = logging.getLogger(__name__)


class JobHunterAgent(BaseAgent):
    """
    Agent 2: Job Hunter
    - Reads CVProfile + UserPreferences from shared memory
    - Builds intelligent search queries
    - Searches Tavily → DuckDuckGo → JSearch → Adzuna → Demo
    - Scores each job against the CV profile
    - Outputs list[JobListing] to shared memory
    """

    agent_name = "job_hunter"
    agent_description = "Searches and ranks jobs from Indian and global portals"

    def run(self, memory: AgentMemory) -> AgentMemory:
        """Execute job search and matching pipeline."""
        memory.pipeline_status = PipelineStatus.AGENT2_RUNNING

        if memory.cv_profile is None:
            memory.add_error("No CV profile available. Agent 1 must run first.")
            return memory

        cv_profile = memory.cv_profile
        prefs = memory.preferences

        # Build search query
        search_query = self._build_search_query(cv_profile, prefs)
        location = prefs.location if prefs else ""

        logger.info(f"[{self.agent_name}] Searching: '{search_query}' in '{location}'")

        # Execute multi-provider search
        job_type = prefs.job_type if prefs else "Any"
        experience = prefs.experience_level if prefs else "Any"
        date_posted = prefs.date_posted if prefs else "Any time"

        raw_jobs, source, warning = search_jobs(
            query=search_query,
            location=location,
            job_type=job_type,
            experience=experience,
            num_results=10,
            date_posted=date_posted,
        )

        if not raw_jobs:
            memory.add_error("No jobs found. Try broadening your search criteria.")
            memory.pipeline_status = PipelineStatus.AGENT2_DONE
            return memory

        # Convert to JobListing models
        job_listings = []
        for job_dict in raw_jobs:
            listing = JobListing(
                title=job_dict.get("title", "N/A"),
                company=job_dict.get("company", "N/A"),
                location=job_dict.get("location", "N/A"),
                description=job_dict.get("description", ""),
                salary=job_dict.get("salary", "Not specified"),
                job_type=job_dict.get("job_type", "N/A"),
                apply_url=job_dict.get("apply_url", "#"),
                source=job_dict.get("source", "unknown"),
                posted_date=job_dict.get("date_posted", ""),
                skills_required=job_dict.get("skills_required", []),
            )
            job_listings.append(listing)

        # Score jobs using LLM (if CV text available)
        if cv_profile.raw_text:
            job_listings = self._score_jobs(cv_profile, job_listings)

        # Sort by match score descending
        job_listings.sort(key=lambda j: j.match_score, reverse=True)

        memory.job_results = job_listings
        memory.pipeline_status = PipelineStatus.AGENT2_DONE

        logger.info(
            f"[{self.agent_name}] Found {len(job_listings)} jobs "
            f"from {source}, top score: {job_listings[0].match_score:.0f}%"
        )

        return memory

    def _build_search_query(self, cv_profile, prefs) -> str:
        """Build an effective search query from CV profile and preferences."""
        parts = []

        # Use explicit target role if provided
        if prefs and prefs.target_role and prefs.target_role.strip():
            parts.append(prefs.target_role.strip())
        else:
            # Try to infer from work history
            if cv_profile.work_history:
                parts.append(cv_profile.work_history[0].title)
            elif cv_profile.sections.get("experience"):
                exp_text = cv_profile.sections["experience"]
                lines = exp_text.split("\n")
                for line in lines[:3]:
                    line = line.strip()
                    if line and len(line) < 60 and not any(c.isdigit() for c in line[:4]):
                        parts.append(line)
                        break

        # Add key skills
        if prefs and prefs.key_skills:
            parts.append(", ".join(prefs.key_skills[:3]))
        elif cv_profile.skills:
            parts.append(", ".join(cv_profile.skills[:3]))

        if not parts:
            parts.append("software developer")

        return " ".join(parts[:3])

    def _score_jobs(self, cv_profile, jobs: list[JobListing]) -> list[JobListing]:
        """Use LLM to score job matches against the CV profile."""
        try:
            # Format jobs for LLM evaluation
            jobs_text = "\n\n".join([
                f"### Job {i+1}: {j.title}\n"
                f"- Company: {j.company}\n"
                f"- Location: {j.location}\n"
                f"- Description: {j.description[:300]}\n"
                f"- Skills Required: {', '.join(j.skills_required[:5])}\n"
                for i, j in enumerate(jobs[:10])
            ])

            safe_cv = wrap_user_content_safely(cv_profile.raw_text)
            user_content = (
                safe_cv
                + f"\n\n--- JOB LISTINGS TO EVALUATE ---\n{jobs_text}\n"
                + f"\nCandidate Skills: {', '.join(cv_profile.skills[:10])}\n"
                + f"Experience Level: {cv_profile.experience_level.value}\n"
            )

            response = self.call_model(
                system_prompt=AGENT2_JOB_SEARCH_PROMPT,
                user_content=user_content,
                max_tokens=3000,
            )

            # Parse scores from LLM response
            jobs = self._parse_scores(jobs, response)

        except Exception as e:
            logger.warning(f"LLM scoring failed, using skill-based scoring: {e}")
            jobs = self._skill_based_scoring(cv_profile, jobs)

        return jobs

    def _parse_scores(self, jobs: list[JobListing], llm_response: str) -> list[JobListing]:
        """Parse match scores from LLM response and assign to jobs."""
        import re

        lines = llm_response.split("\n")
        score_pattern = re.compile(r"(\d+)\s*%")

        job_idx = 0
        for line in lines:
            if job_idx >= len(jobs):
                break

            # Look for "Job 1", "Job 2", etc. or "Match Score"
            if any(marker in line.lower() for marker in [f"job {job_idx + 1}", "match score", "score"]):
                match = score_pattern.search(line)
                if match:
                    try:
                        score = min(100.0, max(0.0, float(match.group(1))))
                        jobs[job_idx].match_score = score
                        job_idx += 1
                    except ValueError:
                        pass

            # Extract matching/missing skills
            if "matching" in line.lower() and job_idx > 0:
                skills = re.findall(r"`([^`]+)`|'([^']+)'", line)
                matching = [s[0] or s[1] for s in skills]
                if matching:
                    jobs[job_idx - 1].matching_skills = matching[:5]

            if "missing" in line.lower() or "gap" in line.lower():
                skills = re.findall(r"`([^`]+)`|'([^']+)'", line)
                missing = [s[0] or s[1] for s in skills]
                if missing and job_idx > 0:
                    jobs[job_idx - 1].missing_skills = missing[:5]

        # Assign default scores to unscored jobs
        for job in jobs:
            if job.match_score == 0.0:
                job.match_score = 50.0  # default moderate match

        return jobs

    def _skill_based_scoring(self, cv_profile, jobs: list[JobListing]) -> list[JobListing]:
        """Fallback: Score jobs based on skill overlap."""
        cv_skills = {s.lower() for s in cv_profile.skills}

        for job in jobs:
            job_skills = {s.lower() for s in job.skills_required}

            if job_skills:
                overlap = cv_skills & job_skills
                score = (len(overlap) / len(job_skills)) * 100
                job.match_score = min(100.0, score)
                job.matching_skills = list(overlap)[:5]
                job.missing_skills = list(job_skills - cv_skills)[:5]
            else:
                # No skills listed, check description
                desc_lower = job.description.lower()
                matches = sum(1 for s in cv_skills if s in desc_lower)
                job.match_score = min(100.0, matches * 15.0)

        return jobs
