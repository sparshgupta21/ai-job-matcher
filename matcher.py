"""
AI Job Matcher - Job Matching and Ranking Engine
Coordinates CV parsing, job search, and LLM analysis.
"""

import logging
from config import MODEL_MAP

logger = logging.getLogger(__name__)


def build_search_query(cv_data, occupation="", skills_input=""):
    """Build an effective job search query from CV data and user inputs."""
    parts = []

    # Use explicit occupation if provided
    if occupation and occupation.strip():
        parts.append(occupation.strip())
    else:
        # Try to infer from CV sections
        if cv_data.get("sections", {}).get("experience"):
            exp_text = cv_data["sections"]["experience"]
            # Extract first job title-like line
            lines = exp_text.split("\n")
            for line in lines[:3]:
                line = line.strip()
                if line and len(line) < 60 and not any(c.isdigit() for c in line[:4]):
                    parts.append(line)
                    break

    # Add skills
    if skills_input and skills_input.strip():
        parts.append(skills_input.strip())
    elif cv_data.get("skills"):
        # Use top 3 skills
        top_skills = cv_data["skills"][:3]
        parts.append(", ".join(top_skills))

    if not parts:
        parts.append("software developer")  # sensible default

    return " ".join(parts[:3])  # Keep query concise


def format_jobs_as_markdown(jobs, source="", warning=""):
    """Format job results as rich Markdown for Gradio display."""
    if not jobs:
        return (
            "## No Jobs Found\n\n"
            "No matching jobs were found. Try:\n"
            "- Broadening your search terms\n"
            "- Removing location filters\n"
            "- Using different keywords\n"
        )

    lines = []

    # Header
    lines.append(f"## Found {len(jobs)} Matching Jobs\n")

    if warning:
        lines.append(f"> **Note:** {warning}\n")

    if source == "demo":
        lines.append("> *Showing demo data. Configure a job API key for real listings.*\n")

    lines.append("---\n")

    # Job cards
    for i, job in enumerate(jobs, 1):
        medal = {1: "gold", 2: "silver", 3: "bronze"}.get(i, "")
        medal_emoji = {1: "\U0001f947", 2: "\U0001f948", 3: "\U0001f949"}.get(i, f"**#{i}**")

        lines.append(f"### {medal_emoji} {job.get('title', 'N/A')}")
        lines.append(f"**{job.get('company', 'N/A')}** | {job.get('location', 'N/A')}\n")

        if job.get("salary") and job["salary"] != "Not specified":
            lines.append(f"**Salary:** {job['salary']}")

        if job.get("job_type"):
            lines.append(f"**Type:** {job['job_type']}")

        if job.get("date_posted"):
            lines.append(f"**Posted:** {job['date_posted']}")

        # Skills
        skills = job.get("skills_required", [])
        if skills:
            skill_tags = " | ".join([f"`{s}`" for s in skills[:6]])
            lines.append(f"\n**Skills:** {skill_tags}")

        # Description preview
        desc = job.get("description", "")
        if desc:
            preview = desc[:200] + "..." if len(desc) > 200 else desc
            lines.append(f"\n{preview}")

        # Apply link
        apply_url = job.get("apply_url", "#")
        if apply_url and apply_url != "#":
            lines.append(f"\n**[Apply Now \u2192]({apply_url})**")

        lines.append("\n---\n")

    return "\n".join(lines)


def format_cv_analysis(cv_data):
    """Format extracted CV data as readable Markdown."""
    lines = ["## CV Analysis Summary\n"]

    contact = cv_data.get("contact", {})
    if any(contact.values()):
        lines.append("### Contact Information")
        if contact.get("name"):
            lines.append(f"- **Name:** {contact['name']}")
        if contact.get("email"):
            lines.append(f"- **Email:** {contact['email']}")
        if contact.get("phone"):
            lines.append(f"- **Phone:** {contact['phone']}")
        if contact.get("linkedin"):
            lines.append(f"- **LinkedIn:** {contact['linkedin']}")
        lines.append("")

    skills = cv_data.get("skills", [])
    if skills:
        lines.append("### Detected Skills")
        skill_tags = " | ".join([f"`{s}`" for s in skills])
        lines.append(skill_tags)
        lines.append("")

    sections = cv_data.get("sections", {})

    if sections.get("summary"):
        lines.append("### Professional Summary")
        lines.append(sections["summary"][:500])
        lines.append("")

    if sections.get("experience"):
        lines.append("### Experience")
        lines.append(sections["experience"][:800])
        lines.append("")

    if sections.get("education"):
        lines.append("### Education")
        lines.append(sections["education"][:400])
        lines.append("")

    if sections.get("certifications"):
        lines.append("### Certifications")
        lines.append(sections["certifications"][:300])
        lines.append("")

    return "\n".join(lines)


