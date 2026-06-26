#!/usr/bin/env python3
"""Workflow 2: Resume Tailor — reads JD from env vars (set by GitHub Actions workflow_dispatch)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from agents.resume_tailor import extract_resume_text, tailor_for_job, save_output
from database.db import JobDatabase


def main():
    settings = Settings()

    # Inputs from workflow_dispatch or CLI env vars
    job = {
        "url": os.environ.get("JOB_URL", ""),
        "title": os.environ.get("JOB_TITLE", ""),
        "company": os.environ.get("COMPANY", ""),
        "description": os.environ.get("JOB_DESCRIPTION", ""),
        "location": os.environ.get("JOB_LOCATION", ""),
    }

    if not job["title"] or not job["company"]:
        print("Error: JOB_TITLE and COMPANY environment variables are required.")
        sys.exit(1)

    print("=" * 60)
    print(f"Resume Tailor: {job['title']} @ {job['company']}")
    print("=" * 60)

    print(f"\n[Step 1] Extracting resume text from {settings.resume_path}...")
    resume_text = extract_resume_text(settings.resume_path)
    print(f"  Extracted {len(resume_text)} characters")

    print("\n[Step 2] Generating tailored content with Claude...")
    result = tailor_for_job(resume_text, job, settings)

    print("\n[Step 3] Saving output...")
    output_path = save_output(result, job, settings.output_dir)
    print(f"  Saved to: {output_path}")

    print("\n[Step 4] Logging to database...")
    with JobDatabase(settings.database_path) as db:
        result["job_title"] = job["title"]
        result["company"] = job["company"]
        result["output_file"] = output_path
        db.insert_tailored_resume(result)

    print("\n--- Missing Keywords ---")
    for kw in result.get("missing_keywords", []):
        print(f"  - {kw}")

    print("\n--- Papers to Highlight ---")
    for p in result.get("papers_to_highlight", []):
        print(f"  - {p}")

    print("\n--- Summary Suggestion ---")
    print(result.get("summary_suggestion", ""))

    print("\n--- Tailored Bullets ---")
    for bullet in result.get("tailored_bullets", []):
        print(bullet)

    print(f"\nDone! Full output saved to: {output_path}")


if __name__ == "__main__":
    main()
