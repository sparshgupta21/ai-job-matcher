"""
AI Job Matcher v2.0 — Job Search Integration
Multi-provider search: Tavily → DuckDuckGo → JSearch → Adzuna → Demo fallback.
India-first portal targeting with global fallback.
"""

import os
import logging
import requests

from config import (
    JSEARCH_API_URL, JSEARCH_API_HOST, ADZUNA_API_URL,
    JOB_PORTAL_SITES_INDIA, JOB_PORTAL_SITES_GLOBAL,
    MAX_TAVILY_RESULTS, MAX_DUCKDUCKGO_RESULTS,
    MAX_JSEARCH_RESULTS, MAX_ADZUNA_RESULTS,
    SEARCH_PROVIDER_PRIORITY,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
# 1. TAVILY SEARCH (Primary — 1,000 free/month)
# ═══════════════════════════════════════════════

def get_tavily_api_key():
    """Get Tavily API key from environment."""
    return os.environ.get("TAVILY_API_KEY", "")


def search_jobs_tavily(query, location="", job_type="", experience="",
                       num_results=8, include_india=True, api_key=""):
    """
    Search jobs using Tavily Search API.
    Targets specific job portal sites for structured results.
    """
    # Per-user key takes priority; fall back to env var only for CLI/local use
    effective_key = api_key or get_tavily_api_key()
    if not effective_key:
        return None, "No Tavily API key configured."

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=effective_key)

        # Build search query with location
        search_query = f"{query} jobs"
        if location:
            search_query += f" in {location}"
        if job_type and job_type != "Any":
            search_query += f" {job_type}"
        if experience and experience != "Any":
            search_query += f" {experience}"

        # Target India-first portals
        portal_sites = JOB_PORTAL_SITES_INDIA if include_india else JOB_PORTAL_SITES_GLOBAL

        response = client.search(
            query=search_query,
            search_depth="basic",
            max_results=min(num_results, MAX_TAVILY_RESULTS),
            include_domains=portal_sites[:5],
            include_answer=False,
        )

        jobs = []
        for result in response.get("results", []):
            url = result.get("url", "")
            title_raw = result.get("title", "")
            content = result.get("content", "")

            # Parse job details from search result
            job = _parse_tavily_result(title_raw, content, url)
            if job:
                jobs.append(job)

        if jobs:
            logger.info(f"Tavily returned {len(jobs)} job results")
            return jobs, None

        return None, "Tavily returned no matching jobs."

    except Exception as e:
        logger.warning(f"Tavily search failed: {e}")
        return None, f"Tavily search failed: {str(e)}"


def _parse_tavily_result(title, content, url):
    """Parse a Tavily search result into a job listing dict."""
    if not title or not url:
        return None

    # Determine source portal
    source = "tavily"
    for portal in JOB_PORTAL_SITES_INDIA + JOB_PORTAL_SITES_GLOBAL:
        if portal in url:
            source = portal.split(".")[0]  # e.g., "naukri", "linkedin"
            break

    # Clean title — often includes "- Company Name" or "| Location"
    title_clean = title
    company = "N/A"
    for sep in [" - ", " | ", " at ", " — "]:
        if sep in title:
            parts = title.split(sep, 1)
            title_clean = parts[0].strip()
            company = parts[1].strip() if len(parts) > 1 else "N/A"
            break

    # Extract location from content if present
    location = "India"
    location_keywords = ["location:", "place:", "city:", "based in", "office:"]
    for keyword in location_keywords:
        if keyword.lower() in content.lower():
            idx = content.lower().index(keyword.lower()) + len(keyword)
            loc_text = content[idx:idx + 50].strip()
            location = loc_text.split("\n")[0].split(",")[0].strip()[:40]
            break

    return {
        "title": title_clean[:100],
        "company": company[:60],
        "location": location,
        "description": content[:500] if content else "",
        "salary": "Not specified",
        "job_type": "N/A",
        "date_posted": "",
        "apply_url": url,
        "skills_required": [],
        "source": source,
    }


# ═══════════════════════════════════════════════
# 2. DUCKDUCKGO SEARCH (Free, Unlimited fallback)
# ═══════════════════════════════════════════════

