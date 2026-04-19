"""
AI Job Matcher v2.0 — Agent Orchestrator
Coordinates the 3-agent pipeline: CV Ingestor → Job Hunter → Application Helper.
Returns formatted results for the Gradio dashboard.
"""

import os
import logging
import time

from models import (
    AgentMemory, UserPreferences, PipelineStatus, CVProfile,
)
from agents.cv_ingestor import CVIngestorAgent, parse_cv_to_profile
from agents.job_hunter import JobHunterAgent
from agents.application_helper import ApplicationHelperAgent
from guardrails import (
    rate_limiter, validate_file_upload, validate_user_inputs,
    sanitize_text,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Central orchestrator that runs the 3-agent pipeline sequentially.
    Manages shared AgentMemory and returns formatted results.
    """

    def __init__(self, model_display_name: str = "SmolLM2 1.7B (Fast & Light)"):
        self.agent1 = CVIngestorAgent(model_display_name)
        self.agent2 = JobHunterAgent(model_display_name)
        self.agent3 = ApplicationHelperAgent(model_display_name)
        self.memory = AgentMemory()

    def run_pipeline(
        self,
        cv_file,
        model_display_name,
        city,
        occupation,
        experience,
        job_type,
        work_mode,
        education,
        salary_range,
        skills_input,
        date_posted,
        hf_token_input="",
        tavily_key_input="",
    ) -> tuple[str, str, str, str, str]:
        """
        Run the full 3-agent pipeline.

        Returns:
            (agent_status_md, jobs_md, autofill_md, cv_analysis_md, ai_insights_md)
        """
        pipeline_start = time.time()

        # ── Step 0: Set API tokens if provided via UI ──────────
        if hf_token_input and hf_token_input.strip():
            os.environ["HF_TOKEN"] = hf_token_input.strip()
        if tavily_key_input and tavily_key_input.strip():
            os.environ["TAVILY_API_KEY"] = tavily_key_input.strip()

        # ── Step 1: Rate limiting ──────────────────────────────
        if not rate_limiter.is_allowed():
            msg = (
                "## ⏳ Rate Limit Reached\n\n"
                "You've exceeded the maximum number of requests per hour. "
                "Please wait and try again.\n\n"
                f"*Remaining: {rate_limiter.remaining()} requests*"
            )
            return _status_error(), msg, "", "", ""

        # ── Step 2: Validate inputs ───────────────────────────
        if not cv_file:
            return _status_error(), "## 📄 Please Upload Your CV\n\nUpload a PDF or DOCX file to get started.", "", "", ""

        is_valid, error = validate_file_upload(cv_file)
        if not is_valid:
            return _status_error(), f"## ❌ File Error\n\n{error}", "", "", ""

        city = sanitize_text(city or "")
        occupation = sanitize_text(occupation or "")
        skills_input = sanitize_text(skills_input or "")

        is_valid, error = validate_user_inputs(city, occupation, skills_input)
        if not is_valid:
            return _status_error(), f"## 🔒 Security Alert\n\n{error}", "", "", ""

        # ── Step 3: Reinitialize agents with selected model ───
        self.agent1 = CVIngestorAgent(model_display_name)
        self.agent2 = JobHunterAgent(model_display_name)
        self.agent3 = ApplicationHelperAgent(model_display_name)
        self.memory = AgentMemory()

        # ── Step 4: Build preferences ─────────────────────────
        skills_list = [s.strip() for s in skills_input.split(",") if s.strip()] if skills_input else []

        self.memory.preferences = UserPreferences(
            location=city,
            target_role=occupation,
            key_skills=skills_list,
            experience_level=experience,
            job_type=job_type,
            work_mode=work_mode,
            education_level=education,
            salary_range=salary_range,
            date_posted=date_posted,
        )

        # ── Step 5: Parse CV into CVProfile ─────────────────
        try:
            cv_profile = parse_cv_to_profile(cv_file)
            self.memory.cv_profile = cv_profile
        except ValueError as e:
            return _status_error(), f"## ❌ CV Parsing Error\n\n{str(e)}", "", "", ""
        except Exception as e:
            return _status_error(), f"## ❌ Unexpected Error\n\nFailed to parse CV: {str(e)}", "", "", ""

        # ── Step 6: Run Agent 1 (CV Ingestor) ──────────────
        self.memory = self.agent1.safe_execute(self.memory)
        self.memory.agent1_time = self.agent1.elapsed_time

        if not self.memory.is_healthy():
            return (
                _status_partial(1, self.memory),
                f"## Agent 1 Error\n\n{'; '.join(self.memory.errors)}",
                "", _format_cv_analysis(self.memory.cv_profile), ""
            )

        # ── Step 7: Run Agent 2 (Job Hunter) ───────────────
        self.memory = self.agent2.safe_execute(self.memory)
        self.memory.agent2_time = self.agent2.elapsed_time

        # ── Step 8: Run Agent 3 (Application Helper) ───────
        if self.memory.job_results:
            self.memory = self.agent3.safe_execute(self.memory)
            self.memory.agent3_time = self.agent3.elapsed_time

        # ── Step 9: Format all results ─────────────────────
        self.memory.pipeline_status = PipelineStatus.COMPLETED
        total_time = time.time() - pipeline_start

        status_md = _format_agent_status(self.memory, total_time)
        jobs_md = _format_jobs(self.memory)
        autofill_md = _format_autofill(self.memory)
        cv_md = _format_cv_analysis(self.memory.cv_profile)
        ai_md = _format_ai_insights(self.memory)

        return status_md, jobs_md, autofill_md, cv_md, ai_md


# ═══════════════════════════════════════════════
# Result Formatters
# ═══════════════════════════════════════════════

def _status_error():
    return "⬜ Agent 1 &nbsp; ⬜ Agent 2 &nbsp; ⬜ Agent 3"


def _status_partial(failed_at, memory):
    icons = ["❌", "⬜", "⬜"]
    if failed_at > 1:
        icons[0] = "✅"
    return f"{icons[0]} CV Ingestor &nbsp; {icons[1]} Job Hunter &nbsp; {icons[2]} Apply Helper"


def _format_agent_status(memory: AgentMemory, total_time: float) -> str:
    """Format the agent pipeline status for the dashboard."""
    a1 = f"✅ CV Ingestor ({memory.agent1_time:.1f}s)"
    a2_icon = "✅" if memory.job_results else "⚠️"
    a2 = f"{a2_icon} Job Hunter ({memory.agent2_time:.1f}s)"
    a3_icon = "✅" if memory.applications else "⚠️"
    a3 = f"{a3_icon} Apply Helper ({memory.agent3_time:.1f}s)"

    status = f"{a1} &nbsp;→&nbsp; {a2} &nbsp;→&nbsp; {a3}"
    status += f"\n\n*Total pipeline time: {total_time:.1f}s*"

    if memory.errors:
        status += f"\n\n⚠️ Warnings: {'; '.join(memory.errors[:3])}"

    return status


def _format_jobs(memory: AgentMemory) -> str:
    """Format job results with match scores and apply links."""
    jobs = memory.job_results
    if not jobs:
        return (
            "## 🔍 No Jobs Found\n\n"
            "No matching jobs were found. Try:\n"
            "- Broadening your search terms\n"
            "- Removing location filters\n"
            "- Using different keywords\n"
        )

    lines = [f"## 💼 Found {len(jobs)} Matching Jobs\n"]

    # Source info
    sources = set(j.source for j in jobs)
    source_str = ", ".join(sorted(sources))
    lines.append(f"> *Sources: {source_str}*\n")
    lines.append("---\n")

    for i, job in enumerate(jobs, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"**#{i}**")

        # Match score badge
        score = job.match_score
        score_color = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        score_badge = f"{score_color} **{score:.0f}% Match**"

        lines.append(f"### {medal} {job.title}")
        lines.append(f"**{job.company}** | {job.location} | {score_badge}\n")

        if job.salary and job.salary != "Not specified":
            lines.append(f"💰 **Salary:** {job.salary}")

        if job.job_type and job.job_type != "N/A":
            lines.append(f"🏢 **Type:** {job.job_type}")

        if job.posted_date:
            lines.append(f"📅 **Posted:** {job.posted_date}")

        if job.source:
            lines.append(f"🌐 **Source:** {job.source}")

        # Skills
        if job.matching_skills:
            matched = " | ".join([f"✅ `{s}`" for s in job.matching_skills[:5]])
            lines.append(f"\n**Matching Skills:** {matched}")

        if job.missing_skills:
            missing = " | ".join([f"⚠️ `{s}`" for s in job.missing_skills[:5]])
            lines.append(f"**Skills to Develop:** {missing}")

        if job.skills_required and not job.matching_skills:
            skill_tags = " | ".join([f"`{s}`" for s in job.skills_required[:6]])
            lines.append(f"\n**Required Skills:** {skill_tags}")

        # Description preview
        if job.description:
            preview = job.description[:200] + "..." if len(job.description) > 200 else job.description
            lines.append(f"\n{preview}")

        # Apply link
        if job.apply_url and job.apply_url != "#":
            lines.append(f"\n**[🚀 Apply Now →]({job.apply_url})**")

        lines.append("\n---\n")

    return "\n".join(lines)


def _format_autofill(memory: AgentMemory) -> str:
    """Format auto-fill data and application packages."""
    if not memory.applications:
        if memory.cv_profile:
            return _basic_autofill(memory.cv_profile)
        return "*Upload a CV and run the pipeline to see auto-fill data.*"

    lines = ["## 📝 Auto-Fill Application Data\n"]
    lines.append("*Copy and paste these fields into job application forms:*\n")

    # Common auto-fill table (from first application)
    auto_fill = memory.applications[0].auto_fill_data
    if auto_fill:
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        for label, value in auto_fill.items():
            lines.append(f"| **{label}** | {value or '*Not found*'} |")
        lines.append("")

    # Per-job application packages
    lines.append("---\n")
    lines.append("## 🎯 Tailored Application Packages\n")

    for i, app in enumerate(memory.applications, 1):
        job = app.job
        lines.append(f"### {i}. {job.title} at {job.company}\n")

        if app.apply_url and app.apply_url != "#":
            lines.append(f"**[🚀 Apply Now →]({app.apply_url})**\n")

        if app.cover_letter_snippet:
            lines.append("**📧 Cover Letter Opening:**")
            lines.append(f"> {app.cover_letter_snippet}\n")

        if app.application_tips:
            lines.append("**💡 Application Tips:**")
            for tip in app.application_tips:
                lines.append(f"- {tip}")
            lines.append("")

        lines.append("---\n")

    return "\n".join(lines)


def _basic_autofill(cv_profile: CVProfile) -> str:
    """Basic auto-fill when only Agent 1 ran."""
    lines = ["## 📝 Auto-Fill Data\n"]
    contact = cv_profile.contact

    fields = [
        ("Full Name", contact.name),
        ("Email", contact.email),
        ("Phone", contact.phone),
        ("LinkedIn", contact.linkedin),
        ("Skills", ", ".join(cv_profile.skills[:10]) if cv_profile.skills else ""),
    ]

    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    for label, value in fields:
        lines.append(f"| **{label}** | {value or '*Not detected*'} |")

    return "\n".join(lines)


def _format_cv_analysis(cv_profile) -> str:
    """Format CV analysis results."""
    if not cv_profile:
        return "*Upload a CV to see analysis results.*"

    lines = ["## 📄 CV Analysis Summary\n"]

    contact = cv_profile.contact
    if contact.name or contact.email:
        lines.append("### 👤 Contact Information")
        if contact.name:
            lines.append(f"- **Name:** {contact.name}")
        if contact.email:
            lines.append(f"- **Email:** {contact.email}")
        if contact.phone:
            lines.append(f"- **Phone:** {contact.phone}")
        if contact.linkedin:
            lines.append(f"- **LinkedIn:** {contact.linkedin}")
        lines.append("")

    if cv_profile.experience_level.value != "Unknown":
        lines.append(f"### 📊 Experience: {cv_profile.experience_level.value}")
        if cv_profile.experience_years > 0:
            lines.append(f"- **Years:** {cv_profile.experience_years}")
        lines.append("")

    if cv_profile.skills:
        lines.append("### 🔧 Detected Skills")
        skill_tags = " | ".join([f"`{s}`" for s in cv_profile.skills[:20]])
        lines.append(skill_tags)
        lines.append("")

    sections = cv_profile.sections
    if sections.get("summary"):
        lines.append("### 📋 Professional Summary")
        lines.append(sections["summary"][:500])
        lines.append("")

    if sections.get("experience"):
        lines.append("### 💼 Experience")
        lines.append(sections["experience"][:800])
        lines.append("")

    if sections.get("education"):
        lines.append("### 🎓 Education")
        lines.append(sections["education"][:400])
        lines.append("")

    if sections.get("certifications"):
        lines.append("### 🏆 Certifications")
        lines.append(sections["certifications"][:300])
        lines.append("")

    return "\n".join(lines)


def _format_ai_insights(memory: AgentMemory) -> str:
    """Format AI-powered insights from all agents."""
    lines = ["## 🤖 AI Insights\n"]

    # LLM analysis from Agent 1
    if memory.cv_profile and memory.cv_profile.sections.get("llm_analysis"):
        lines.append("### Agent 1 — CV Analysis")
        lines.append(memory.cv_profile.sections["llm_analysis"][:1500])
        lines.append("")

    # Agent timing summary
    lines.append("### ⏱️ Pipeline Performance")
    lines.append(f"- **Agent 1** (CV Ingestor): {memory.agent1_time:.1f}s")
    lines.append(f"- **Agent 2** (Job Hunter): {memory.agent2_time:.1f}s")
    lines.append(f"- **Agent 3** (Apply Helper): {memory.agent3_time:.1f}s")
    total = memory.agent1_time + memory.agent2_time + memory.agent3_time
    lines.append(f"- **Total Agent Time**: {total:.1f}s")
    lines.append("")

    # Job source stats
    if memory.job_results:
        lines.append("### 🌐 Search Sources")
        source_counts: dict[str, int] = {}
        for job in memory.job_results:
            source_counts[job.source] = source_counts.get(job.source, 0) + 1
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- **{source}**: {count} jobs")
        lines.append("")

    # Errors/warnings
    if memory.errors:
        lines.append("### ⚠️ Warnings")
        for error in memory.errors[:5]:
            lines.append(f"- {error}")

    return "\n".join(lines)
