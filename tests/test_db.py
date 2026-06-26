import os
import pytest
from database.db import JobDatabase

DB_PATH = "data/test_jobs.db"


@pytest.fixture(autouse=True)
def clean_db():
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


@pytest.fixture
def db():
    return JobDatabase(DB_PATH)


def _sample_job(**overrides) -> dict:
    base = {
        "url": "https://example.com/job/1",
        "title": "ML Engineer",
        "company": "Acme AI",
        "location": "Remote",
        "description": "Work on LLMs with PyTorch",
        "date_posted": "2026-06-26",
        "source": "linkedin",
        "is_remote": True,
        "visa_signals": ["entry level", "opt"],
    }
    base.update(overrides)
    return base


def test_insert_and_exists(db):
    job = _sample_job()
    job_id = db.insert_job(job)
    assert job_id is not None
    assert db.job_exists(job["url"], job["title"], job["company"])


def test_dedup_by_url(db):
    job = _sample_job()
    id1 = db.insert_job(job)
    id2 = db.insert_job(job)  # same URL → INSERT OR IGNORE
    assert id1 is not None
    assert id2 is None


def test_dedup_by_title_company(db):
    job1 = _sample_job(url="https://example.com/job/1")
    job2 = _sample_job(url="https://example.com/job/2")  # different URL, same title+company
    id1 = db.insert_job(job1)
    id2 = db.insert_job(job2)
    assert id1 is not None
    assert id2 is None


def test_update_scores(db):
    job_id = db.insert_job(_sample_job())
    scores = {
        "skill_match": 8.5,
        "visa_friendly": 7.0,
        "relevance": 9.0,
        "competition": 4.0,
        "overall": 8.1,
        "jd_summary": "ML role with LLMs",
        "recommendation": "Strong match. Apply.",
    }
    db.update_scores(job_id, scores)
    rows = db.get_todays_email_queue(min_score=5.0)
    assert len(rows) == 1
    assert abs(rows[0]["overall_score"] - 8.1) < 0.01


def test_mark_emailed(db):
    job_id = db.insert_job(_sample_job())
    db.update_scores(job_id, {"skill_match": 8, "visa_friendly": 8, "relevance": 8,
                               "competition": 3, "overall": 8.0,
                               "jd_summary": "...", "recommendation": "Apply"})
    queue = db.get_todays_email_queue(min_score=5.0)
    assert len(queue) == 1
    db.mark_emailed([job_id])
    queue_after = db.get_todays_email_queue(min_score=5.0)
    assert len(queue_after) == 0


def test_min_score_filter(db):
    job_id = db.insert_job(_sample_job())
    db.update_scores(job_id, {"skill_match": 3, "visa_friendly": 3, "relevance": 3,
                               "competition": 8, "overall": 3.0,
                               "jd_summary": "...", "recommendation": "Skip"})
    queue = db.get_todays_email_queue(min_score=5.5)
    assert len(queue) == 0
