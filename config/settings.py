from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    anthropic_api_key: str = field(
        default_factory=lambda: os.environ["ANTHROPIC_API_KEY"]
    )
    claude_model: str = field(
        default_factory=lambda: os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    )

    gmail_user: str = field(
        default_factory=lambda: os.environ.get("GMAIL_USER", "jennyho0221@gmail.com")
    )
    gmail_app_password: str = field(
        default_factory=lambda: os.environ.get("GMAIL_APP_PASSWORD", "")
    )
    email_to: str = "jennyho0221@gmail.com"
    email_from: str = field(
        default_factory=lambda: os.environ.get("GMAIL_USER", "jennyho0221@gmail.com")
    )

    database_path: str = field(
        default_factory=lambda: os.environ.get("DATABASE_PATH", "data/jobs.db")
    )
    resume_path: str = field(
        default_factory=lambda: os.environ.get("RESUME_PATH", "data/jennyho_base_resume.pdf")
    )
    resume_docx_path: str = field(
        default_factory=lambda: os.environ.get("RESUME_DOCX_PATH", "data/jennyho_base_resume.docx")
    )
    output_dir: str = "output"

    min_overall_score: float = field(
        default_factory=lambda: float(os.environ.get("MIN_OVERALL_SCORE", "5.5"))
    )
    max_jobs_per_email: int = field(
        default_factory=lambda: int(os.environ.get("MAX_JOBS_PER_EMAIL", "25"))
    )
