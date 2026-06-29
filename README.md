# Jobspray
This is application to search the jobs and apply automatically

# 🌌 GalaxyJob — Open Source AI Job Aggregator

> **Search all job platforms worldwide from a single, beautiful interface.**  
> Upload your resumé → AI parses your skills → searches LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter & more — across 60+ countries — for free.

![Galaxy UI](https://img.shields.io/badge/UI-Galaxy_Blue_%26_Orange-2b5fd9?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
[![Deploy to Render](https://img.shields.io/badge/Deploy_to-Render-46E3B7?style=flat-square)](https://render.com/deploy)

---

## ✨ Features

- **🤖 AI-Powered Resume Parsing** — Upload PDF/DOCX/TXT; extracts name, email, skills, experience, designation, companies, degree, college
- **🌍 Global Job Search** — Scrapes LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Bayt, Naukri & more across 60+ countries
- **🧠 Smart Query Generation** — Auto-generates search queries from your resume (skills, title, past companies, experience level)
- **🎨 Stunning Galaxy UI** — Deep blue space background with animated stars + white & orange nebula clouds
- **🔒 100% Free & Open Source** — No API keys required, no paid tiers, MIT licensed
- **🚀 Free Deployment** — Ready for Render, Railway, or any Python PaaS (free tier)

## 🖥️ Demo

| Step | Screenshot |
|------|-----------|
| 1. Upload resume → parsed instantly | Skills, experience, designation extracted |
| 2. Choose countries | Select from 20+ countries (USA, UK, Canada, India, Germany, etc.) |
| 3. Click search | Aggregates jobs from all platforms |
| 4. Browse results | Click any job card to open application link |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11 + Flask 3.1 |
| **Job Scraper** | [JobSpy](https://github.com/speedyapply/JobSpy) (LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter, Bayt, Naukri, BDJobs) |
| **Resume Parser** | [pyresparser](https://github.com/OmkarPathak/pyresparser) (NLP-based extraction) |
| **Frontend** | Vanilla HTML/CSS/JS — zero framework dependencies |
| **Deployment** | Gunicorn + Render/Railway free tier |

## 📦 Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/yourusername/galaxyjob.git
cd galaxyjob

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download NLP model (for resume parsing)
python -m spacy download en_core_web_sm

# 5. Run
python app.py

# Open http://localhost:5000
