import json
import pytest
from unittest.mock import MagicMock, patch
from agents.job_scorer import score_job, _build_user_prompt


def _mock_client(response_text: str):
    mock_content = MagicMock()
    mock_content.text = response_text
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    client = MagicMock()
    client.messages.create.return_value = mock_response
    return client


def _sample_job():
    return {
        "title": "ML Engineer",
        "company": "Test AI Inc",
        "location": "Remote",
        "description": "Work on LLM fine-tuning with PyTorch. Entry level. OPT sponsorship available.",
        "visa_signals": ["opt", "entry level"],
    }


_VALID_SCORES = {
    "skill_match": 8.5,
    "visa_friendly": 9.0,
    "relevance": 8.0,
    "competition": 3.0,
    "overall": 8.375,
    "jd_summary": "ML engineer role focused on LLM fine-tuning.",
    "recommendation": "Strong match. Apply immediately.",
}


def test_score_job_valid_response():
    client = _mock_client(json.dumps(_VALID_SCORES))
    result = score_job(_sample_job(), client, "claude-sonnet-4-6")
    assert result is not None
    assert result["skill_match"] == 8.5
    assert result["overall"] == 8.375
    assert "recommendation" in result


def test_score_job_invalid_json_returns_none():
    client = _mock_client("This is not JSON at all")
    result = score_job(_sample_job(), client, "claude-sonnet-4-6")
    assert result is None


def test_build_user_prompt_contains_job_info():
    job = _sample_job()
    prompt = _build_user_prompt(job)
    assert "ML Engineer" in prompt
    assert "Test AI Inc" in prompt
    assert "opt" in prompt


def test_score_job_truncates_long_description():
    long_desc = "x" * 10000
    job = {**_sample_job(), "description": long_desc}
    client = _mock_client(json.dumps(_VALID_SCORES))
    # Should not raise; description gets truncated to 4000 chars in prompt
    result = score_job(job, client, "claude-sonnet-4-6")
    assert result is not None
    call_args = client.messages.create.call_args
    user_content = call_args.kwargs["messages"][0]["content"]
    assert len(user_content) < 5000
