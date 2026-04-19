"""
AI Job Matcher v2.0 — LLM Inference Engine
Supports HF Inference API (serverless) with retry logic and structured output.
"""

import os
import time
import logging
import json

logger = logging.getLogger(__name__)


def get_hf_token():
    """Get HuggingFace token from environment or return None."""
    return os.environ.get("HF_TOKEN", os.environ.get("HUGGINGFACE_TOKEN", ""))


def call_llm(model_id, system_prompt, user_content, max_tokens=2048, temperature=0.3, retries=2):
    """
    Call an LLM via the HuggingFace Inference API with retry logic.

    Args:
        model_id: HuggingFace model identifier
        system_prompt: System-level instructions (isolated from user)
        user_content: User-provided content (treated as data)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        retries: Number of retry attempts on transient failure

    Returns:
        str: Generated text response
    """
    token = get_hf_token()

    if not token:
        return _fallback_response(user_content)

    last_error = None

    for attempt in range(retries + 1):
        try:
            from huggingface_hub import InferenceClient

            client = InferenceClient(token=token)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]

            response = client.chat_completion(
                model=model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            result = response.choices[0].message.content
            return result.strip() if result else "No response generated."

        except Exception as e:
            last_error = str(e)
            logger.warning(f"LLM call attempt {attempt + 1}/{retries + 1} failed: {last_error}")

            # Don't retry on auth errors or model-not-found
            if any(code in last_error for code in ["401", "403", "404"]):
                break

            # Exponential backoff for rate limits
            if "429" in last_error or "rate limit" in last_error.lower():
                wait_time = min(2 ** attempt * 2, 30)
                logger.info(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            elif attempt < retries:
                time.sleep(1)

    return _handle_error(last_error, model_id)


def call_llm_structured(model_id, system_prompt, user_content, max_tokens=2048):
    """
    Call LLM and attempt to parse structured output.
    Falls back to raw text if JSON parsing fails.

    Returns:
        tuple[str, dict | None]: (raw_text, parsed_dict_or_None)
    """
    raw = call_llm(model_id, system_prompt, user_content, max_tokens=max_tokens)

    # Try to extract JSON from the response
    parsed = None
    try:
        # Look for JSON block in response
        json_match = None
        if "```json" in raw:
            start = raw.index("```json") + 7
            end = raw.index("```", start)
            json_match = raw[start:end].strip()
        elif "{" in raw and "}" in raw:
            # Try to extract the outermost JSON object
            start = raw.index("{")
            depth = 0
            for i, c in enumerate(raw[start:], start):
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        json_match = raw[start:i + 1]
                        break

        if json_match:
            parsed = json.loads(json_match)
    except (json.JSONDecodeError, ValueError):
        pass

    return raw, parsed


def _handle_error(error_msg, model_id):
    """Format error messages for the user."""
    if not error_msg:
        error_msg = "Unknown error"

    logger.error(f"LLM API error: {error_msg}")

    if "rate limit" in error_msg.lower() or "429" in error_msg:
        return (
            "## Rate Limit Reached\n\n"
            "The HuggingFace Inference API rate limit has been exceeded. "
            "Please wait a few minutes and try again, or try a different model.\n\n"
            "**Tip:** Free tier has limited credits (~$0.10/month). "
            "Consider using smaller models like SmolLM2 1.7B for faster responses."
        )
    elif "401" in error_msg or "unauthorized" in error_msg.lower():
        return (
            "## Authentication Error\n\n"
            "Your HuggingFace token is invalid or expired. "
            "Please check your `HF_TOKEN` environment variable.\n\n"
            "Get a free token at: https://huggingface.co/settings/tokens"
        )
    elif "model" in error_msg.lower() and ("not found" in error_msg.lower() or "404" in error_msg):
        return (
            "## Model Not Available\n\n"
            f"The model `{model_id}` is currently unavailable on the Inference API. "
            "Please try a different model from the dropdown."
        )
    else:
        return (
            f"## LLM Error\n\n"
            f"An error occurred while processing your request: {error_msg}\n\n"
            "Please try again or select a different model."
        )


def _fallback_response(user_content):
    """Generate a basic response when no HF token is available."""
    return (
        "## HuggingFace Token Required\n\n"
        "To use AI-powered analysis, please provide your HuggingFace API token:\n\n"
        "1. **Get a free token** at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)\n"
        "2. **Set it** as the `HF_TOKEN` environment variable, or paste it in the token field above\n\n"
        "### Without a token, here's what was extracted from your CV:\n\n"
        f"```\n{user_content[:500]}...\n```\n\n"
        "*AI analysis features (job matching, cover letters, auto-fill) require a valid HF token.*"
    )


# ─────────────────────────────────────────────
# Agent-specific LLM functions
# ─────────────────────────────────────────────

def analyze_cv_with_llm(model_id, cv_text):
    """Use LLM to analyze a CV and extract structured information."""
    from prompts import AGENT1_CV_SYSTEM_PROMPT
    from guardrails import wrap_user_content_safely

    safe_content = wrap_user_content_safely(cv_text)
    return call_llm(model_id, AGENT1_CV_SYSTEM_PROMPT, safe_content)


def match_jobs_with_llm(model_id, cv_text, jobs_data):
    """Use LLM to match and rank jobs against a CV."""
    from prompts import AGENT2_JOB_SEARCH_PROMPT
    from guardrails import wrap_user_content_safely

    # Format jobs for LLM
    jobs_text = "\n\n".join([
        f"### Job {i+1}: {job.get('title', 'N/A')}\n"
        f"- **Company:** {job.get('company', 'N/A')}\n"
        f"- **Location:** {job.get('location', 'N/A')}\n"
        f"- **Description:** {job.get('description', 'N/A')[:300]}\n"
        f"- **Apply URL:** {job.get('apply_url', 'N/A')}\n"
        for i, job in enumerate(jobs_data[:10])
    ])

    user_content = wrap_user_content_safely(cv_text)
    user_content += f"\n\n--- JOB LISTINGS TO EVALUATE ---\n{jobs_text}"

    return call_llm(model_id, AGENT2_JOB_SEARCH_PROMPT, user_content, max_tokens=3000)


def generate_search_queries(model_id, cv_text):
    """Use LLM to generate optimized job search queries from CV."""
    from prompts import AGENT2_QUERY_GENERATION_PROMPT
    from guardrails import wrap_user_content_safely

    safe_content = wrap_user_content_safely(cv_text)
    return call_llm(model_id, AGENT2_QUERY_GENERATION_PROMPT, safe_content, max_tokens=500)


def generate_autofill(model_id, cv_text):
    """Use LLM to extract auto-fill data from CV."""
    from prompts import AGENT3_APPLICATION_PROMPT
    from guardrails import wrap_user_content_safely

    safe_content = wrap_user_content_safely(cv_text)
    return call_llm(model_id, AGENT3_APPLICATION_PROMPT, safe_content, max_tokens=1000)


def generate_cover_letter(model_id, cv_text, job_title, company_name):
    """Use LLM to generate a tailored cover letter."""
    from prompts import COVER_LETTER_PROMPT
    from guardrails import wrap_user_content_safely

    safe_content = wrap_user_content_safely(cv_text)
    safe_content += (
        f"\n\n--- TARGET JOB ---\n"
        f"Job Title: {job_title}\n"
        f"Company: {company_name}\n"
    )

    return call_llm(model_id, COVER_LETTER_PROMPT, safe_content, max_tokens=1500)
