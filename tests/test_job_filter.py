import pytest
from filters.job_filter import passes_exclusion_filter, extract_visa_signals, filter_jobs


def _job(title="ML Engineer", description=""):
    return {"title": title, "company": "Test Co", "description": description}


def test_excludes_citizenship_required():
    job = _job(description="Must be a US Citizen to apply")
    assert not passes_exclusion_filter(job)


def test_excludes_security_clearance():
    job = _job(description="Active Top Secret/SCI clearance required")
    assert not passes_exclusion_filter(job)


def test_excludes_no_sponsorship():
    job = _job(description="We will not sponsor visas for this role")
    assert not passes_exclusion_filter(job)


def test_excludes_senior_years():
    job = _job(description="10+ years of software engineering experience required")
    assert not passes_exclusion_filter(job)


def test_passes_normal_ml_job():
    job = _job(description="2+ years of experience with PyTorch and LLMs. Entry level welcome.")
    assert passes_exclusion_filter(job)


def test_extracts_visa_signals():
    job = _job(description="Open to OPT candidates. Entry level position. H1B sponsorship available.")
    signals = extract_visa_signals(job)
    assert "opt" in signals
    assert "entry level" in signals


def test_no_signals_generic_job():
    job = _job(description="Work on distributed systems with Go and Kubernetes.")
    signals = extract_visa_signals(job)
    assert signals == []


def test_filter_jobs_mixed():
    jobs = [
        _job("ML Engineer", "entry level llm pytorch opt sponsorship"),
        _job("Senior ML", "10+ years experience security clearance"),
        _job("AI Engineer", "0-2 years experience pytorch"),
    ]
    results = filter_jobs(jobs)
    assert len(results) == 2
    titles = [j["title"] for j in results]
    assert "Senior ML" not in titles


def test_filter_attaches_visa_signals():
    jobs = [_job("AI Engineer", "opt entry level sponsorship available")]
    results = filter_jobs(jobs)
    assert len(results) == 1
    assert len(results[0]["visa_signals"]) > 0