def format_autofill_data(cv_data, llm_autofill=""):
    """Format auto-fill data for easy copy-paste."""
    lines = ["## Auto-Fill Data\n"]
    lines.append("*Copy and paste these fields into job application forms:*\n")

    contact = cv_data.get("contact", {})

    fields = [
        ("Full Name", contact.get("name", "")),
        ("Email", contact.get("email", "")),
        ("Phone", contact.get("phone", "")),
        ("LinkedIn", contact.get("linkedin", "")),
    ]

    skills = cv_data.get("skills", [])
    if skills:
        fields.append(("Skills (comma-separated)", ", ".join(skills)))

    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    for label, value in fields:
        lines.append(f"| **{label}** | {value or '*Not detected*'} |")
    lines.append("")

    if llm_autofill:
        lines.append("### AI-Enhanced Profile\n")
        lines.append(llm_autofill)

    return "\n".join(lines)


def run_job_matching_pipeline(
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
):
    """
    Main pipeline: parse CV -> search jobs -> LLM analysis -> formatted results.
    Returns (job_results_md, autofill_md, cv_analysis_md, llm_analysis_md)
    """
    import os
    from guardrails import (
        rate_limiter, validate_file_upload, validate_user_inputs,
        sanitize_text, check_prompt_injection,
    )
    from cv_parser import parse_cv
    from job_search import search_jobs
    from llm_engine import (
        analyze_cv_with_llm, match_jobs_with_llm,
        generate_autofill, generate_cover_letter,
    )

    # ── Step 0: Set HF token if provided via UI ────────────────────
    if hf_token_input and hf_token_input.strip():
        os.environ["HF_TOKEN"] = hf_token_input.strip()

    # ── Step 1: Rate limiting ──────────────────────────────────────
    if not rate_limiter.is_allowed():
        remaining_msg = (
            "## Rate Limit Reached\n\n"
            "You've exceeded the maximum number of requests per hour. "
            "Please wait a while and try again.\n\n"
            f"*Remaining requests: {rate_limiter.remaining()}*"
        )
        return remaining_msg, "", "", ""

    # ── Step 2: Validate inputs ────────────────────────────────────
    if not cv_file:
        return "## Please Upload Your CV\n\nUpload a PDF or DOCX file to get started.", "", "", ""

    is_valid, error = validate_file_upload(cv_file)
    if not is_valid:
        return f"## File Error\n\n{error}", "", "", ""

    city = sanitize_text(city or "")
    occupation = sanitize_text(occupation or "")
    skills_input = sanitize_text(skills_input or "")

    is_valid, error = validate_user_inputs(city, occupation, skills_input)
    if not is_valid:
        return f"## Security Alert\n\n{error}", "", "", ""

    # ── Step 3: Parse CV ───────────────────────────────────────────
    try:
        cv_data = parse_cv(cv_file)
    except ValueError as e:
        return f"## CV Parsing Error\n\n{str(e)}", "", "", ""
    except Exception as e:
        return f"## Unexpected Error\n\nFailed to parse CV: {str(e)}", "", "", ""

    # ── Step 4: Build search query ─────────────────────────────────
    search_query = build_search_query(cv_data, occupation, skills_input)
    location = city if city else ""

    # ── Step 5: Search for jobs ────────────────────────────────────
    jobs, source, warning = search_jobs(
        query=search_query,
        location=location,
        job_type=job_type if job_type != "Any" else "Any",
        experience=experience if experience != "Any" else "Any",
        num_results=10,
        date_posted=date_posted if date_posted != "Any time" else "Any time",
    )

    # ── Step 6: Format basic results ───────────────────────────────
    jobs_md = format_jobs_as_markdown(jobs, source, warning)
    cv_analysis_md = format_cv_analysis(cv_data)

    # ── Step 7: LLM-powered analysis ──────────────────────────────
    model_id = MODEL_MAP.get(model_display_name, "HuggingFaceTB/SmolLM2-1.7B-Instruct")

    # LLM CV Analysis
    llm_analysis_md = ""
    try:
        llm_analysis_md = analyze_cv_with_llm(model_id, cv_data.get("raw_text", ""))
    except Exception as e:
        llm_analysis_md = f"*AI analysis unavailable: {str(e)}*"

    # LLM Job Matching
    if jobs:
        try:
            llm_match = match_jobs_with_llm(model_id, cv_data.get("raw_text", ""), jobs)
            jobs_md += f"\n\n## AI Match Analysis\n\n{llm_match}"
        except Exception as e:
            jobs_md += f"\n\n*AI matching unavailable: {str(e)}*"

    # LLM Auto-fill
    autofill_md = ""
    try:
        llm_autofill = generate_autofill(model_id, cv_data.get("raw_text", ""))
        autofill_md = format_autofill_data(cv_data, llm_autofill)
    except Exception as e:
        autofill_md = format_autofill_data(cv_data, f"*AI auto-fill unavailable: {str(e)}*")

    return jobs_md, autofill_md, cv_analysis_md, llm_analysis_md
