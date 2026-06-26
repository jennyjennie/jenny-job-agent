import json
import time
import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from config.settings import Settings

_SYSTEM_PROMPT = """You are a career advisor helping Jenny Ho evaluate job postings.

Jenny's profile:
- UCLA MEng AI (graduating Aug 2026), NYCU BS CS
- Strong skills: Python, PyTorch, LLM fine-tuning, inference optimization, FastAPI, Docker, Linux
- Research: NeurIPS 2024 first author "Stutter Makes Smarter" (small LLM self-improvement via disfluency);
  ACL 2025 co-author (multimodal text recognition with LLMs)
- Industry: MediaTek Research (LLM training pipelines, 20% GPU cost reduction, evaluation dashboards);
  Google Pixel team (Python automation tooling, UI testing); Gamania (recommendation systems)
- Recent project: Full-stack AI financial assistant with Claude API tool-calling loop
- Needs OPT work authorization (F-1 student, graduating Aug 2026, requires employer sponsorship)

Score the job on four axes (each 0.0 to 10.0):
1. skill_match: Does Jenny's actual skill set (PyTorch, LLM fine-tuning, FastAPI, Python, inference) match what this JD requires?
2. visa_friendly: How likely is this employer to sponsor OPT/H1B?
   - 10 = explicitly offers sponsorship
   - 7 = startup or no mention (often flexible)
   - 3 = large corp with no sponsorship mention (hit or miss)
   - 0 = explicitly excludes or requires existing US work auth
3. relevance: How well does this role fit Jenny's ML/AI/LLM research trajectory?
   - 10 = LLM research engineer / applied scientist / ML infra
   - 7 = general ML engineer / AI platform
   - 4 = backend SWE with some ML exposure
   - 1 = pure backend/frontend unrelated to ML
4. competition: How competitive is this role? (lower = better for Jenny's chances)
   - 10 = FAANG ML research (Google Brain / OpenAI / Meta AI)
   - 6 = large tech ML team (mid-FAANG)
   - 3 = Series B/C startup
   - 1 = small startup or niche company

Compute: overall = 0.35*skill_match + 0.30*visa_friendly + 0.25*relevance + 0.10*(10-competition)

Return ONLY valid JSON, no prose, no markdown fences:
{"skill_match": <float>, "visa_friendly": <float>, "relevance": <float>, "competition": <float>, "overall": <float>, "jd_summary": "<2-3 sentence summary of the role>", "recommendation": "<1-2 sentences: should Jenny apply and why>"}"""


def _build_user_prompt(job: dict) -> str:
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    description = (job.get("description", "") or "")[:4000]
    visa_signals = job.get("visa_signals", [])
    return f"""Job Title: {title}
Company: {company}
Location: {location}
Visa signals found in posting: {visa_signals}

Job Description:
{description}"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=20),
    retry=retry_if_exception_type(
        (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError)
    ),
)
def _call_claude(client: anthropic.Anthropic, model: str, user_prompt: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


def score_job(job: dict, client: anthropic.Anthropic, model: str) -> dict | None:
    user_prompt = _build_user_prompt(job)
    try:
        raw = _call_claude(client, model, user_prompt)
        scores = json.loads(raw)
        return scores
    except json.JSONDecodeError as e:
        print(f"[Scorer] JSON parse error for {job.get('title')}: {e}")
        return None
    except Exception as e:
        print(f"[Scorer] Error scoring {job.get('title')} @ {job.get('company')}: {e}")
        return None


def score_jobs_batch(
    jobs: list[dict], settings: Settings
) -> list[tuple[dict, dict | None]]:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    results = []
    for i, job in enumerate(jobs, 1):
        print(f"[Scorer] Scoring [{i}/{len(jobs)}]: {job.get('title')} @ {job.get('company')}")
        scores = score_job(job, client, settings.claude_model)
        results.append((job, scores))
        if i < len(jobs):
            time.sleep(0.5)
    return results
