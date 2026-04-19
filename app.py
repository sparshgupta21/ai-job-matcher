"""
AI Job Matcher v2.0 — Main Gradio Application
Multi-agent AI job matching powered by open-source LLMs from Hugging Face.
"""

import gradio as gr
import os

from config import (
    MODEL_CHOICES, EXPERIENCE_LEVELS, JOB_TYPES, WORK_MODES,
    EDUCATION_LEVELS, SALARY_RANGES, DATE_POSTED_OPTIONS, APP_VERSION,
)
from agents.orchestrator import AgentOrchestrator
from utils import setup_logging

setup_logging()

# ─────────────────────────────────────────────
# Custom CSS — Premium dark glassmorphism theme
# ─────────────────────────────────────────────

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ──────────────────────────────── */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    max-width: 1100px !important;
    margin: 0 auto !important;
}

/* ── Header Banner ───────────────────────── */
#app-header {
    text-align: center;
    padding: 2.5rem 1.5rem;
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 40%, #24243e 100%);
    border-radius: 18px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(139, 92, 246, 0.3);
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.05);
    position: relative;
    overflow: hidden;
}
#app-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: conic-gradient(
        from 0deg,
        transparent 0deg 340deg,
        rgba(139, 92, 246, 0.08) 340deg 360deg
    );
    animation: headerGlow 8s linear infinite;
    pointer-events: none;
}
@keyframes headerGlow {
    to { transform: rotate(360deg); }
}
#app-header::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.15) 0%, transparent 70%);
    pointer-events: none;
}
#app-header h1 {
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    color: #e0e7ff !important;
    margin: 0 0 0.4rem 0 !important;
    position: relative; z-index: 1;
    letter-spacing: -0.5px;
}
#app-header p {
    color: #94a3b8 !important;
    font-size: 1rem !important;
    margin: 0.2rem 0 0 0 !important;
    position: relative; z-index: 1;
}
#app-header .subtitle {
    font-size: 0.85rem !important;
    color: #64748b !important;
    margin-top: 0.6rem !important;
}
#app-header .version-badge {
    display: inline-block;
    background: rgba(139, 92, 246, 0.25);
    color: #c4b5fd;
    font-size: 0.7rem;
    padding: 2px 10px;
    border-radius: 12px;
    margin-left: 8px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* ── Agent Pipeline Status ───────────────── */
#agent-status {
    text-align: center;
    padding: 1rem;
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 14px;
    margin-bottom: 1rem;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
}
#agent-status .prose {
    text-align: center !important;
}

/* ── Section headers ─────────────────────── */
.section-title {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #c7d2fe !important;
    padding: 0.6rem 0 !important;
    margin: 0.8rem 0 0.2rem 0 !important;
    border-bottom: 2px solid rgba(139, 92, 246, 0.3) !important;
    display: block;
}

/* ── Inputs override ─────────────────────── */
.gradio-container input[type="text"],
.gradio-container textarea,
.gradio-container .wrap input {
    background: #1e1b4b !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(139, 92, 246, 0.35) !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}
.gradio-container input[type="text"]:focus,
.gradio-container textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.2) !important;
}
.gradio-container input[type="text"]::placeholder,
.gradio-container textarea::placeholder {
    color: #6b7280 !important;
}

/* ── Dropdown / select ───────────────────── */
.gradio-container .wrap.svelte-1sk0pyu,
.gradio-container .secondary-wrap {
    background: #1e1b4b !important;
    border: 1px solid rgba(139, 92, 246, 0.35) !important;
    border-radius: 10px !important;
}
.gradio-container .wrap.svelte-1sk0pyu input,
.gradio-container .secondary-wrap input {
    color: #e2e8f0 !important;
}

/* ── Labels ──────────────────────────────── */
.gradio-container label,
.gradio-container .label-wrap span,
.gradio-container span.svelte-1gfkn6j {
    color: #c7d2fe !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}
.gradio-container .info {
    color: #94a3b8 !important;
}

/* ── Block containers ────────────────────── */
.gradio-container .block {
    background: #0f172a !important;
    border: 1px solid rgba(139, 92, 246, 0.15) !important;
    border-radius: 12px !important;
}

/* ── File upload ─────────────────────────── */
.gradio-container .upload-text {
    color: #94a3b8 !important;
}
.gradio-container .upload-text span {
    color: #94a3b8 !important;
}

/* ── Primary button ──────────────────────── */
#search-btn {
    background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 50%, #a78bfa 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 16px 40px !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    cursor: pointer !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 6px 24px rgba(139, 92, 246, 0.45) !important;
    min-height: 58px !important;
    letter-spacing: 0.5px;
    position: relative;
    overflow: hidden;
}
#search-btn::before {
    content: '';
    position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    transition: left 0.5s;
}
#search-btn:hover::before {
    left: 100%;
}
#search-btn:hover {
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 10px 36px rgba(139, 92, 246, 0.6) !important;
}
#search-btn:active {
    transform: translateY(0) scale(0.99) !important;
}

