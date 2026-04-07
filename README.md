---
title: AI Job Matcher
emoji: 🎯
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "5.0"
app_file: app.py
pinned: false
license: mit
short_description: AI-powered job matching using open-source LLMs
---

# AI Job Matcher

> **Smart job matching powered by open-source LLMs from Hugging Face**

Upload your CV, select an AI model, and instantly find matching jobs with AI-powered analysis, auto-fill data, and tailored recommendations — all running on free, open-source language models.

[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-lg-dark.svg)](https://huggingface.co/spaces/sparshgupta21/ai-job-matcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sparshgupta21/ai-job-matcher/blob/main/colab_notebook.ipynb)

---

## Features

| Feature | Description |
|---------|-------------|
| **CV Parsing** | Upload PDF or DOCX resumes with automatic skill and section extraction |
| **LLM Selection** | Choose from 6+ small, efficient open-source models (1B-3.8B params) |
| **Job Search** | Real-time job listings via JSearch/Adzuna APIs + demo mode |
| **AI Matching** | LLM-powered job-to-CV matching with relevance scoring |
| **Auto-Fill** | Extract application data (name, email, skills) ready to copy-paste |
| **Cover Letters** | AI-generated tailored cover letters per job |
| **Security** | Multi-layer guardrails against prompt injection and jailbreaking |
| **Privacy** | CVs processed in-memory only — never stored on disk |

## Available AI Models

| Model | Size | Best For |
|-------|------|----------|
| SmolLM2 1.7B | 1.7B | Fast, lightweight analysis |
| Llama 3.2 1B | 1B | Fastest responses |
| Gemma 2 2B | 2B | Balanced performance |
| Qwen 2.5 1.5B | 1.5B | Multilingual CVs |
| Qwen 2.5 3B | 3B | Highest quality analysis |
| Phi 3.5 Mini | 3.8B | Strong reasoning |

> All models are under 4B parameters to avoid memory errors on free tier.

---

## Quick Start

### Option 1: Hugging Face Spaces (Easiest)

1. Click the **"Open in Spaces"** badge above
2. Enter your HF token in the settings
3. Upload your CV and start searching!

### Option 2: Google Colab

1. Click the **"Open In Colab"** badge above
2. Run all cells
3. Enter your HF token when prompted
4. Use the generated public link

### Option 3: Run Locally

```bash
# Clone the repository
git clone https://github.com/sparshgupta21/ai-job-matcher.git
cd ai-job-matcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set your HF token
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx  # Linux/Mac
# set HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx   # Windows

# Optional: Set job search API key
export JSEARCH_API_KEY=your_rapidapi_key

# Launch the app
python app.py
```

Open http://localhost:7860 in your browser.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | **Yes** | HuggingFace API token ([get one free](https://huggingface.co/settings/tokens)) |
| `JSEARCH_API_KEY` | No | JSearch API key via [RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) (200 free req/month) |
| `ADZUNA_APP_ID` | No | Adzuna App ID ([register free](https://developer.adzuna.com/)) |
| `ADZUNA_API_KEY` | No | Adzuna API Key |

> Without job API keys, the app runs in **demo mode** with sample job listings.

---

## How It Works

```
1. Upload CV (PDF/DOCX)
    ↓
2. CV Parser extracts text, skills, contact info
    ↓
3. Guardrails sanitize input (prompt injection protection)
    ↓
4. LLM analyzes CV and generates search queries
    ↓
5. Job Search API fetches matching listings
    ↓
6. LLM scores each job against your profile
    ↓
7. Results displayed with match scores + apply links
```

## Security & Guardrails

This application implements multiple layers of security:

- **Input Sanitization**: Strips LLM control tokens and special characters
- **Prompt Injection Detection**: Regex-based detection of 25+ injection patterns
- **Context Isolation**: System prompts are completely separated from user data
- **Output Filtering**: PII detection and removal from LLM responses
- **Rate Limiting**: Session-based request throttling (20 req/hour)
- **File Validation**: Type, size, and content verification for uploads
- **Topic Enforcement**: LLM constrained to job-search-related responses only

---

## Deploy to Hugging Face Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Gradio** as the SDK
3. Upload all project files (or connect your GitHub repo)
4. Add `HF_TOKEN` as a Space secret in Settings
5. Optionally add `JSEARCH_API_KEY` for real job data
6. Your app will be live at `https://huggingface.co/spaces/sparshgupta21/ai-job-matcher`

---

## Project Structure

```
ai-job-matcher/
├── app.py                # Main Gradio application
├── config.py             # Model configs & filter options
├── cv_parser.py          # PDF/DOCX resume parser
├── llm_engine.py         # HF Inference API integration
├── job_search.py         # Job search API integration
├── matcher.py            # Job matching & ranking engine
├── guardrails.py         # Security & safety layer
├── prompts.py            # Isolated system prompts
├── sample_data.py        # Demo mode fallback data
├── utils.py              # Shared utilities
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables
├── colab_notebook.ipynb  # Google Colab launcher
├── README.md             # This file
└── LICENSE               # MIT License
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Hugging Face](https://huggingface.co/) for open-source models and free Spaces hosting
- [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) for job listing data
- [Gradio](https://gradio.app/) for the beautiful UI framework
- All the open-source LLM creators (Meta, Google, Alibaba, Microsoft, Mistral, HuggingFace)
