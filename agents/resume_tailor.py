import json
import re
from datetime import datetime, timezone
from pathlib import Path
import anthropic
import pdfplumber

from config.settings import Settings

_SYSTEM_PROMPT = """You are a resume expert helping Jenny Ho tailor her resume for a specific job.

Jenny's background:
- UCLA MEng AI (graduating Aug 2026), NYCU BS CS
- Key papers: NeurIPS 2024 first author "Stutter Makes Smarter" (small LLM self-improvement);
  ACL 2025 co-author (multimodal text recognition with LLMs)
- MediaTek Research: LLM training pipeline, 20% GPU cost reduction, evaluation dashboards
- Google Pixel team: Python automation, tooling, UI testing infrastructure
- Gamania: recommendation system with collaborative filtering
- Recent project: full-stack AI financial assistant using Claude API tool-calling
- Skills: Python, PyTorch, LLM fine-tuning, inference optimization, FastAPI, Docker

Your task:
1. Identify keywords in the JD that Jenny's resume is missing or underemphasizes
2. Generate 5-8 tailored bullet points that highlight Jenny's most relevant experiences
   - Lead with the NeurIPS/ACL papers when role is ML/research oriented
   - Lead with MediaTek LLM pipeline when role is ML engineering oriented
   - Lead with Google experience when role is software engineering / infra oriented
   - Use strong action verbs and include metrics where possible
3. Identify which of Jenny's papers/projects to highlight
4. Suggest a 2-3 sentence resume summary tailored to this specific role

Return ONLY valid JSON, no prose, no markdown fences:
{
  "missing_keywords": ["keyword1", "keyword2"],
  "tailored_bullets": [
    "• Action verb ... [metric] ...",
    "• Action verb ... [metric] ..."
  ],
  "papers_to_highlight": ["NeurIPS 2024 - Stutter Makes Smarter", "ACL 2025 - ..."],
  "summary_suggestion": "2-3 sentence resume summary here"
}"""


def extract_resume_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)


def tailor_for_job(resume_text: str, job: dict, settings: Settings) -> dict:
    title = job.get("title", "")
    company = job.get("company", "")
    description = (job.get("description", "") or "")[:5000]

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    user_prompt = f"""Target Role: {title} at {company}

Job Description:
{description}

Jenny's Current Resume:
{resume_text[:3000]}"""

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=1500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = response.content[0].text

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to extract JSON from response if there's surrounding text
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


def save_output(result: dict, job: dict, output_dir: str) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    company = re.sub(r"[^\w\s-]", "", job.get("company", "company")).strip().replace(" ", "_")
    title = re.sub(r"[^\w\s-]", "", job.get("title", "role")).strip().replace(" ", "_")[:40]
    filename = f"{company}_{title}_{date_str}.md"
    output_path = Path(output_dir) / "tailored_resumes" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Resume Tailoring: {job.get('title')} @ {job.get('company')}",
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"**URL:** {job.get('url', 'N/A')}",
        "",
        "## Missing Keywords to Add",
        "",
    ]
    for kw in result.get("missing_keywords", []):
        lines.append(f"- `{kw}`")

    lines += [
        "",
        "## Papers / Projects to Highlight",
        "",
    ]
    for paper in result.get("papers_to_highlight", []):
        lines.append(f"- {paper}")

    lines += [
        "",
        "## Suggested Resume Summary",
        "",
        result.get("summary_suggestion", ""),
        "",
        "## Tailored Bullet Points",
        "",
    ]
    for bullet in result.get("tailored_bullets", []):
        lines.append(bullet)

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return str(output_path)
