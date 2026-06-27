import pytest
from filters.job_filter import passes_exclusion_filter, extract_visa_signals, filter_jobs


def _job(title="ML Engineer", description="", company="Test Co"):
    return {"title": title, "company": company, "description": description}


def _passes(job):
    ok, _ = passes_exclusion_filter(job)
    return ok


def test_excludes_citizenship_required():
    assert not _passes(_job(description="Must be a US Citizen to apply"))


def test_excludes_security_clearance():
    assert not _passes(_job(description="Active Top Secret/SCI clearance required"))


def test_excludes_no_sponsorship():
    assert not _passes(_job(description="We will not sponsor visas for this role"))


def test_excludes_senior_years():
    assert not _passes(_job(description="10+ years of software engineering experience required"))


def test_excludes_five_plus_years():
    assert not _passes(_job(description="Requires 5+ years of ML experience"))


def test_excludes_senior_title():
    assert not _passes(_job(title="Senior ML Engineer"))


def test_excludes_lead_title():
    assert not _passes(_job(title="Lead Data Scientist"))


def test_excludes_staff_title():
    assert not _passes(_job(title="Staff Software Engineer"))


def test_excludes_director_title():
    assert not _passes(_job(title="Director of Machine Learning"))


def test_excludes_staffing_company():
    assert not _passes(_job(company="AgileGrid Solutions"))

def test_excludes_recruiting_company():
    assert not _passes(_job(company="CodeGeniusRecruit LLC"))

def test_passes_solutions_in_description_not_company():
    # "solutions" only blocked in company name, not description
    assert _passes(_job(company="Anthropic", description="build ML solutions for enterprise"))

def test_senior_in_description_does_not_exclude():
    # "senior" only blocked in title, not description
    assert _passes(_job(title="ML Engineer", description="You will work alongside senior engineers"))


def test_passes_normal_ml_job():
    assert _passes(_job(description="2+ years of experience with PyTorch and LLMs. Entry level welcome."))


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
        _job("Senior ML Engineer", "10+ years experience security clearance"),
        _job("AI Engineer", "0-2 years experience pytorch"),
        _job("Lead Data Scientist", "great role"),
    ]
    results = filter_jobs(jobs)
    assert len(results) == 2
    titles = [j["title"] for j in results]
    assert "Senior ML Engineer" not in titles
    assert "Lead Data Scientist" not in titles


def test_filter_attaches_visa_signals():
    jobs = [_job("AI Engineer", "opt entry level sponsorship available")]
    results = filter_jobs(jobs)
    assert len(results) == 1
    assert len(results[0]["visa_signals"]) > 0
