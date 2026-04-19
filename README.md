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
short_description: Multi-Agent AI job matching with open-source LLMs
---

# AI Job Matcher v2.0

> **Multi-Agent AI job matching powered by open-source LLMs from Hugging Face**

Upload your CV, and 3 AI agents work together to analyze your profile, hunt for matching jobs across Indian portals (Naukri, LinkedIn, IIMJobs, Foundit), and prepare application packages with auto-fill data and tailored tips.

[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-lg-dark.svg)](https://huggingface.co/spaces/sparsh21/AI_job_matcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sparshgupta21/ai-job-matcher/blob/main/colab_notebook.ipynb)

---

## 🏗️ Architecture: 3 AI Agents

```
📄 Agent 1: CV Ingestor        🔍 Agent 2: Job Hunter           📋 Agent 3: Application Helper
  ├── Parse PDF/DOCX             ├── Build smart queries           ├── Direct apply links
  ├── Extract skills/contact     ├── Search Naukri, LinkedIn       ├── Auto-fill form data
  ├── LLM-enhanced analysis      │   IIMJobs, Foundit, Monster     ├── Cover letter snippets
  └── → CVProfile (Pydantic)     ├── Score & rank matches          └── Application tips
                                 └── → JobListings (Pydantic)
```

All agents communicate through **Pydantic v2 data contracts** — no raw text passed between agents, only validated schemas.

---

## Features

| Feature | Description |
|---------|-------------|
| **3-Agent Architecture** | CV Ingestor → Job Hunter → Application Helper pipeline |
| **Pydantic Contracts** | Typed data handshake between agents with validation |
| **India-First Search** | Targets Naukri, LinkedIn India, IIMJobs, Foundit, Shine |
| **Multi-Provider Search** | Tavily → DuckDuckGo (free!) → JSearch → Adzuna → Demo |
| **LLM Selection** | 6 free open-source models (1B-3.8B params) |
| **Auto-Fill** | Extract application data ready to copy-paste |
| **Cover Letters** | AI-generated tailored snippets per job |
| **Security** | Multi-layer guardrails, HMAC-signed agent context |
| **Privacy** | CVs processed in-memory only — never stored |
| **Portal Tips** | Naukri/LinkedIn/IIMJobs-specific application advice |

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
2. Enter your HF token and Tavily key
3. Upload your CV and launch the pipeline!

### Option 2: Run Locally

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

# Set your API keys
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
export TAVILY_API_KEY=tvly-xxxxxxxxxx   # optional but recommended

# Launch the app
python app.py
```

Open http://localhost:7860 in your browser.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_TOKEN` | **Yes** | HuggingFace API token ([get free](https://huggingface.co/settings/tokens)) |
| `TAVILY_API_KEY` | Recommended | Tavily search key ([get free](https://tavily.com), 1000/month) |
| `JSEARCH_API_KEY` | No | JSearch via RapidAPI (200 free/month) |
| `ADZUNA_APP_ID` | No | Adzuna App ID |
| `ADZUNA_API_KEY` | No | Adzuna API Key |

> **Free search without API keys:** The app includes DuckDuckGo search (unlimited, no key needed) and demo mode as fallbacks.

---

## How It Works

```
1. Upload CV (PDF/DOCX)
    ↓
2. Agent 1 (CV Ingestor):
   - Parse text, extract skills, contact info
   - LLM-enhanced experience classification
   - Output: CVProfile (Pydantic model)
    ↓
3. Agent 2 (Job Hunter):
   - Build search queries from CVProfile
   - Search: Tavily → DuckDuckGo → JSearch → Adzuna
   - Target: Naukri, LinkedIn, IIMJobs, Foundit
   - LLM-score each job vs your profile
   - Output: Ranked JobListings (Pydantic models)
    ↓
4. Agent 3 (Application Helper):
   - Generate auto-fill fields from CV
   - Create cover letter snippets per job
   - Provide portal-specific application tips
   - Output: ApplicationPackages (Pydantic models)
    ↓
5. Dashboard shows all results across 4 tabs
```

## Security & Guardrails

This application implements multiple layers of security:

- **Input Sanitization**: Strips LLM control tokens and special characters
- **Prompt Injection Detection**: 30+ regex patterns including multi-agent attacks
- **Context Isolation**: System prompts completely separated from user data
- **HMAC-Signed Agent Context**: Agents verify data integrity between pipeline stages
- **Output Filtering**: PII detection (SSN, credit cards, Aadhaar, PAN) from LLM responses
- **Rate Limiting**: Session-based request throttling (20 req/hour)
- **File Validation**: Type, size, and content verification for uploads
- **Topic Enforcement**: Agents constrained to job-search-related responses only
- **Pydantic Validation**: All inter-agent data validated by strict schemas

---

## Project Structure

```
ai-job-matcher/
├── app.py                      # Main Gradio dashboard
├── config.py                   # Models, filters, API settings
├── models.py                   # Pydantic v2 data contracts
├── agents/
│   ├── __init__.py
│   ├── base.py                 # Base agent class
│   ├── cv_ingestor.py          # Agent 1: CV parsing & analysis
│   ├── job_hunter.py           # Agent 2: Multi-portal job search
│   ├── application_helper.py   # Agent 3: Apply links & auto-fill
│   └── orchestrator.py         # Pipeline coordinator
├── cv_parser.py                # PDF/DOCX text extraction
├── llm_engine.py               # HF Inference API with retry
├── job_search.py               # Tavily + DuckDuckGo + JSearch + Adzuna
├── guardrails.py               # Multi-layer security
├── prompts.py                  # Agent system prompts
├── sample_data.py              # Demo mode fallback data
├── utils.py                    # Shared utilities
├── matcher.py                  # Legacy pipeline (backward compat)
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── colab_notebook.ipynb        # Google Colab launcher
├── README.md                   # This file
└── LICENSE                     # MIT License
```

---

## Search Provider Priority

| Priority | Provider | Free Tier | Requires Key? |
|----------|----------|-----------|---------------|
| 1 | **Tavily** | 1,000/month | Yes |
| 2 | **DuckDuckGo** | Unlimited | **No** ✨ |
| 3 | **JSearch** | 200/month | Yes |
| 4 | **Adzuna** | Limited | Yes |
| 5 | **Demo Mode** | Unlimited | No |

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
- [Tavily](https://tavily.com/) for AI-optimized search API
- [DuckDuckGo](https://duckduckgo.com/) for free, unlimited search
- [Gradio](https://gradio.app/) for the UI framework
- [Pydantic](https://docs.pydantic.dev/) for data validation
- All the open-source LLM creators (Meta, Google, Alibaba, Microsoft, HuggingFace)