def search_jobs_duckduckgo(query, location="", num_results=10):
    """
    Search jobs using DuckDuckGo (completely free, no API key).
    Uses duckduckgo-search Python library.
    """
    try:
        from duckduckgo_search import DDGS

        search_query = f"{query} jobs"
        if location:
            search_query += f" in {location}"

        # Add India-specific job portals
        search_query += " (naukri OR linkedin OR iimjobs OR foundit)"

        jobs = []
        with DDGS() as ddgs:
            results = list(ddgs.text(
                search_query,
                region="in-en",  # India English
                max_results=min(num_results, MAX_DUCKDUCKGO_RESULTS),
            ))

        for result in results:
            title = result.get("title", "")
            body = result.get("body", "")
            url = result.get("href", "")

            job = _parse_tavily_result(title, body, url)  # same parser works
            if job:
                job["source"] = "duckduckgo"
                jobs.append(job)

        if jobs:
            logger.info(f"DuckDuckGo returned {len(jobs)} job results")
            return jobs, None

        return None, "DuckDuckGo returned no matching jobs."

    except ImportError:
        return None, "duckduckgo-search library not installed."
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        return None, f"DuckDuckGo search failed: {str(e)}"


# ═══════════════════════════════════════════════
# 3. JSEARCH API (RapidAPI — 200 free/month)
# ═══════════════════════════════════════════════

def get_jsearch_api_key():
    """Get JSearch/RapidAPI key from environment."""
    return os.environ.get("JSEARCH_API_KEY", os.environ.get("RAPIDAPI_KEY", ""))


def search_jobs_jsearch(query, location="", job_type="", experience="",
                        num_results=10, date_posted=""):
    """
    Search jobs using JSearch API (via RapidAPI).
    Free tier: ~200 requests/month.
    """
    api_key = get_jsearch_api_key()
    if not api_key:
        return None, "No JSearch API key configured."

    # Build search query
    search_query = query
    if location:
        search_query += f" in {location}"

    params = {
        "query": search_query,
        "page": "1",
        "num_pages": "1",
        "results_per_page": str(min(num_results, MAX_JSEARCH_RESULTS)),
    }

    # Map date_posted filter
    date_map = {
        "Past 24 hours": "today",
        "Past 3 days": "3days",
        "Past week": "week",
        "Past month": "month",
    }
    if date_posted and date_posted in date_map:
        params["date_posted"] = date_map[date_posted]

    # Map job type
    type_map = {
        "Full-Time": "FULLTIME",
        "Part-Time": "PARTTIME",
        "Contract": "CONTRACTOR",
        "Internship": "INTERN",
    }
    if job_type and job_type in type_map:
        params["employment_types"] = type_map[job_type]

    # Map experience
    exp_map = {
        "Internship / Entry Level (0-1 years)": "under_3_years",
        "Junior (1-3 years)": "under_3_years",
        "Mid-Level (3-5 years)": "more_than_3_years",
        "Senior (5-10 years)": "more_than_3_years",
        "Lead / Principal (10+ years)": "more_than_3_years",
    }
    if experience and experience in exp_map:
        params["job_requirements"] = exp_map[experience]

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": JSEARCH_API_HOST,
    }

    try:
        response = requests.get(JSEARCH_API_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("data", []):
            job = {
                "title": item.get("job_title", "N/A"),
                "company": item.get("employer_name", "N/A"),
                "location": _format_location(item),
                "description": item.get("job_description", "")[:500],
                "salary": _format_salary(item),
                "job_type": item.get("job_employment_type", "N/A"),
                "date_posted": item.get("job_posted_at_datetime_utc", "N/A")[:10],
                "apply_url": item.get("job_apply_link", "#"),
                "skills_required": item.get("job_required_skills") or [],
                "source": "jsearch",
            }
            jobs.append(job)

        return jobs, None

    except requests.exceptions.Timeout:
        return None, "Job search request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return None, "JSearch API rate limit reached."
        elif e.response.status_code == 403:
            return None, "JSearch API key is invalid."
        return None, f"Job search API error: {e}"
    except Exception as e:
        return None, f"Job search failed: {str(e)}"


# ═══════════════════════════════════════════════
# 4. ADZUNA API
# ═══════════════════════════════════════════════

def get_adzuna_credentials():
    """Get Adzuna API credentials from environment."""
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_API_KEY", "")
    return app_id, app_key


def search_jobs_adzuna(query, location="", country="in", num_results=10):
    """
    Search jobs using Adzuna API.
    Default to India (country='in').
    """
    app_id, app_key = get_adzuna_credentials()
    if not app_id or not app_key:
        return None, "No Adzuna API credentials configured."

    url = f"{ADZUNA_API_URL}/{country}/search/1"

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": min(num_results, MAX_ADZUNA_RESULTS),
        "what": query,
        "content-type": "application/json",
    }

    if location:
        params["where"] = location

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for item in data.get("results", []):
            job = {
                "title": item.get("title", "N/A"),
                "company": item.get("company", {}).get("display_name", "N/A"),
                "location": item.get("location", {}).get("display_name", "N/A"),
                "description": item.get("description", "")[:500],
                "salary": _format_adzuna_salary(item),
                "job_type": item.get("contract_time", "N/A"),
                "date_posted": item.get("created", "N/A")[:10],
                "apply_url": item.get("redirect_url", "#"),
                "skills_required": [],
                "source": "adzuna",
            }
            jobs.append(job)

        return jobs, None

    except Exception as e:
        return None, f"Adzuna search failed: {str(e)}"


