import os
import io
import json
import tempfile
import traceback
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, flash, redirect, url_for
)
from werkzeug.utils import secure_filename

# ── Resume Parser ──────────────────────────────────────────────────────────
try:
    from pyresparser import ResumeParser
    RESUME_PARSER_AVAILABLE = True
except Exception as e:
    RESUME_PARSER_AVAILABLE = False
    print(f"[WARN] pyresparser not available: {e}")

# ── Job Scraper ────────────────────────────────────────────────────────────
try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except Exception as e:
    JOBSPY_AVAILABLE = False
    print(f"[WARN] jobspy not available: {e}")


# ── App Configuration ──────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "galaxy-job-secret-key-change-in-prod")

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

# Default countries for global search — you can expand from JobSpy's 60+
SUPPORTED_COUNTRIES = [
    "USA", "UK", "Canada", "Australia", "India", "Germany",
    "France", "Spain", "Italy", "Netherlands", "Brazil", "Japan",
    "Singapore", "UAE", "Switzerland", "Sweden", "Ireland",
    "New Zealand", "Mexico", "South Africa"
]

# ── Helpers ────────────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_resume(file_path: str) -> dict:
    """Extract structured data from a resume file."""
    if not RESUME_PARSER_AVAILABLE:
        return {
            "name": None,
            "email": None,
            "skills": [],
            "experience": None,
            "designation": None,
            "companies": [],
            "college": None,
            "degree": None,
            "_note": "pyresparser not installed — install spacy model for full parsing",
        }
    try:
        data = ResumeParser(file_path).get_extracted_data()
        # Normalise None → safe defaults
        return {
            "name": data.get("name"),
            "email": data.get("email"),
            "skills": data.get("skills") or [],
            "experience": data.get("total_experience"),
            "designation": data.get("designation"),
            "companies": data.get("company_names") or [],
            "college": data.get("college_name"),
            "degree": data.get("degree"),
        }
    except Exception as exc:
        print(f"[ERROR] Resume parsing failed: {exc}")
        return {
            "name": None,
            "email": None,
            "skills": [],
            "experience": None,
            "designation": None,
            "companies": [],
            "college": None,
            "degree": None,
            "_error": str(exc),
        }


def search_jobs_globally(
    search_term: str,
    location: str = "",
    countries: list[str] | None = None,
    results_per_source: int = 10,
    hours_old: int = 168,
) -> list[dict]:
    """
    Search across LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter & more.
    Falls back gracefully if JobSpy is missing.
    """
    if not JOBSPY_AVAILABLE:
        return _mock_job_results(search_term, location)

    if not countries:
        countries = ["USA"]

    all_jobs = []
    seen_urls: set[str] = set()

    for country in countries:
        try:
            raw = scrape_jobs(
                site_name=[
                    "linkedin",
                    "indeed",
                    "glassdoor",
                    "google",
                    "zip_recruiter",
                ],
                search_term=search_term,
                location=location,
                results_wanted=results_per_source,
                hours_old=hours_old,
                country_indeed=country,
                linkedin_fetch_description=True,
            )
        except Exception as exc:
            print(f"[WARN] JobSpy failed for country={country}: {exc}")
            continue

        if raw is None or (hasattr(raw, "empty") and raw.empty):
            continue

        # Convert DataFrame rows → dicts, deduplicate by URL
        for _, row in raw.iterrows():
            job_dict = row.to_dict()
            url = str(job_dict.get("job_url", ""))
            if url and url not in seen_urls:
                seen_urls.add(url)
                job_dict["_source_country"] = country
                all_jobs.append(job_dict)

        # Respect rate limits
        import time
        time.sleep(0.5)

    return all_jobs


def _mock_job_results(search_term: str, location: str) -> list[dict]:
    """Fallback mock data when JobSpy is unavailable (for demo purposes)."""
    return [
        {
            "title": f"{search_term} — Senior Developer",
            "company": "TechCorp Global",
            "company_url": "https://example.com/techcorp",
            "job_url": "https://linkedin.com/jobs/view/1",
            "location": location or "San Francisco, CA",
            "country": "USA",
            "is_remote": True,
            "description": f"We are looking for a talented {search_term} to join our team…",
            "job_type": "fulltime",
            "salary_source": "estimated",
            "min_amount": 120000,
            "max_amount": 180000,
            "currency": "USD",
            "date_posted": "2026-06-28",
            "site": "linkedin",
        },
        {
            "title": f"{search_term} — Full Stack Engineer",
            "company": "InnovateAI",
            "company_url": "https://example.com/innovate",
            "job_url": "https://indeed.com/viewjob?jk=abc123",
            "location": location or "Remote",
            "country": "USA",
            "is_remote": True,
            "description": f"InnovateAI is hiring a {search_term} to build next-gen platforms…",
            "job_type": "fulltime",
            "salary_source": "estimated",
            "min_amount": 130000,
            "max_amount": 200000,
            "currency": "USD",
            "date_posted": "2026-06-27",
            "site": "indeed",
        },
        {
            "title": f"{search_term} — Machine Learning Engineer",
            "company": "DataFlow Systems",
            "company_url": "https://example.com/dataflow",
            "job_url": "https://glassdoor.com/job/456",
            "location": location or "New York, NY",
            "country": "USA",
            "is_remote": False,
            "description": f"Join DataFlow as a {search_term} working on cutting-edge ML pipelines…",
            "job_type": "fulltime",
            "salary_source": "estimated",
            "min_amount": 140000,
            "max_amount": 210000,
            "currency": "USD",
            "date_posted": "2026-06-26",
            "site": "glassdoor",
        },
        {
            "title": f"{search_term} — Cloud Architect",
            "company": "NexGen Cloud",
            "company_url": "https://example.com/nexgen",
            "job_url": "https://googlejobs.com/789",
            "location": location or "Seattle, WA",
            "country": "USA",
            "is_remote": True,
            "description": f"NexGen Cloud needs a {search_term} to design scalable cloud solutions…",
            "job_type": "contract",
            "salary_source": "estimated",
            "min_amount": 150000,
            "max_amount": 220000,
            "currency": "USD",
            "date_posted": "2026-06-25",
            "site": "google",
        },
    ]