/* ── Tabs ────────────────────────────────── */
.gradio-container .tab-nav {
    border-bottom: 2px solid rgba(139, 92, 246, 0.2) !important;
}
.gradio-container .tab-nav button {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 10px 18px !important;
    color: #94a3b8 !important;
    transition: all 0.3s ease !important;
    border: none !important;
    background: transparent !important;
}
.gradio-container .tab-nav button.selected {
    background: linear-gradient(135deg, #7c3aed, #8b5cf6) !important;
    color: #ffffff !important;
    border-radius: 8px 8px 0 0 !important;
}

/* ── Markdown results ────────────────────── */
.gradio-container .prose,
.gradio-container .markdown-text,
.gradio-container .md {
    color: #cbd5e1 !important;
}
.gradio-container .prose h2,
.gradio-container .markdown-text h2 {
    color: #e0e7ff !important;
    border-bottom: 1px solid rgba(139, 92, 246, 0.25) !important;
    padding-bottom: 0.4rem !important;
}
.gradio-container .prose h3,
.gradio-container .markdown-text h3 {
    color: #c7d2fe !important;
}
.gradio-container .prose a,
.gradio-container .markdown-text a {
    color: #a78bfa !important;
    font-weight: 600 !important;
    transition: color 0.2s !important;
}
.gradio-container .prose a:hover,
.gradio-container .markdown-text a:hover {
    color: #c4b5fd !important;
}
.gradio-container .prose code,
.gradio-container .markdown-text code {
    background: rgba(139, 92, 246, 0.15) !important;
    color: #c4b5fd !important;
    padding: 2px 7px !important;
    border-radius: 5px !important;
}
.gradio-container .prose table th,
.gradio-container .markdown-text table th {
    background: rgba(139, 92, 246, 0.2) !important;
    padding: 10px !important;
}
.gradio-container .prose table td,
.gradio-container .markdown-text table td {
    padding: 8px 10px !important;
    border-bottom: 1px solid rgba(139, 92, 246, 0.1) !important;
}

/* ── Accordion ───────────────────────────── */
.gradio-container .accordion {
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
    border-radius: 12px !important;
}

/* ── Footer ──────────────────────────────── */
#app-footer {
    text-align: center;
    padding: 1.2rem;
    margin-top: 1.5rem;
}
#app-footer p {
    color: #64748b !important;
    font-size: 0.82rem !important;
    margin: 0.25rem 0 !important;
}
#app-footer a {
    color: #a78bfa !important;
    text-decoration: none !important;
    font-weight: 600 !important;
}
#app-footer a:hover { color: #c4b5fd !important; }

/* ── Responsive ──────────────────────────── */
@media (max-width: 768px) {
    #app-header h1 { font-size: 1.5rem !important; }
    #search-btn { width: 100% !important; }
}