# ═══════════════════════════════════════════════
# 5. MAIN SEARCH ORCHESTRATOR
# ═══════════════════════════════════════════════

def search_jobs(query, location="", job_type="Any", experience="Any",
                num_results=10, date_posted="Any time", tavily_api_key=""):
    """
    Main job search function.
    Tries providers in priority order, falls back to demo data.
    Returns: (jobs_list, source_name, warning_or_None)
    """
    all_jobs = []
    sources_tried = []
    warnings = []

    for provider in SEARCH_PROVIDER_PRIORITY:
        if len(all_jobs) >= num_results:
            break

        if provider == "tavily":
            jobs, error = search_jobs_tavily(
                query=query, location=location,
                job_type=job_type if job_type != "Any" else "",
                experience=experience if experience != "Any" else "",
                num_results=num_results,
                api_key=tavily_api_key,
            )
            if jobs:
                all_jobs.extend(jobs)
                sources_tried.append("tavily")
            elif error:
                warnings.append(error)

        elif provider == "duckduckgo":
            jobs, error = search_jobs_duckduckgo(
                query=query, location=location,
                num_results=num_results - len(all_jobs),
            )
            if jobs:
                all_jobs.extend(jobs)
                sources_tried.append("duckduckgo")
            elif error:
                warnings.append(error)

        elif provider == "jsearch":
            jobs, error = search_jobs_jsearch(
                query=query, location=location,
                job_type=job_type if job_type != "Any" else "",
                experience=experience if experience != "Any" else "",
                num_results=num_results - len(all_jobs),
                date_posted=date_posted if date_posted != "Any time" else "",
            )
            if jobs:
                all_jobs.extend(jobs)
                sources_tried.append("jsearch")
            elif error:
                warnings.append(error)

        elif provider == "adzuna":
            jobs, error = search_jobs_adzuna(
                query=query, location=location,
                num_results=num_results - len(all_jobs),
            )
            if jobs:
                all_jobs.extend(jobs)
                sources_tried.append("adzuna")
            elif error:
                warnings.append(error)

        elif provider == "demo":
            if not all_jobs:
                from sample_data import get_sample_jobs
                demo_jobs = get_sample_jobs(
                    query=query, location=location,
                    job_type=job_type, num_results=num_results,
                )
                all_jobs.extend(demo_jobs)
                sources_tried.append("demo")

    # Deduplicate by URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        url = job.get("apply_url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_jobs.append(job)

    unique_jobs = unique_jobs[:num_results]

    source_str = "+".join(sources_tried) if sources_tried else "demo"
    warning_str = None

    if "demo" in sources_tried and len(sources_tried) == 1:
        warning_str = (
            "Using demo data (no search API keys configured). "
            "Set TAVILY_API_KEY for real job listings from Indian portals."
        )
    elif warnings and not unique_jobs:
        warning_str = " | ".join(warnings[:2])

    return unique_jobs, source_str, warning_str


# ═══════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════

def _format_location(item):
    """Format location from JSearch API response."""
    city = item.get("job_city", "")
    state = item.get("job_state", "")
    country = item.get("job_country", "")
    remote = item.get("job_is_remote", False)

    parts = [p for p in [city, state] if p]
    location = ", ".join(parts) if parts else country or "N/A"

    if remote:
        location += " (Remote)"

    return location


def _format_salary(item):
    """Format salary from JSearch API response."""
    min_sal = item.get("job_min_salary")
    max_sal = item.get("job_max_salary")
    period = item.get("job_salary_period", "")

    if min_sal and max_sal:
        return f"${min_sal:,.0f} - ${max_sal:,.0f} {period}".strip()
    elif min_sal:
        return f"From ${min_sal:,.0f} {period}".strip()
    elif max_sal:
        return f"Up to ${max_sal:,.0f} {period}".strip()
    return "Not specified"


def _format_adzuna_salary(item):
    """Format salary from Adzuna API response."""
    min_sal = item.get("salary_min")
    max_sal = item.get("salary_max")

    if min_sal and max_sal:
        return f"${min_sal:,.0f} - ${max_sal:,.0f}"
    elif min_sal:
        return f"From ${min_sal:,.0f}"
    return "Not specified"
