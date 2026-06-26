#!/usr/bin/env python3
"""Workflow 1: Daily Job Hunter — scrape, filter, dedup, score."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from scrapers.job_scraper import scrape_all_jobs
from filters.job_filter import filter_jobs
from database.db import JobDatabase
from agents.job_scorer import score_jobs_batch


def main():
    settings = Settings()

    print("=" * 60)
    print("Daily Job Hunter starting")
    print("=" * 60)

    # Step 1: Scrape
    print("\n[Step 1] Scraping jobs...")
    raw_jobs = scrape_all_jobs(settings)
    print(f"  Scraped {len(raw_jobs)} unique jobs")

    # Step 2: Pre-filter (no API cost)
    print("\n[Step 2] Filtering jobs...")
    filtered_jobs = filter_jobs(raw_jobs)

    # Step 3: Dedup against DB and insert new ones
    print("\n[Step 3] Deduplicating against database...")
    new_jobs = []
    new_job_ids = []
    with JobDatabase(settings.database_path) as db:
        for job in filtered_jobs:
            if not db.job_exists(job["url"], job["title"], job["company"]):
                job_id = db.insert_job(job)
                if job_id:
                    job["_db_id"] = job_id
                    new_jobs.append(job)
                    new_job_ids.append(job_id)
        print(f"  {len(new_jobs)} new jobs inserted (of {len(filtered_jobs)} filtered)")

    if not new_jobs:
        print("\nNo new jobs to score. Done.")
        return

    # Step 4: Score with Claude
    print(f"\n[Step 4] Scoring {len(new_jobs)} jobs with Claude...")
    scored_results = score_jobs_batch(new_jobs, settings)

    # Step 5: Write scores back to DB
    print("\n[Step 5] Writing scores to database...")
    scored_count = 0
    with JobDatabase(settings.database_path) as db:
        for job, scores in scored_results:
            job_id = job.get("_db_id")
            if job_id and scores:
                db.update_scores(job_id, scores)
                scored_count += 1

    print(f"\n{'=' * 60}")
    print(f"Done. {scored_count}/{len(new_jobs)} jobs scored and saved.")
    print("=" * 60)


if __name__ == "__main__":
    main()
