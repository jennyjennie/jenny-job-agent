import math
import time
from config.keywords import (
    SEARCH_KEYWORDS,
    LOCATIONS,
    JOB_SITES,
    RESULTS_PER_SITE,
    HOURS_OLD,
    SCRAPE_REMOTE,
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


def scrape_all_jobs(
    settings: Settings,
    keywords_override: list[str] | None = None,
    locations_override: list[str] | None = None,
    scrape_remote_override: bool | None = None,
) -> list[dict]:
    try:
        from jobspy import scrape_jobs as jobspy_scrape
    except ImportError:
        raise ImportError("Install python-jobspy: pip install python-jobspy")

    keywords = keywords_override if keywords_override is not None else SEARCH_KEYWORDS
    locations = locations_override if locations_override is not None else LOCATIONS
    do_remote = scrape_remote_override if scrape_remote_override is not None else SCRAPE_REMOTE

    all_jobs: list[dict] = []

    # Build the list of (label, jobspy_kwargs) combos to run
    combos: list[tuple[str, dict]] = []
    if do_remote:
        for keyword in keywords:
            combos.append((keyword, {"search_term": keyword, "is_remote": True}))
    for keyword in keywords:
        for location in locations:
            combos.append((keyword, {"search_term": keyword, "location": location}))

    for i, (keyword, kwargs) in enumerate(combos, 1):
        label = kwargs.get("location", "remote")
        print(f"[Scraper] [{i}/{len(combos)}] '{keyword}' in '{label}'")
        try:
            df = jobspy_scrape(
                site_name=JOB_SITES,
                results_wanted=RESULTS_PER_SITE,
                hours_old=HOURS_OLD,
                country_indeed="USA",
                linkedin_fetch_description=True,
                verbose=0,
                **kwargs,
            )
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                job = normalize_job(row.to_dict(), source=keyword)
                if job["title"] and job["company"] and job["url"]:
                    all_jobs.append(job)
            print(f"  → {len(df)} raw results")
            time.sleep(2)
        except Exception as e:
            print(f"  [Scraper] Error for '{keyword}' / '{label}': {e}")
            continue

    deduped = deduplicate_within_batch(all_jobs)
    print(f"[Scraper] Total: {len(all_jobs)} raw → {len(deduped)} after batch dedup")
    return deduped
