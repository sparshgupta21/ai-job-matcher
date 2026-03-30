"""
AI Job Matcher - Sample Job Data
Fallback demo data when no job search API key is configured.
"""


SAMPLE_JOBS = [
    {
        "title": "Senior Software Engineer",
        "company": "TechFlow Inc.",
        "location": "San Francisco, CA (Hybrid)",
        "description": (
            "We are looking for a Senior Software Engineer to join our platform team. "
            "You will design and build scalable microservices, mentor junior engineers, "
            "and collaborate with product teams. Strong experience with Python, Go, or Java "
            "required. Cloud experience (AWS/GCP) preferred. 5+ years of experience needed."
        ),
        "salary": "$150,000 - $200,000",
        "job_type": "Full-Time",
        "date_posted": "2 days ago",
        "apply_url": "https://example.com/apply/senior-swe-techflow",
        "skills_required": ["Python", "Go", "AWS", "Microservices", "Docker", "Kubernetes"],
    },
    {
        "title": "Data Scientist",
        "company": "DataMinds Analytics",
        "location": "New York, NY (Remote)",
        "description": (
            "Join our data science team to build ML models that drive business decisions. "
            "You'll work with large datasets, develop predictive models, and present insights "
            "to stakeholders. Proficiency in Python, SQL, and ML frameworks (TensorFlow/PyTorch) "
            "required. 3+ years experience in data science or related field."
        ),
        "salary": "$120,000 - $160,000",
        "job_type": "Full-Time",
        "date_posted": "1 day ago",
        "apply_url": "https://example.com/apply/data-scientist-dataminds",
        "skills_required": ["Python", "SQL", "Machine Learning", "TensorFlow", "Statistics"],
    },
    {
        "title": "Frontend Developer",
        "company": "PixelPerfect Studios",
        "location": "Austin, TX (On-site)",
        "description": (
            "We need a creative Frontend Developer to build beautiful, responsive web applications. "
            "Strong skills in React, TypeScript, and CSS required. Experience with Next.js "
            "and design systems is a plus. You'll work closely with our UX team to deliver "
            "pixel-perfect implementations. 2-4 years experience."
        ),
        "salary": "$90,000 - $130,000",
        "job_type": "Full-Time",
        "date_posted": "3 days ago",
        "apply_url": "https://example.com/apply/frontend-dev-pixelperfect",
        "skills_required": ["React", "TypeScript", "CSS", "Next.js", "HTML"],
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudScale Solutions",
        "location": "Seattle, WA (Remote)",
        "description": (
            "Looking for a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. "
            "Must have experience with AWS, Terraform, Docker, and Kubernetes. "
            "You'll improve deployment processes, monitor system health, and ensure 99.9% uptime. "
            "3-5 years of DevOps or SRE experience required."
        ),
        "salary": "$130,000 - $170,000",
        "job_type": "Full-Time",
        "date_posted": "5 days ago",
        "apply_url": "https://example.com/apply/devops-cloudscale",
        "skills_required": ["AWS", "Terraform", "Docker", "Kubernetes", "CI/CD", "Linux"],
    },
    {
        "title": "Product Manager",
        "company": "InnovateTech",
        "location": "Chicago, IL (Hybrid)",
        "description": (
            "Seeking an experienced Product Manager to lead our B2B SaaS platform. "
            "You'll define product strategy, prioritize features, and work with engineering "
            "and design teams. Strong analytical skills and experience with Agile methodologies "
            "required. 4+ years in product management."
        ),
        "salary": "$110,000 - $150,000",
        "job_type": "Full-Time",
        "date_posted": "1 week ago",
        "apply_url": "https://example.com/apply/pm-innovatetech",
        "skills_required": ["Product Strategy", "Agile", "Scrum", "Data Analysis", "Jira"],
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Frontier Labs",
        "location": "Boston, MA (Remote)",
        "description": (
            "Join our ML team to build and deploy production ML systems. "
            "You'll develop NLP models, optimize inference pipelines, and work with MLOps tools. "
            "Strong Python skills and experience with PyTorch or TensorFlow required. "
            "Experience with LLMs and transformer architectures is highly valued. 3+ years."
        ),
        "salary": "$140,000 - $190,000",
        "job_type": "Full-Time",
        "date_posted": "4 days ago",
        "apply_url": "https://example.com/apply/ml-engineer-aifrontier",
        "skills_required": ["Python", "PyTorch", "NLP", "MLOps", "Deep Learning", "Docker"],
    },
    {
        "title": "UX Designer",
        "company": "DesignFirst Agency",
        "location": "Los Angeles, CA (Hybrid)",
        "description": (
            "We're hiring a UX Designer to create intuitive, user-centered designs for web "
            "and mobile applications. You'll conduct user research, create wireframes and "
            "prototypes, and collaborate with developers. Proficiency in Figma required. "
            "Portfolio demonstrating strong UX thinking needed. 2-5 years experience."
        ),
        "salary": "$85,000 - $120,000",
        "job_type": "Full-Time",
        "date_posted": "6 days ago",
        "apply_url": "https://example.com/apply/ux-designer-designfirst",
        "skills_required": ["Figma", "User Research", "Wireframing", "Prototyping", "UI Design"],
    },
    {
        "title": "Backend Developer (Python)",
        "company": "ServerStack Corp",
        "location": "Denver, CO (Remote)",
        "description": (
            "Looking for a Python Backend Developer to build REST APIs and microservices. "
            "Experience with Django or FastAPI, PostgreSQL, and Redis required. "
            "You'll design scalable backend architectures and write clean, tested code. "
            "Strong understanding of software design patterns. 3+ years Python experience."
        ),
        "salary": "$100,000 - $140,000",
        "job_type": "Full-Time",
        "date_posted": "2 days ago",
        "apply_url": "https://example.com/apply/backend-python-serverstack",
        "skills_required": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "REST API"],
    },
    {
        "title": "Cybersecurity Analyst",
        "company": "SecureNet Defense",
        "location": "Washington, DC (On-site)",
        "description": (
            "Join our security operations team to monitor, detect, and respond to cyber threats. "
            "You'll perform vulnerability assessments, manage SIEM tools, and develop security "
            "policies. CISSP or CEH certification preferred. Knowledge of network security, "
            "firewalls, and incident response required. 2-4 years experience."
        ),
        "salary": "$95,000 - $135,000",
        "job_type": "Full-Time",
        "date_posted": "3 days ago",
        "apply_url": "https://example.com/apply/cybersec-securenet",
        "skills_required": ["Cybersecurity", "SIEM", "Network Security", "Penetration Testing", "Linux"],
    },
    {
        "title": "Marketing Analyst",
        "company": "GrowthHub Marketing",
        "location": "Miami, FL (Remote)",
        "description": (
            "We need a Marketing Analyst to drive data-driven marketing decisions. "
            "You'll analyze campaign performance, build dashboards, and provide actionable "
            "insights. Proficiency in Google Analytics, SQL, and visualization tools "
            "(Tableau/Power BI) required. 1-3 years experience in marketing analytics."
        ),
        "salary": "$65,000 - $90,000",
        "job_type": "Full-Time",
        "date_posted": "1 day ago",
        "apply_url": "https://example.com/apply/marketing-analyst-growthhub",
        "skills_required": ["SQL", "Google Analytics", "Tableau", "Excel", "Data Analysis"],
    },
    {
        "title": "Junior Software Developer",
        "company": "CodeLaunch Startups",
        "location": "Portland, OR (Hybrid)",
        "description": (
            "Great opportunity for early-career developers! You'll build features for our "
            "web application using React and Node.js. We provide mentorship and growth "
            "opportunities. Basic knowledge of JavaScript, HTML/CSS, and Git required. "
            "0-2 years experience. CS degree or bootcamp graduate welcome."
        ),
        "salary": "$60,000 - $80,000",
        "job_type": "Full-Time",
        "date_posted": "1 day ago",
        "apply_url": "https://example.com/apply/junior-dev-codelaunch",
        "skills_required": ["JavaScript", "React", "Node.js", "HTML", "CSS", "Git"],
    },
    {
        "title": "Cloud Solutions Architect",
        "company": "MegaCloud Systems",
        "location": "Dallas, TX (Remote)",
        "description": (
            "Design and implement enterprise cloud solutions on AWS and Azure. "
            "You'll work with clients to understand their needs, design architectures, "
            "and lead migration projects. AWS Solutions Architect certification required. "
            "8+ years IT experience with 5+ years in cloud architecture."
        ),
        "salary": "$160,000 - $210,000",
        "job_type": "Full-Time",
        "date_posted": "1 week ago",
        "apply_url": "https://example.com/apply/cloud-architect-megacloud",
        "skills_required": ["AWS", "Azure", "Cloud Architecture", "Terraform", "Security"],
    },
]


def get_sample_jobs(query="", location="", job_type="Any", num_results=10):
    """Return filtered sample jobs for demo mode."""
    results = SAMPLE_JOBS.copy()

    if query:
        query_lower = query.lower()
        results = [
            job for job in results
            if query_lower in job["title"].lower()
            or query_lower in job["description"].lower()
            or any(query_lower in skill.lower() for skill in job.get("skills_required", []))
        ]

    if location and location.lower() != "any":
        loc_lower = location.lower()
        results = [
            job for job in results
            if loc_lower in job["location"].lower()
        ]

    if job_type and job_type != "Any":
        results = [
            job for job in results
            if job.get("job_type", "").lower() == job_type.lower()
        ]

    return results[:num_results]
