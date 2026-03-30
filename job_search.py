"""
AI Job Matcher - Job Search API Integration
Supports JSearch (RapidAPI) and Adzuna APIs with demo mode fallback.
"""

import os
import logging
import requests

from config import JSEARCH_API_URL, JSEARCH_API_HOST, ADZUNA_API_URL

logger = logging.getLogger(__name__)


def get_jsearch_api_key():
    """Get JSearch/RapidAPI key from environment."""
    return os.environ.get("JSEARCH_API_KEY", os.environ.get("RAPIDAPI_KEY", ""))


def get_adzuna_credentials():
    """Get Adzuna API credentials from environment."""
    app_id = os.environ.get("ADZUNA_APP_ID", "")
    app_key = os.environ.get("ADZUNA_API_KEY", "")
    return app_id, app_key


def search_jobs_jsearch(query, location="", job_type="", experience="", num_results=10, date_posted=""):
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
        "results_per_page": str(min(num_results, 10)),
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
                "source": "JSearch",
            }
            jobs.append(job)

        return jobs, None

    except requests.exceptions.Timeout:
        return None, "Job search request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return None, "JSearch API rate limit reached. Using demo data instead."
        elif e.response.status_code == 403:
            return None, "JSearch API key is invalid. Please check your JSEARCH_API_KEY."
        return None, f"Job search API error: {e}"
    except Exception as e:
        return None, f"Job search failed: {str(e)}"


def search_jobs_adzuna(query, location="", country="us", num_results=10):
    """
    Search jobs using Adzuna API.
    Free tier: limited daily requests.
    """
    app_id, app_key = get_adzuna_credentials()
    if not app_id or not app_key:
        return None, "No Adzuna API credentials configured."

    url = f"{ADZUNA_API_URL}/{country}/search/1"

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": min(num_results, 10),
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
                "source": "Adzuna",
            }
            jobs.append(job)

        return jobs, None

    except Exception as e:
        return None, f"Adzuna search failed: {str(e)}"


def search_jobs(query, location="", job_type="Any", experience="Any",
                num_results=10, date_posted="Any time"):
    """
    Main job search function. Tries available APIs, falls back to demo data.
    """
    # Try JSearch first
    jobs, error = search_jobs_jsearch(
        query=query,
        location=location,
        job_type=job_type if job_type != "Any" else "",
        experience=experience if experience != "Any" else "",
        num_results=num_results,
        date_posted=date_posted if date_posted != "Any time" else "",
    )

    if jobs:
        return jobs, "jsearch", None

    # Try Adzuna
    jobs, error2 = search_jobs_adzuna(query=query, location=location, num_results=num_results)
    if jobs:
        return jobs, "adzuna", None

    # Fall back to demo data
    from sample_data import get_sample_jobs
    demo_jobs = get_sample_jobs(
        query=query,
        location=location,
        job_type=job_type,
        num_results=num_results,
    )

    fallback_msg = (
        "Using demo data (no job API key configured). "
        "Set JSEARCH_API_KEY or ADZUNA_APP_ID + ADZUNA_API_KEY for real job listings."
    )

    return demo_jobs, "demo", fallback_msg


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
