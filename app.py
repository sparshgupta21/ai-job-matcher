"""
AI Job Matcher - Main Gradio Application
AI-powered job matching using open-source LLMs from Hugging Face.
"""

import gradio as gr
import os

from config import (
    MODEL_CHOICES, EXPERIENCE_LEVELS, JOB_TYPES, WORK_MODES,
    EDUCATION_LEVELS, SALARY_RANGES, DATE_POSTED_OPTIONS,
)
from matcher import run_job_matching_pipeline
from utils import setup_logging, get_app_version

setup_logging()

# ─────────────────────────────────────────────
# Custom CSS for Premium Dark Theme
# ─────────────────────────────────────────────

CUSTOM_CSS = """
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Root Theme Overrides */
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --accent-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    --card-bg: rgba(30, 32, 48, 0.8);
    --card-border: rgba(102, 126, 234, 0.2);
    --glow-color: rgba(102, 126, 234, 0.3);
}

/* Global Styles */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* Header Banner */
#app-header {
    text-align: center;
    padding: 2rem 1rem;
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    border-radius: 16px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(102, 126, 234, 0.3);
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
    position: relative;
    overflow: hidden;
}

#app-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 60%);
    animation: pulse-glow 4s ease-in-out infinite;
}

@keyframes pulse-glow {
    0%, 100% { opacity: 0.5; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.05); }
}

#app-header h1 {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.5rem 0 !important;
    position: relative;
    z-index: 1;
}

#app-header p {
    color: #a0a8c8 !important;
    font-size: 1rem !important;
    margin: 0 !important;
    position: relative;
    z-index: 1;
}

/* Section headers */
.section-header {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #b8c0e0 !important;
    margin-bottom: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 2px solid rgba(102, 126, 234, 0.3) !important;
}

/* Input styling */
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    border-radius: 10px !important;
    border: 1px solid rgba(102, 126, 234, 0.3) !important;
    transition: all 0.3s ease !important;
}

.gradio-container input:focus,
.gradio-container textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
}

/* File upload area */
.gradio-container .upload-area {
    border: 2px dashed rgba(102, 126, 234, 0.4) !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}

.gradio-container .upload-area:hover {
    border-color: #667eea !important;
    background: rgba(102, 126, 234, 0.05) !important;
}

/* Primary button */
#search-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 32px !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: white !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    text-transform: none !important;
    min-height: 52px !important;
}

#search-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5) !important;
}

#search-btn:active {
    transform: translateY(0) !important;
}

/* Tab styling */
.gradio-container .tabs {
    border-radius: 12px !important;
    overflow: hidden !important;
}

.gradio-container .tab-nav button {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 10px 20px !important;
    transition: all 0.3s ease !important;
}

.gradio-container .tab-nav button.selected {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
}

/* Results markdown styling */
.gradio-container .markdown-text h2 {
    color: #c0c8e8 !important;
    border-bottom: 2px solid rgba(102, 126, 234, 0.3) !important;
    padding-bottom: 0.5rem !important;
}

.gradio-container .markdown-text h3 {
    color: #b0b8d8 !important;
}

.gradio-container .markdown-text code {
    background: rgba(102, 126, 234, 0.15) !important;
    color: #a8b4ff !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
    font-size: 0.85em !important;
}

.gradio-container .markdown-text a {
    color: #667eea !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    transition: color 0.3s ease !important;
}

.gradio-container .markdown-text a:hover {
    color: #f093fb !important;
}

.gradio-container .markdown-text table {
    border-collapse: collapse !important;
    width: 100% !important;
    margin: 1rem 0 !important;
}

.gradio-container .markdown-text th {
    background: rgba(102, 126, 234, 0.2) !important;
    padding: 10px !important;
    text-align: left !important;
}

.gradio-container .markdown-text td {
    padding: 8px 10px !important;
    border-bottom: 1px solid rgba(102, 126, 234, 0.1) !important;
}

/* Accordion styling */
.gradio-container .accordion {
    border: 1px solid rgba(102, 126, 234, 0.2) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
}

/* Info badges */
.info-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 2px;
}

.badge-api { background: rgba(79, 172, 254, 0.2); color: #4facfe; }
.badge-demo { background: rgba(240, 147, 251, 0.2); color: #f093fb; }

/* Footer */
#app-footer {
    text-align: center;
    padding: 1rem;
    color: #606880;
    font-size: 0.85rem;
    margin-top: 1rem;
}

/* Responsive */
@media (max-width: 768px) {
    #app-header h1 { font-size: 1.6rem !important; }
    #search-btn { width: 100% !important; }
}

/* Smooth scrolling */
html { scroll-behavior: smooth; }

/* Loading animation */
.generating {
    border-color: #667eea !important;
}
"""

