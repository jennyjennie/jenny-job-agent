import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class JobDatabase:
    def __init__(self, db_path: str = "data/jobs.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        schema_path = Path(__file__).parent / "schema.sql"
        sql = schema_path.read_text()
        self._conn.executescript(sql)
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ── Deduplication ────────────────────────────────────────────────────────

    def job_exists(self, url: str, title: str, company: str) -> bool:
        row = self._conn.execute(
            "SELECT id FROM jobs WHERE url = ? OR (title = ? AND company = ?)",
            (url, title, company),
        ).fetchone()
        return row is not None

    # ── Insert ────────────────────────────────────────────────────────────────

    def insert_job(self, job: dict) -> int | None:
        now = datetime.now(timezone.utc).isoformat()
        visa_signals = json.dumps(job.get("visa_signals", []))
        try:
            cur = self._conn.execute(
                """
                INSERT OR IGNORE INTO jobs
                    (url, title, company, location, description, date_posted,
                     salary_min, salary_max, is_remote, source,
                     visa_signals, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.get("url", ""),
                    job.get("title", ""),
                    job.get("company", ""),
                    job.get("location", ""),
                    job.get("description", ""),
                    job.get("date_posted", ""),
                    job.get("salary_min"),
                    job.get("salary_max"),
                    1 if job.get("is_remote") else 0,
                    job.get("source", ""),
                    visa_signals,
                    now,
                ),
            )
            self._conn.commit()
            return cur.lastrowid if cur.rowcount > 0 else None
        except sqlite3.Error as e:
            print(f"[DB] Insert error for {job.get('title')} @ {job.get('company')}: {e}")
            return None

    # ── Scoring ───────────────────────────────────────────────────────────────

    def update_scores(self, job_id: int, scores: dict):
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE jobs SET
                skill_match_score   = ?,
                visa_friendly_score = ?,
                relevance_score     = ?,
                competition_score   = ?,
                overall_score       = ?,
                jd_summary          = ?,
                recommendation      = ?,
                scored_at           = ?
            WHERE id = ?
            """,
            (
                scores.get("skill_match"),
                scores.get("visa_friendly"),
                scores.get("relevance"),
                scores.get("competition"),
                scores.get("overall"),
                scores.get("jd_summary", ""),
                scores.get("recommendation", ""),
                now,
                job_id,
            ),
        )
        self._conn.commit()

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_todays_unscored_jobs(self) -> list[dict]:
        today = datetime.now(timezone.utc).date().isoformat()
        rows = self._conn.execute(
            """
            SELECT * FROM jobs
            WHERE scraped_at >= ? AND scored_at IS NULL
            ORDER BY scraped_at DESC
            """,
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_todays_email_queue(self, min_score: float = 5.5) -> list[dict]:
        today = datetime.now(timezone.utc).date().isoformat()
        rows = self._conn.execute(
            """
            SELECT * FROM jobs
            WHERE scraped_at >= ?
              AND emailed = 0
              AND overall_score >= ?
            ORDER BY overall_score DESC
            """,
            (today, min_score),
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_emailed(self, job_ids: list[int]):
        if not job_ids:
            return
        placeholders = ",".join("?" * len(job_ids))
        self._conn.execute(
            f"UPDATE jobs SET emailed = 1 WHERE id IN ({placeholders})", job_ids
        )
        self._conn.commit()

    # ── Coffee chat ───────────────────────────────────────────────────────────

    def insert_coffee_chat_target(self, target: dict) -> int | None:
        now = datetime.now(timezone.utc).isoformat()
        try:
            cur = self._conn.execute(
                """
                INSERT OR IGNORE INTO coffee_chat_targets
                    (name, title, company, linkedin_url, school,
                     connection_type, personalized_message, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target.get("name", ""),
                    target.get("title", ""),
                    target.get("company", ""),
                    target.get("linkedin_url", ""),
                    target.get("school", ""),
                    target.get("connection_type", ""),
                    target.get("personalized_message", ""),
                    now,
                ),
            )
            self._conn.commit()
            return cur.lastrowid if cur.rowcount > 0 else None
        except sqlite3.Error as e:
            print(f"[DB] Coffee chat insert error: {e}")
            return None

    # ── Resume tailor ─────────────────────────────────────────────────────────

    def insert_tailored_resume(self, result: dict) -> int | None:
        now = datetime.now(timezone.utc).isoformat()
        try:
            cur = self._conn.execute(
                """
                INSERT INTO tailored_resumes
                    (job_id, job_title, company, missing_keywords,
                     tailored_bullets, papers_to_highlight,
                     summary_suggestion, output_file, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.get("job_id"),
                    result.get("job_title", ""),
                    result.get("company", ""),
                    json.dumps(result.get("missing_keywords", [])),
                    json.dumps(result.get("tailored_bullets", [])),
                    json.dumps(result.get("papers_to_highlight", [])),
                    result.get("summary_suggestion", ""),
                    result.get("output_file", ""),
                    now,
                ),
            )
            self._conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"[DB] Tailored resume insert error: {e}")
            return None

    # ── Email log ─────────────────────────────────────────────────────────────

    def log_email_sent(self, jobs_count: int, status: str, email_to: str = ""):
        now = datetime.now(timezone.utc).isoformat()
        github_run_id = os.environ.get("GITHUB_RUN_ID", "")
        self._conn.execute(
            """
            INSERT INTO email_log (sent_at, jobs_included, email_to, github_run_id, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (now, jobs_count, email_to, github_run_id, status),
        )
        self._conn.commit()
