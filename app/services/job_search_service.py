import urllib.request
import json
import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.job import JobListing, JobPreference
from app.models.user import User


class JobSearchService:
    REJECT_KEYWORDS = ["senior", "sr.", "lead", "principal", "staff", "manager", "director", "architect", "5+ years", "7+ years", "10+ years"]

    @staticmethod
    def is_valid_url(url: str) -> bool:
        if not url or not isinstance(url, str):
            return False
        return url.startswith("http://") or url.startswith("https://")

    @staticmethod
    def is_quality_job(title: str, description: str, url: str) -> bool:
        if not JobSearchService.is_valid_url(url):
            return False
            
        combined = f"{title} {description}".lower()
        for kw in JobSearchService.REJECT_KEYWORDS:
            if kw in combined:
                return False
        return True

    @staticmethod
    def calculate_relevance_score(title: str, company: str, description: str, skills_str: str) -> float:
        score = 0.0
        combined = f"{title} {skills_str} {description}".lower()

        # 1. Role Tier Scoring
        if any(k in combined for k in ["machine learning", "ml engineer", "ai engineer", "python developer"]):
            score += 25.0
        elif any(k in combined for k in ["software engineer", "software developer", "backend developer", "full stack"]):
            score += 20.0
        elif any(k in combined for k in ["data analyst", "qa engineer", "data engineer"]):
            score += 15.0
        else:
            score += 10.0

        # 2. Fresher / Entry Level Scoring
        if any(k in combined for k in ["fresher", "entry level", "intern", "trainee", "graduate", "0-1 years", "0-2 years"]):
            score += 20.0

        # 3. Key Technical Skill Match
        if "python" in combined: score += 10.0
        if "machine learning" in combined or "ml" in combined: score += 15.0
        if "sql" in combined: score += 10.0
        if "dsa" in combined or "data structures" in combined: score += 10.0
        if "git" in combined: score += 5.0
        if "rest api" in combined or "fastapi" in combined or "django" in combined: score += 5.0

        # 4. Location & Remote Bonus
        if "remote" in combined or "india" in combined or "pune" in combined or "bengaluru" in combined:
            score += 10.0

        # Normalize score between 0.0 and 100.0
        return min(100.0, max(0.0, round(score, 1)))

    @staticmethod
    def generate_fingerprint(company: str, title: str, source_url: str) -> str:
        norm_company = re.sub(r"\W+", "", company.lower().strip())
        norm_title = re.sub(r"\W+", "", title.lower().strip())
        norm_url = source_url.lower().strip()
        raw_str = f"{norm_company}:{norm_title}:{norm_url}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def discover_and_ingest_jobs(self, db: Session, user: User) -> List[JobListing]:
        """
        Fetches live jobs from authentic APIs, filters quality jobs, calculates relevance score,
        and saves new listings with deduplication fingerprints into SQLite.
        """
        raw_listings = []

        # 1. Remotive Live API
        try:
            req = urllib.request.Request("https://remotive.com/api/remote-jobs?category=software-dev&limit=10", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("jobs", []):
                    raw_listings.append({
                        "title": item.get("title", ""),
                        "company": item.get("company_name", ""),
                        "location": item.get("candidate_required_location", "Remote"),
                        "remote": True,
                        "experience_level": "Fresher / Entry Level",
                        "skills": ", ".join(item.get("tags", ["Python", "Backend"])),
                        "description": item.get("description", "")[:500],
                        "source": "Remotive API",
                        "source_url": item.get("url", "")
                    })
        except Exception:
            pass

        # 2. RemoteOK Live API
        try:
            req = urllib.request.Request("https://remoteok.com/api?tag=python", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data[1:10]:
                    if isinstance(item, dict):
                        raw_listings.append({
                            "title": item.get("position", ""),
                            "company": item.get("company", ""),
                            "location": item.get("location", "Remote / Worldwide"),
                            "remote": True,
                            "experience_level": "Entry Level / Junior",
                            "skills": ", ".join(item.get("tags", ["Python", "Developer"])),
                            "description": item.get("description", "")[:500],
                            "source": "RemoteOK API",
                            "source_url": item.get("url", "")
                        })
        except Exception:
            pass

        ingested_jobs = []
        for j in raw_listings:
            title = j["title"]
            company = j["company"]
            url = j["source_url"]
            desc = j["description"]

            if not self.is_quality_job(title, desc, url):
                continue

            fp = self.generate_fingerprint(company, title, url)
            existing = db.query(JobListing).filter(
                (JobListing.fingerprint == fp) | (JobListing.duplicate_hash == fp)
            ).first()

            if not existing:
                rel_score = self.calculate_relevance_score(title, company, desc, j["skills"])
                job_rec = JobListing(
                    title=title,
                    company=company,
                    location=j["location"],
                    remote=j["remote"],
                    experience_level=j["experience_level"],
                    skills=j["skills"],
                    description=desc,
                    source=j["source"],
                    source_url=url,
                    discovered_at=datetime.now(timezone.utc),
                    relevance_score=rel_score,
                    duplicate_hash=fp,
                    fingerprint=fp,
                    status="active"
                )
                db.add(job_rec)
                ingested_jobs.append(job_rec)

        db.commit()
        return ingested_jobs

    def generate_daily_digest(self, db: Session, user: User, limit: int = 10) -> Dict[str, Any]:
        """
        Generates daily job digest of top quality job listings matched to user preferences.
        """
        self.discover_and_ingest_jobs(db, user)
        jobs = db.query(JobListing).filter(JobListing.status == "active").order_by(JobListing.relevance_score.desc()).limit(limit).all()

        return {
            "digest_date": datetime.now(timezone.utc).date().isoformat(),
            "target_applications": 5,
            "jobs_count": len(jobs),
            "jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "remote": j.remote,
                    "experience_level": j.experience_level,
                    "skills": j.skills,
                    "source": j.source,
                    "source_url": j.source_url,
                    "relevance_score": j.relevance_score
                }
                for j in jobs
            ]
        }

