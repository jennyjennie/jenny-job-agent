from config.keywords import EXCLUDE_PHRASES, VISA_POSITIVE_SIGNALS


def _normalize(job: dict) -> str:
    title = job.get("title", "") or ""
    description = job.get("description", "") or ""
    return (title + " " + description).lower()


def passes_exclusion_filter(job: dict) -> bool:
    text = _normalize(job)
    for phrase in EXCLUDE_PHRASES:
        if phrase in text:
            return False
    return True


def extract_visa_signals(job: dict) -> list[str]:
    text = _normalize(job)
    return [signal for signal in VISA_POSITIVE_SIGNALS if signal in text]


def filter_jobs(jobs: list[dict]) -> list[dict]:
    results = []
    excluded = 0
    for job in jobs:
        if not passes_exclusion_filter(job):
            excluded += 1
            continue
        job["visa_signals"] = extract_visa_signals(job)
        results.append(job)
    print(f"[Filter] {len(jobs)} jobs in → {len(results)} pass ({excluded} excluded)")
    return results
