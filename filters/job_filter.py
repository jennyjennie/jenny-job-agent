from config.keywords import EXCLUDE_TITLE_PHRASES, EXCLUDE_PHRASES, EXCLUDE_COMPANY_PHRASES, VISA_POSITIVE_SIGNALS


def passes_exclusion_filter(job: dict) -> tuple[bool, str]:
    """Returns (passes, reason). reason is non-empty when excluded."""
    title = (job.get("title", "") or "").lower()
    company = (job.get("company", "") or "").lower()
    description = (job.get("description", "") or "").lower()
    fulltext = title + " " + description

    for phrase in EXCLUDE_TITLE_PHRASES:
        if phrase in title:
            return False, f"title contains '{phrase}'"

    for phrase in EXCLUDE_PHRASES:
        if phrase in fulltext:
            return False, f"text contains '{phrase}'"

    for phrase in EXCLUDE_COMPANY_PHRASES:
        if phrase in company:
            return False, f"company contains '{phrase}'"

    return True, ""


def extract_visa_signals(job: dict) -> list[str]:
    fulltext = ((job.get("title", "") or "") + " " + (job.get("description", "") or "")).lower()
    return [signal for signal in VISA_POSITIVE_SIGNALS if signal in fulltext]


def filter_jobs(jobs: list[dict], verbose: bool = False) -> list[dict]:
    results = []
    excluded = 0
    for job in jobs:
        passes, reason = passes_exclusion_filter(job)
        if not passes:
            if verbose:
                print(f"  [Filter] EXCLUDED: {job.get('title')} @ {job.get('company')} — {reason}")
            excluded += 1
            continue
        job["visa_signals"] = extract_visa_signals(job)
        results.append(job)
    print(f"[Filter] {len(jobs)} jobs in → {len(results)} pass ({excluded} excluded)")
    return results