# ─────────────────────────────────────────────
# Build the Gradio Interface
# ─────────────────────────────────────────────

def create_app():
    """Create and return the Gradio Blocks app."""

    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="purple",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
        block_background_fill="*neutral_900",
        block_background_fill_dark="*neutral_900",
        block_border_color="*neutral_800",
        block_border_color_dark="*neutral_800",
        block_label_text_color="*neutral_300",
        block_label_text_color_dark="*neutral_300",
        input_background_fill="*neutral_800",
        input_background_fill_dark="*neutral_800",
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_dark="*primary_600",
    )

    with gr.Blocks(
        theme=theme,
        css=CUSTOM_CSS,
        title="AI Job Matcher - Smart Job Search with Open Source LLMs",
        analytics_enabled=False,
    ) as app:

        # ── Header ────────────────────────────────────────────
        gr.HTML("""
            <div id="app-header">
                <h1>&#127919; AI Job Matcher</h1>
                <p>Smart job matching powered by open-source LLMs from Hugging Face</p>
                <p style="font-size: 0.85rem; margin-top: 8px !important; color: #808aaa !important;">
                    Upload your CV &bull; Select an AI model &bull; Find your perfect job match
                </p>
            </div>
        """)

        # ── HF Token (collapsible) ────────────────────────────
        with gr.Accordion("🔑 HuggingFace Token (Required for AI features)", open=False):
            gr.Markdown(
                "Enter your free HuggingFace API token to enable AI-powered analysis. "
                "Get one at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). "
                "Or set the `HF_TOKEN` environment variable."
            )
            hf_token_input = gr.Textbox(
                label="HF Token",
                placeholder="hf_xxxxxxxxxxxxxxxxxxxx",
                type="password",
                elem_id="hf-token-input",
            )

        # ── Main Input Section ─────────────────────────────────
        gr.HTML('<p class="section-header">📄 Upload & Configure</p>')

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
                    info="Small, efficient open-source models (no OOM risk)",
                    elem_id="model-select",
                )
                occupation_input = gr.Textbox(
                    label="💼 Desired Occupation / Job Title",
                    placeholder="e.g., Software Engineer, Data Scientist, Product Manager",
                    elem_id="occupation-input",
                )

        # ── Search Filters ─────────────────────────────────────
        gr.HTML('<p class="section-header">🔍 Search Filters</p>')

        with gr.Row():
            city_input = gr.Textbox(
                label="📍 City / Location",
                placeholder="e.g., San Francisco, London, Remote",
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

        # ── Search Button ──────────────────────────────────────
        search_btn = gr.Button(
            value="🔍  Find Matching Jobs",
            variant="primary",
            elem_id="search-btn",
            size="lg",
        )

        # ── Results Section ────────────────────────────────────
        gr.HTML('<p class="section-header" style="margin-top: 1.5rem;">📈 Results</p>')

        with gr.Tabs():
            with gr.Tab("💼 Job Matches", id="tab-jobs"):
                jobs_output = gr.Markdown(
                    value="*Upload your CV and click 'Find Matching Jobs' to see results.*",
                    elem_id="jobs-results",
                )

            with gr.Tab("📝 Auto-Fill Data", id="tab-autofill"):
                autofill_output = gr.Markdown(
                    value="*Auto-fill data will appear here after analyzing your CV.*",
                    elem_id="autofill-results",
                )

            with gr.Tab("📄 CV Analysis", id="tab-cv"):
                cv_analysis_output = gr.Markdown(
                    value="*CV analysis will appear here after uploading your resume.*",
                    elem_id="cv-analysis-results",
                )

            with gr.Tab("🤖 AI Insights", id="tab-ai"):
                ai_output = gr.Markdown(
                    value="*AI-powered insights will appear here (requires HF token).*",
                    elem_id="ai-results",
                )

        # ── Wire up the search button ──────────────────────────
        search_btn.click(
            fn=run_job_matching_pipeline,
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
            ],
            outputs=[
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
                    AI Job Matcher v{get_app_version()} &bull;
                    Powered by open-source LLMs on
                    <a href="https://huggingface.co" target="_blank" style="color: #667eea;">Hugging Face</a> &bull;
                    <a href="https://github.com" target="_blank" style="color: #667eea;">GitHub</a>
                </p>
                <p style="font-size: 0.75rem; color: #505868; margin-top: 4px;">
                    Your CV is processed in-memory only and never stored. &bull;
                    Protected by multi-layer guardrails against prompt injection.
                </p>
            </div>
        """)

    return app


# ─────────────────────────────────────────────
# Launch
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()

    # Detect environment and launch accordingly
    from utils import is_running_on_spaces, is_running_on_colab

    if is_running_on_spaces():
        app.launch()
    elif is_running_on_colab():
        app.launch(share=True)
    else:
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
        )