/* ── Smooth scrolling + loading ──────────── */
html { scroll-behavior: smooth; }
.generating { border-color: #8b5cf6 !important; }
"""

# ─────────────────────────────────────────────
# Pipeline entry point (called by Gradio button)
# ─────────────────────────────────────────────

def run_pipeline_wrapper(
    cv_file, model_display_name, city, occupation,
    experience, job_type, work_mode, education,
    salary_range, skills_input, date_posted,
    hf_token_input, tavily_key_input,
):
    """Wrapper around the agent orchestrator for Gradio."""
    orchestrator = AgentOrchestrator(model_display_name)
    return orchestrator.run_pipeline(
        cv_file=cv_file,
        model_display_name=model_display_name,
        city=city,
        occupation=occupation,
        experience=experience,
        job_type=job_type,
        work_mode=work_mode,
        education=education,
        salary_range=salary_range,
        skills_input=skills_input,
        date_posted=date_posted,
        hf_token_input=hf_token_input,
        tavily_key_input=tavily_key_input,
    )


# ─────────────────────────────────────────────
# Build the Gradio Interface
# ─────────────────────────────────────────────

def create_app():
    """Create and return the Gradio Blocks app."""

    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.violet,
        secondary_hue=gr.themes.colors.purple,
        neutral_hue=gr.themes.colors.slate,
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        # Force dark palette everywhere
        body_background_fill="#0b0f1a",
        body_background_fill_dark="#0b0f1a",
        body_text_color="#e2e8f0",
        body_text_color_dark="#e2e8f0",
        body_text_color_subdued="#94a3b8",
        body_text_color_subdued_dark="#94a3b8",
        block_background_fill="#111827",
        block_background_fill_dark="#111827",
        block_border_color="rgba(139,92,246,0.15)",
        block_border_color_dark="rgba(139,92,246,0.15)",
        block_label_text_color="#c7d2fe",
        block_label_text_color_dark="#c7d2fe",
        block_title_text_color="#e0e7ff",
        block_title_text_color_dark="#e0e7ff",
        input_background_fill="#1e1b4b",
        input_background_fill_dark="#1e1b4b",
        input_border_color="rgba(139,92,246,0.3)",
        input_border_color_dark="rgba(139,92,246,0.3)",
        input_placeholder_color="#6b7280",
        input_placeholder_color_dark="#6b7280",
        button_primary_background_fill="#7c3aed",
        button_primary_background_fill_dark="#7c3aed",
        button_primary_text_color="#ffffff",
        button_primary_text_color_dark="#ffffff",
        border_color_accent="#8b5cf6",
        border_color_accent_dark="#8b5cf6",
        color_accent_soft="rgba(139,92,246,0.15)",
        color_accent_soft_dark="rgba(139,92,246,0.15)",
        shadow_drop="0 4px 14px rgba(0,0,0,0.25)",
        shadow_drop_lg="0 8px 30px rgba(0,0,0,0.35)",
    )

    with gr.Blocks(
        title="AI Job Matcher v2.0 — Multi-Agent AI Job Search",
        analytics_enabled=False,
    ) as app:

        # ── Header ────────────────────────────────────────────
        gr.HTML(f"""
            <div id="app-header">
                <h1>🎯 AI Job Matcher <span class="version-badge">v{APP_VERSION}</span></h1>
                <p>Multi-Agent AI · Powered by Open-Source LLMs from Hugging Face</p>
                <p class="subtitle">
                    3 AI Agents work together: 📄 CV Ingestor → 🔍 Job Hunter → 📋 Application Helper
                </p>
            </div>
        """)

        # ── API Keys (open by default — users must enter their own) ──
        with gr.Accordion("🔑 API Keys — Enter YOUR Keys to Use AI Features", open=True):
            gr.Markdown(
                "⚠️ **You must enter your own API keys.** Each user's tokens are used "
                "privately for their session only — never stored, never shared. "
                "Get a [free HF token](https://huggingface.co/settings/tokens) and "
                "optionally a [free Tavily key](https://tavily.com) for real job search."
            )
            with gr.Row():
                hf_token_input = gr.Textbox(
                    label="HuggingFace Token",
                    placeholder="hf_xxxxxxxxxxxxxxxxxxxx",
                    type="password",
                    info="Get free at huggingface.co/settings/tokens",
                    elem_id="hf-token-input",
                )
                tavily_key_input = gr.Textbox(
                    label="Tavily Search Key (optional)",
                    placeholder="tvly-xxxxxxxxxx",
                    type="password",
                    info="Get free at tavily.com (1000 searches/month)",
                    elem_id="tavily-key-input",
                )

        # ── Upload & Configure ─────────────────────────────────
        gr.HTML('<span class="section-title">📄 Upload & Configure</span>')

        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                cv_upload = gr.File(
                    label="Upload Your CV / Resume",
                    file_types=[".pdf", ".docx", ".doc"],
                    type="filepath",
                    elem_id="cv-upload",
                )

            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=MODEL_CHOICES,
                    value=MODEL_CHOICES[0],
                    label="🤖 Select AI Model",
                    info="Small, efficient models (no OOM risk on free tier)",
                    elem_id="model-select",
                )
                occupation_input = gr.Textbox(
                    label="💼 Desired Job Title / Role",
                    placeholder="e.g., Software Engineer, Data Scientist, Product Manager",
                    elem_id="occupation-input",
                )

        # ── Search Filters ─────────────────────────────────────
        gr.HTML('<span class="section-title">🔍 Search Filters</span>')

        with gr.Row():
            city_input = gr.Textbox(
                label="📍 City / Location",
                placeholder="e.g., Bangalore, Mumbai, Delhi NCR, Remote",
                elem_id="city-input",
            )
            skills_input = gr.Textbox(
                label="🔧 Key Skills (comma-separated)",
                placeholder="e.g., Python, React, Machine Learning",
                elem_id="skills-input",
            )

        with gr.Row():
            experience_dropdown = gr.Dropdown(
                choices=EXPERIENCE_LEVELS,
                value="Any",
                label="📅 Experience Level",
                elem_id="experience-select",
            )
            job_type_dropdown = gr.Dropdown(
                choices=JOB_TYPES,
                value="Any",
                label="🏢 Job Type",
                elem_id="job-type-select",
            )
            work_mode_dropdown = gr.Dropdown(
                choices=WORK_MODES,
                value="Any",
                label="🏠 Work Mode",
                elem_id="work-mode-select",
            )

        with gr.Row():
            education_dropdown = gr.Dropdown(
                choices=EDUCATION_LEVELS,
                value="Any",
                label="🎓 Education Level",
                elem_id="education-select",
            )
            salary_dropdown = gr.Dropdown(
                choices=SALARY_RANGES,
                value="Any",
                label="💰 Salary Range",
                elem_id="salary-select",
            )
            date_posted_dropdown = gr.Dropdown(
                choices=DATE_POSTED_OPTIONS,
                value="Any time",
                label="📅 Date Posted",
                elem_id="date-posted-select",
            )

        # ── Launch Button ──────────────────────────────────────
        search_btn = gr.Button(
            value="🚀  Launch AI Pipeline",
            variant="primary",
            elem_id="search-btn",
            size="lg",
        )

        # ── Agent Status Panel ────────────────────────────────
        agent_status = gr.Markdown(
            value="⬜ CV Ingestor &nbsp;→&nbsp; ⬜ Job Hunter &nbsp;→&nbsp; ⬜ Apply Helper",
            elem_id="agent-status",
        )

        # ── Results Section ────────────────────────────────────
        gr.HTML('<span class="section-title" style="margin-top: 1.5rem;">📈 Results</span>')

        with gr.Tabs():
            with gr.Tab("💼 Job Matches", id="tab-jobs"):
                jobs_output = gr.Markdown(
                    value="*Upload your CV and click 'Launch AI Pipeline' to see results.*",
                    elem_id="jobs-results",
                )

            with gr.Tab("📝 Auto-Fill & Apply", id="tab-autofill"):
                autofill_output = gr.Markdown(
                    value="*Application data and cover letter snippets will appear here.*",
                    elem_id="autofill-results",
                )

            with gr.Tab("📄 CV Analysis", id="tab-cv"):
                cv_analysis_output = gr.Markdown(
                    value="*CV analysis will appear here after uploading your resume.*",
                    elem_id="cv-analysis-results",
                )

            with gr.Tab("🤖 AI Insights", id="tab-ai"):
                ai_output = gr.Markdown(
                    value="*AI-powered insights and pipeline stats will appear here.*",
                    elem_id="ai-results",
                )

        # ── Wire up the pipeline ───────────────────────────────
        search_btn.click(
            fn=run_pipeline_wrapper,
            inputs=[
                cv_upload,
                model_dropdown,
                city_input,
                occupation_input,
                experience_dropdown,
                job_type_dropdown,
                work_mode_dropdown,
                education_dropdown,
                salary_dropdown,
                skills_input,
                date_posted_dropdown,
                hf_token_input,
                tavily_key_input,
            ],
            outputs=[
                agent_status,
                jobs_output,
                autofill_output,
                cv_analysis_output,
                ai_output,
            ],
            show_progress="full",
        )

        # ── Footer ─────────────────────────────────────────────
        gr.HTML(f"""
            <div id="app-footer">
                <p>
                    AI Job Matcher v{APP_VERSION} &bull;
                    Powered by open-source LLMs on
                    <a href="https://huggingface.co" target="_blank">Hugging Face</a> &bull;
                    <a href="https://github.com/sparshgupta21/ai-job-matcher" target="_blank">GitHub</a>
                </p>
                <p>
                    Your CV is processed in-memory only and never stored. &bull;
                    Protected by multi-layer guardrails against prompt injection. &bull;
                    India-first job portal targeting 🇮🇳
                </p>
            </div>
        """)

    return app, theme, CUSTOM_CSS


# ─────────────────────────────────────────────
# Launch
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app, theme, css = create_app()

    # Detect environment and launch accordingly
    from utils import is_running_on_spaces, is_running_on_colab

    if is_running_on_spaces():
        app.launch(theme=theme, css=css)
    elif is_running_on_colab():
        app.launch(share=True, theme=theme, css=css)
    else:
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            theme=theme,
            css=css,
        )
