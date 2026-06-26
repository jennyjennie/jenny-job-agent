import json
import os
from datetime import datetime, timezone
from pathlib import Path
import jinja2

from config.settings import Settings
from database.db import JobDatabase
from mailer.sender import send_email


def _load_env(name: str, template_dir: Path) -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=(name == "html"),
    )
    # Custom filter: parse JSON strings stored in DB
    env.filters["fromjson"] = lambda s: json.loads(s) if s else []
    return env


def build_report(jobs: list[dict], settings: Settings) -> tuple[str, str]:
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
        jobs = db.get_todays_email_queue(settings.min_overall_score)
        jobs = jobs[: settings.max_jobs_per_email]

        if not jobs:
            print("[Report] No new scored jobs above threshold. Skipping email.")
            return

        print(f"[Report] Building report for {len(jobs)} jobs...")
        html_body, txt_body = build_report(jobs, settings)

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        subject = f"Jenny's Job Report — {date_str} — {len(jobs)} new jobs"

        success = send_email(
            to=settings.email_to,
            subject=subject,
            html=html_body,
            text=txt_body,
            settings=settings,
        )

        status = "sent" if success else "failed"
        db.log_email_sent(
            jobs_count=len(jobs),
            status=status,
            email_to=settings.email_to,
        )

        if success:
            db.mark_emailed([j["id"] for j in jobs])
            print(f"[Report] Email sent. {len(jobs)} jobs marked as emailed.")
        else:
            print("[Report] Email send failed. Jobs NOT marked as emailed (will retry tomorrow).")
