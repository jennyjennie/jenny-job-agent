#!/usr/bin/env python3
"""Workflow 1: Daily Job Hunter — scrape, filter, dedup, score, email.

Usage:
  python scripts/run_job_hunter.py           # full run
  python scripts/run_job_hunter.py --test    # 1 keyword × 1 location, then email
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from config.keywords import SEARCH_KEYWORDS, LOCATIONS
from scrapers.job_scraper import scrape_all_jobs
from filters.job_filter import filter_jobs
from database.db import JobDatabase
from agents.job_scorer import score_jobs_batch
from agents.email_report_agent import run_daily_report

TEST_KEYWORDS = SEARCH_KEYWORDS[:1]   # ML Engineer only
TEST_LOCATIONS = ["San Francisco, CA"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Quick test: 3 keywords × 1 location")
    args = parser.parse_args()

    settings = Settings()
    test_mode = args.test

    print("=" * 60)
    print(f"Daily Job Hunter starting{'  [TEST MODE]' if test_mode else ''}")
    if test_mode:
        print(f"  Keywords : {TEST_KEYWORDS}")
        print(f"  Locations: {TEST_LOCATIONS} (1 combo, remote pass skipped)")
    print("=" * 60)

    # Step 1: Scrape
    print("\n[Step 1] Scraping jobs...")
    raw_jobs = scrape_all_jobs(
        settings,
        keywords_override=TEST_KEYWORDS if test_mode else None,
        locations_override=TEST_LOCATIONS if test_mode else None,
        scrape_remote_override=False if test_mode else None,
    )
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
        print("\nNo new jobs to score.")
    else:
        # Step 4: Score with Claude
        print(f"\n[Step 4] Scoring {len(new_jobs)} jobs with Claude...")
        scored_results = score_jobs_batch(new_jobs, settings)

        # Step 5: Write scores back to DB
        print("\n[Step 5] Writing scores to database...")
        scored_count = 0
        with JobDatabase(settings.database_path) as db:
            for job, scores in scored_results:
                job_id = job.get("_db_id")
                if job_id:
                    db.update_scores(job_id, scores)
                    scored_count += 1

        print(f"\n[Step 5 done] {scored_count}/{len(new_jobs)} jobs scored and saved.")

    # Step 6: Send email report (always runs — picks up all unsent jobs in DB)
    # Skipped in CI (GitHub Actions runs run_email_report.py as a separate step).
    # Set SEND_EMAIL_AFTER_HUNT=0 to suppress locally too.
    if os.environ.get("SEND_EMAIL_AFTER_HUNT", "1") == "1":
        print(f"\n{'=' * 60}")
        print("[Step 6] Sending email report...")
        print("=" * 60)
        run_daily_report(settings)
    else:
        print("\n[Step 6] Skipped (SEND_EMAIL_AFTER_HUNT=0).")


if __name__ == "__main__":
    main()
