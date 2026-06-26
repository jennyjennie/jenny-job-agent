import math
import time
from config.keywords import (
    SEARCH_KEYWORDS,
    LOCATIONS,
    JOB_SITES,
    RESULTS_PER_SITE,
    HOURS_OLD,
)
from config.settings import Settings


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _safe_str(val) -> str:
    if val is None:
        return ""
    s = str(val)
    return "" if s.lower() in ("nan", "none", "nat") else s


def normalize_job(raw: dict, source: str) -> dict:
    return {
        "url": _safe_str(raw.get("job_url")),
        "title": _safe_str(raw.get("title")),
        "company": _safe_str(raw.get("company")),
        "location": _safe_str(raw.get("location")),
        "description": _safe_str(raw.get("description")),
        "date_posted": _safe_str(raw.get("date_posted")),
        "salary_min": _safe_float(raw.get("min_amount")),
        "salary_max": _safe_float(raw.get("max_amount")),
        "is_remote": bool(raw.get("is_remote", False)),
        "source": source,
    }


def deduplicate_within_batch(jobs: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    result = []
    for job in jobs:
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key not in seen and job.get("url"):
            seen.add(key)
            result.append(job)
    return result


def scrape_all_jobs(settings: Settings) -> list[dict]:
    try:
        from jobspy import scrape_jobs as jobspy_scrape
    except ImportError:
        raise ImportError("Install python-jobspy: pip install python-jobspy")

    all_jobs: list[dict] = []
    total_combos = len(SEARCH_KEYWORDS) * len(LOCATIONS)
    done = 0

    for keyword in SEARCH_KEYWORDS:
        for location in LOCATIONS:
            done += 1
            print(f"[Scraper] [{done}/{total_combos}] '{keyword}' in '{location}'")
            try:
                df = jobspy_scrape(
                    site_name=JOB_SITES,
                    search_term=keyword,
                    location=location,
                    results_wanted=RESULTS_PER_SITE,
                    hours_old=HOURS_OLD,
                    country_indeed="USA",
                    linkedin_fetch_description=True,
                    verbose=0,
                )
                if df is None or df.empty:
                    continue
                for _, row in df.iterrows():
                    job = normalize_job(row.to_dict(), source=keyword)
                    if job["title"] and job["company"] and job["url"]:
                        all_jobs.append(job)
                print(f"  → {len(df)} raw results")
                time.sleep(2)  # polite delay between requests
            except Exception as e:
                print(f"  [Scraper] Error for '{keyword}' / '{location}': {e}")
                continue

    deduped = deduplicate_within_batch(all_jobs)
    print(f"[Scraper] Total: {len(all_jobs)} raw → {len(deduped)} after batch dedup")
    return deduped
