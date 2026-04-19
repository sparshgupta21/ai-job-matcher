"""
AI Job Matcher - CV/Resume Parser
Extracts structured data from PDF and DOCX resume files.
"""

import re
import os


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")


def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX: {str(e)}")


def extract_text(file_path):
    """Extract text from uploaded file (PDF or DOCX)."""
    if not file_path or not os.path.exists(file_path):
        raise ValueError("File not found.")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def extract_email(text):
    """Extract email addresses from text."""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    matches = re.findall(pattern, text)
    return matches[0] if matches else ""


def extract_phone(text):
    """Extract phone numbers from text."""
    patterns = [
        r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return the longest match (most complete number)
            return max(matches, key=len).strip()
    return ""


def extract_linkedin(text):
    """Extract LinkedIn URL from text."""
    pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches[0] if matches else ""


def extract_name(text):
    """Extract candidate name (heuristic: first non-empty line that looks like a name)."""
    lines = text.strip().split("\n")
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like headers, emails, or phone numbers
        if "@" in line or re.search(r"\d{3}", line):
            continue
        if len(line) < 50 and len(line.split()) <= 5:
            # Likely a name
            return line
    return ""


SECTION_HEADERS = {
    "experience": [
        "experience", "work experience", "employment", "work history",
        "professional experience", "career history", "employment history",
    ],
    "education": [
        "education", "academic", "qualifications", "academic background",
        "educational background", "degrees",
    ],
    "skills": [
        "skills", "technical skills", "core competencies", "key skills",
        "competencies", "expertise", "proficiencies", "technologies",
        "tools", "programming languages",
    ],
    "summary": [
        "summary", "profile", "objective", "about", "professional summary",
        "career objective", "personal statement", "overview",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "credentials",
        "professional certifications",
    ],
    "projects": [
        "projects", "key projects", "notable projects", "portfolio",
    ],
}


def detect_sections(text):
    """Detect and extract resume sections."""
    lines = text.split("\n")
    sections = {}
    current_section = "header"
    current_content = []

    for line in lines:
        stripped = line.strip().lower()
        found_section = None

        for section_name, headers in SECTION_HEADERS.items():
            for header in headers:
                # Check if line is a section header
                if stripped == header or stripped.startswith(header + ":") or stripped.startswith(header + " :"):
                    found_section = section_name
                    break
                # Check for headers with formatting (e.g., "== EXPERIENCE ==")
                cleaned = re.sub(r"[=\-_*#|]+", "", stripped).strip()
                if cleaned == header:
                    found_section = section_name
                    break
            if found_section:
                break

        if found_section:
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = found_section
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def extract_skills_keywords(text):
    """Extract skill keywords from text using common tech/business terms."""
    common_skills = [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "golang",
        "rust", "swift", "kotlin", "php", "scala", "r", "matlab", "sql", "nosql",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "fastapi",
        "spring", "hibernate", "laravel", ".net", "asp.net",
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
        "jenkins", "ci/cd", "git", "github", "gitlab", "bitbucket",
        "machine learning", "deep learning", "nlp", "computer vision", "ai",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "data science", "data analysis", "data engineering", "etl",
        "sql server", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "rest api", "graphql", "microservices", "api design",
        "agile", "scrum", "kanban", "jira", "confluence",
        "html", "css", "sass", "tailwind", "bootstrap",
        "linux", "unix", "windows server", "networking",
        "cybersecurity", "penetration testing", "security",
        "project management", "team leadership", "communication",
        "excel", "powerpoint", "tableau", "power bi", "looker",
        "salesforce", "sap", "erp", "crm",
        "figma", "sketch", "adobe", "photoshop", "illustrator",
        "blockchain", "web3", "solidity",
        "devops", "sre", "monitoring", "observability",
    ]

    text_lower = text.lower()
    found_skills = []
    for skill in common_skills:
        if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
            found_skills.append(skill.title() if len(skill) > 3 else skill.upper())

    return list(set(found_skills))


def parse_cv(file_path):
    """
    Main CV parsing function.
    Returns a structured dictionary with extracted information.
    """
    # Extract raw text
    raw_text = extract_text(file_path)

    if not raw_text or len(raw_text.strip()) < 50:
        raise ValueError(
            "Could not extract sufficient text from the file. "
            "Please ensure your CV is not an image-only PDF."
        )

    # Truncate if too long
    from config import MAX_CV_TEXT_LENGTH
    if len(raw_text) > MAX_CV_TEXT_LENGTH:
        raw_text = raw_text[:MAX_CV_TEXT_LENGTH]

    # Extract contact info
    contact = {
        "name": extract_name(raw_text),
        "email": extract_email(raw_text),
        "phone": extract_phone(raw_text),
        "linkedin": extract_linkedin(raw_text),
    }

    # Detect sections
    sections = detect_sections(raw_text)

    # Extract skills
    skills = extract_skills_keywords(raw_text)

    return {
        "raw_text": raw_text,
        "contact": contact,
        "sections": sections,
        "skills": skills,
        "file_name": os.path.basename(file_path),
    }
