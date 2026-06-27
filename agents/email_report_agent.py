import json
import os
from datetime import datetime, timezone
from pathlib import Path
import jinja2

from config.settings import Settings
from database.db import JobDatabase
from mailer.sender import send_email

N_TAILOR = 5  # auto-tailor top N jobs by overall_score


def _load_env(name: str, template_dir: Path) -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=(name == "html"),
    )
    env.filters["fromjson"] = lambda s: json.loads(s) if s else []
    return env


def _run_resume_tailor(jobs: list[dict], settings: Settings) -> tuple[list[dict], list[str]]:
    """Tailor resume for the top N jobs.

    Returns:
        tailored_results: [{job, result}, ...] for email display
        docx_paths: list of .docx file paths to attach to email
    """
    from agents.resume_tailor import extract_resume_text, tailor_for_job, save_output, build_docx

    resume_path = settings.resume_path
    if not Path(resume_path).exists():
        print(f"[Tailor] Resume PDF not found at {resume_path} — skipping")
        return [], []

    print(f"[Tailor] Reading resume from {resume_path}...")
    try:
        resume_text = extract_resume_text(resume_path)
    except Exception as e:
        print(f"[Tailor] Failed to read PDF: {e}")
        return [], []

    top_jobs = jobs[:N_TAILOR]
    print(f"[Tailor] Tailoring for top {len(top_jobs)} jobs...")

    tailored_results = []
    docx_paths = []
    for i, job in enumerate(top_jobs, 1):
        label = f"{job.get('title')} @ {job.get('company')}"
        print(f"[Tailor] [{i}/{len(top_jobs)}] {label}")
        try:
            result = tailor_for_job(resume_text, job, settings)
            save_output(result, job, settings.output_dir)
            tailored_results.append({"job": job, "result": result})
            print(f"[Tailor]   → {len(result.get('tailored_bullets', []))} bullets")

            docx_path = build_docx(result, job, settings.output_dir, template_path=settings.resume_docx_path)
            if docx_path:
                docx_paths.append(docx_path)
                print(f"[Tailor]   → .docx saved: {Path(docx_path).name}")
            else:
                print(f"[Tailor]   → .docx skipped (no resume_sections in response)")
        except Exception as e:
            print(f"[Tailor]   → Failed: {e}")
            continue

    return tailored_results, docx_paths


def build_report(
    jobs: list[dict],
    settings: Settings,
    tailored_results: list[dict] | None = None,
) -> tuple[str, str]:
    template_dir = Path(__file__).parent.parent / "mailer" / "templates"
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    github_run_id = os.environ.get("GITHUB_RUN_ID", "")

    high_score_count = sum(1 for j in jobs if (j.get("overall_score") or 0) >= 8)
    visa_friendly_count = sum(
        1 for j in jobs if json.loads(j.get("visa_signals") or "[]")
    )
    top_score = max((j.get("overall_score") or 0) for j in jobs) if jobs else 0

    context = {
        "jobs": jobs,
        "tailored_results": tailored_results or [],
        "date": date_str,
        "github_run_id": github_run_id,
        "high_score_count": high_score_count,
        "visa_friendly_count": visa_friendly_count,
        "top_score": f"{top_score:.1f}",
    }

    html_env = _load_env("html", template_dir)
    txt_env = _load_env("txt", template_dir)

    html_body = html_env.get_template("daily_report.html").render(**context)
    txt_body = txt_env.get_template("daily_report.txt").render(**context)
    return html_body, txt_body


def run_daily_report(settings: Settings):
    with JobDatabase(settings.database_path) as db:
        all_today = db.get_todays_email_queue(min_score=0)
        jobs = [j for j in all_today if (j.get("overall_score") or 0) >= settings.min_overall_score]
        jobs = jobs[: settings.max_jobs_per_email]

        print(f"[Report] Jobs in today's DB queue (any score) : {len(all_today)}")
        print(f"[Report] Score threshold                       : {settings.min_overall_score}")
        print(f"[Report] Jobs above threshold (will email)     : {len(jobs)}")
        if all_today and not jobs:
            scores = [j.get("overall_score") or 0 for j in all_today]
            print(f"[Report] Score range in DB: {min(scores):.1f} – {max(scores):.1f}")
            print("[Report] All jobs are below threshold — lower MIN_OVERALL_SCORE in .env to test")

        if not jobs:
            print("[Report] Nothing to send. Skipping email.")
            return

        # Resume tailoring for top N jobs
        print(f"\n[Report] Running resume tailor for top {min(N_TAILOR, len(jobs))} jobs...")
        tailored_results, docx_paths = _run_resume_tailor(jobs, settings)
        print(f"[Report] Tailoring done: {len(tailored_results)}/{min(N_TAILOR, len(jobs))} succeeded, {len(docx_paths)} .docx built\n")

        print(f"[Report] Building report for {len(jobs)} jobs...")
        html_body, txt_body = build_report(jobs, settings, tailored_results=tailored_results)

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        subject = (
            f"Jenny's Job Report — {date_str} — {len(jobs)} jobs"
            + (f" + {len(docx_paths)} tailored resumes" if docx_paths else "")
        )

        success = send_email(
            to=settings.email_to,
            subject=subject,
            html=html_body,
            text=txt_body,
            settings=settings,
            attachments=docx_paths or None,
        )

        status = "sent" if success else "failed"
        db.log_email_sent(
            jobs_count=len(jobs),
            status=status,
            email_to=settings.email_to,
        )

        if success:
            db.mark_emailed([j["id"] for j in jobs])
            print(f"[Report] Email sent. {len(jobs)} jobs, {len(tailored_results)} tailored resumes, {len(docx_paths)} .docx attachments.")
        else:
            print("[Report] Email send failed. Jobs NOT marked as emailed (will retry tomorrow).")
