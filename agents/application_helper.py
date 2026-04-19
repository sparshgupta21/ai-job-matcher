"""
AI Job Matcher v2.0 — Agent 3: Application Helper
Generates apply links, auto-fill data, and cover letter snippets for matched jobs.
"""

import logging
from agents.base import BaseAgent
from models import (
    AgentMemory, ApplicationPackage, PipelineStatus,
)
from guardrails import wrap_user_content_safely
from prompts import AGENT3_APPLICATION_PROMPT

logger = logging.getLogger(__name__)


class ApplicationHelperAgent(BaseAgent):
    """
    Agent 3: Application Helper
    - Reads CVProfile + JobListings from shared memory
    - For each top-matched job:
        - Provides direct apply link
        - Generates auto-fill field mapping from CV
        - Creates a tailored cover letter snippet
        - Lists application-specific tips
    - Outputs list[ApplicationPackage] to shared memory
    """

    agent_name = "application_helper"
    agent_description = "Prepares application packages with auto-fill and tips"

    def run(self, memory: AgentMemory) -> AgentMemory:
        """Execute application preparation pipeline."""
        memory.pipeline_status = PipelineStatus.AGENT3_RUNNING

        if memory.cv_profile is None:
            memory.add_error("No CV profile available. Agent 1 must run first.")
            return memory

        if not memory.job_results:
            memory.add_error("No job results available. Agent 2 must run first.")
            memory.pipeline_status = PipelineStatus.AGENT3_DONE
            return memory

        cv_profile = memory.cv_profile

        # Build auto-fill data from CV (rule-based, no LLM needed)
        auto_fill = self._build_auto_fill(cv_profile)

        # Process top jobs
        top_jobs = memory.job_results[:5]  # Top 5 matches

        # Use LLM for tailored tips and cover letter snippets
        applications = []
        for i, job in enumerate(top_jobs):
            try:
                app_package = self._build_application_package(
                    cv_profile, job, auto_fill, i + 1, len(top_jobs),
                )
                applications.append(app_package)
            except Exception as e:
                logger.warning(f"Failed to build package for job {i+1}: {e}")
                # Still create a basic package
                applications.append(ApplicationPackage(
                    job=job,
                    apply_url=job.apply_url,
                    auto_fill_data=auto_fill,
                    cover_letter_snippet="",
                    application_tips=["Upload your CV to the application portal"],
                ))

        memory.applications = applications
        memory.pipeline_status = PipelineStatus.AGENT3_DONE

        logger.info(
            f"[{self.agent_name}] Prepared {len(applications)} "
            f"application packages"
        )

        return memory

    def _build_auto_fill(self, cv_profile) -> dict[str, str]:
        """Build auto-fill fields from CV profile (no LLM needed)."""
        contact = cv_profile.contact

        auto_fill = {
            "Full Name": contact.name or "Not found in CV",
            "Email": contact.email or "Not found in CV",
            "Phone": contact.phone or "Not found in CV",
            "LinkedIn URL": contact.linkedin or "Not found in CV",
            "Skills": ", ".join(cv_profile.skills[:15]) if cv_profile.skills else "Not found in CV",
            "Experience Level": cv_profile.experience_level.value,
            "Years of Experience": str(cv_profile.experience_years) if cv_profile.experience_years > 0 else "Not specified",
        }

        # Add work history
        if cv_profile.work_history:
            latest = cv_profile.work_history[0]
            auto_fill["Current Job Title"] = latest.title or "Not found in CV"
            auto_fill["Current Company"] = latest.company or "Not found in CV"
        elif cv_profile.sections.get("experience"):
            exp_lines = cv_profile.sections["experience"].split("\n")
            if exp_lines:
                auto_fill["Current Job Title"] = exp_lines[0].strip()[:60]
                auto_fill["Current Company"] = "See CV"

        # Add education
        if cv_profile.education:
            latest_edu = cv_profile.education[0]
            auto_fill["Highest Education"] = (
                f"{latest_edu.degree} - {latest_edu.institution}"
                if latest_edu.institution else latest_edu.degree
            )
        elif cv_profile.sections.get("education"):
            edu_lines = cv_profile.sections["education"].split("\n")
            if edu_lines:
                auto_fill["Highest Education"] = edu_lines[0].strip()[:80]

        # Summary
        if cv_profile.summary:
            auto_fill["Professional Summary"] = cv_profile.summary[:300]
        elif cv_profile.sections.get("summary"):
            auto_fill["Professional Summary"] = cv_profile.sections["summary"][:300]

        return auto_fill

    def _build_application_package(self, cv_profile, job, auto_fill,
                                   job_num, total_jobs) -> ApplicationPackage:
        """Build a complete application package for one job."""
        # Generate cover letter snippet and tips via LLM
        cover_letter = ""
        tips = []

        try:
            safe_cv = wrap_user_content_safely(cv_profile.raw_text)
            user_content = (
                safe_cv
                + f"\n\n--- TARGET JOB ---\n"
                + f"Job Title: {job.title}\n"
                + f"Company: {job.company}\n"
                + f"Location: {job.location}\n"
                + f"Description: {job.description[:400]}\n"
                + f"Required Skills: {', '.join(job.skills_required[:5])}\n"
                + f"Match Score: {job.match_score:.0f}%\n"
                + f"Matching Skills: {', '.join(job.matching_skills[:5])}\n"
                + f"Missing Skills: {', '.join(job.missing_skills[:5])}\n"
                + f"\nProvide:\n"
                + f"1. A 3-4 sentence cover letter opening paragraph\n"
                + f"2. 3 specific application tips for this role\n"
            )

            response = self.call_model(
                system_prompt=AGENT3_APPLICATION_PROMPT,
                user_content=user_content,
                max_tokens=1000,
            )

            # Parse cover letter and tips from response
            cover_letter, tips = self._parse_application_response(response)

        except Exception as e:
            logger.warning(f"LLM application help failed for job {job_num}: {e}")

        # Fallback tips if LLM didn't provide any
        if not tips:
            tips = self._generate_fallback_tips(cv_profile, job)

        return ApplicationPackage(
            job=job,
            apply_url=job.apply_url,
            auto_fill_data=auto_fill,
            cover_letter_snippet=cover_letter,
            application_tips=tips,
        )

    def _parse_application_response(self, response: str) -> tuple[str, list[str]]:
        """Parse cover letter and tips from LLM response."""
        cover_letter = ""
        tips = []

        lines = response.split("\n")
        in_cover_letter = False
        in_tips = False
        cover_lines = []

        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()

            # Detect cover letter section
            if any(kw in lower for kw in ["cover letter", "opening paragraph", "dear"]):
                in_cover_letter = True
                in_tips = False
                if "dear" in lower or not any(kw in lower for kw in ["cover letter", "opening"]):
                    cover_lines.append(stripped)
                continue

            # Detect tips section
            if any(kw in lower for kw in ["application tip", "tips:", "advice:"]):
                in_cover_letter = False
                in_tips = True
                continue

            if in_cover_letter and stripped:
                if stripped.startswith(("**", "##", "---")) and cover_lines:
                    in_cover_letter = False
                else:
                    cover_lines.append(stripped)

            if in_tips and stripped:
                # Remove bullet/number prefixes
                clean = stripped.lstrip("0123456789.-•*) ").strip()
                if clean and len(clean) > 10:
                    tips.append(clean)

        cover_letter = " ".join(cover_lines).strip()

        # If no structured parsing worked, use first substantial paragraph as cover letter
        if not cover_letter and response:
            paragraphs = [p.strip() for p in response.split("\n\n") if len(p.strip()) > 50]
            if paragraphs:
                cover_letter = paragraphs[0][:500]

        return cover_letter[:500], tips[:5]

    def _generate_fallback_tips(self, cv_profile, job) -> list[str]:
        """Generate rule-based application tips when LLM is unavailable."""
        tips = []

        # Skill gap tips
        if job.missing_skills:
            missing = ", ".join(job.missing_skills[:3])
            tips.append(
                f"Consider highlighting transferable skills related to: {missing}"
            )

        # Match score tips
        if job.match_score >= 80:
            tips.append("Strong match! Apply with confidence and tailor your summary to this role.")
        elif job.match_score >= 50:
            tips.append("Good match. Emphasize your relevant experience in your cover letter.")
        else:
            tips.append("Partial match. Focus on any overlap and show willingness to learn.")

        # Source-specific tips
        if "naukri" in job.source.lower():
            tips.append("Update your Naukri profile to match this job's keywords for better visibility.")
        elif "linkedin" in job.source.lower():
            tips.append("Connect with recruiters at this company on LinkedIn before applying.")
        elif "iimjobs" in job.source.lower():
            tips.append("IIMJobs focuses on premium roles — highlight leadership experience.")

        # Generic application tip
        tips.append("Upload your CV in PDF format for best compatibility with ATS systems.")

        return tips[:4]