def build_search_queries_from_resume(resume_data: dict) -> list[str]:
    """
    Generate smart search queries from resume data.
    Uses designation, skills, and extracted experience.
    """
    queries = set()

    # 1. Try the designation / current title
    designation = resume_data.get("designation")
    if designation and isinstance(designation, str) and len(designation) > 2:
        queries.add(designation.strip())

    # 2. Skills-based queries
    skills = resume_data.get("skills") or []
    if skills:
        # Top 3 skills as a compound query
        top_skills = skills[:3]
        queries.add(" ".join(top_skills))

        # Individual skill-based searches
        for skill in skills[:5]:
            queries.add(skill)
            queries.add(f"{skill} developer")
            queries.add(f"{skill} engineer")

    # 3. Past companies → "ex-{company}" searches
    companies = resume_data.get("companies") or []
    for company in companies[:3]:
        queries.add(company.strip())

    # 4. College / degree
    degree = resume_data.get("degree")
    college = resume_data.get("college")
    if degree and isinstance(degree, str):
        queries.add(f"{degree} graduate")
    if college and isinstance(college, str):
        queries.add(f"{college} alumni")

    # 5. Generic fallback from designation or experience
    exp = resume_data.get("experience")
    if exp and isinstance(exp, (int, float)) and exp > 0:
        level = "senior" if exp >= 5 else "mid-level" if exp >= 2 else "junior"
        queries.add(f"{level} software engineer")
    else:
        queries.add("software engineer")
        queries.add("full stack developer")

    # Filter out very short / noisy entries
    return [q for q in queries if len(q) >= 3]


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/parse-resume", methods=["POST"])
def api_parse_resume():
    """Upload & parse a resume file → structured JSON."""
    if "resume" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid file type. Use PDF, DOCX, or TXT."}), 400

    filename = secure_filename(file.filename)

    # Save to temp location
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix)
    file.save(tmp.name)
    tmp.close()

    try:
        parsed = parse_resume(tmp.name)
        return jsonify({"success": True, "data": parsed})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        os.unlink(tmp.name)


@app.route("/api/search-jobs", methods=["POST"])
def api_search_jobs():
    """
    Accept either:
      - JSON body with { "query": "...", "location": "...", "countries": [...] }
      - JSON body with { "resume_data": {...} } (auto-generates queries)
    Returns unified job listings.
    """
    body = request.get_json(force=True)
    if not body:
        return jsonify({"success": False, "error": "Request body required"}), 400

    # Determine search queries
    queries: list[str] = []
    location = body.get("location", "")
    countries = body.get("countries") or ["USA"]
    custom_query = body.get("query", "").strip()

    if custom_query:
        queries = [custom_query]
    elif "resume_data" in body:
        resume_data = body["resume_data"]
        queries = build_search_queries_from_resume(resume_data)
        # If no location from resume, use a default
        if not location:
            location = "Remote"
    else:
        return jsonify({"success": False, "error": "Provide 'query' or 'resume_data'"}), 400

    # Limit queries to avoid rate-limit hammering
    queries = queries[:5]

    all_jobs: list[dict] = []
    seen_job_urls: set[str] = set()

    for query in queries:
        try:
            results = search_jobs_globally(
                search_term=query,
                location=location,
                countries=countries,
                results_per_source=8,
                hours_old=168,  # 7 days
            )
        except Exception as exc:
            print(f"[ERROR] search_jobs_globally failed for query={query}: {exc}")
            continue

        for job in results:
            url = job.get("job_url") or job.get("url", "")
            if url and url not in seen_job_urls:
                seen_job_urls.add(url)
                all_jobs.append(job)

        # Small delay between query rotations
        import time
        time.sleep(0.3)

    # Sort by date posted (newest first)
    all_jobs.sort(key=lambda j: str(j.get("date_posted", "")), reverse=True)

    return jsonify({
        "success": True,
        "queries_used": queries,
        "total_jobs": len(all_jobs),
        "jobs": all_jobs[:100],  # cap at 100 results
    })


@app.route("/api/countries", methods=["GET"])
def api_countries():
    """Return the list of supported countries."""
    return jsonify({"success": True, "countries": SUPPORTED_COUNTRIES})


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "ok",
        "resume_parser": RESUME_PARSER_AVAILABLE,
        "jobspy": JOBSPY_AVAILABLE,
        "version": "1.0.0",
    })


# ── Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
