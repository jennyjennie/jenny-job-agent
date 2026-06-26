import anthropic
from config.settings import Settings

_SYSTEM_PROMPT = """You are helping Jenny Ho write personalized LinkedIn connection messages.

Jenny's background:
- UCLA MEng AI (graduating Aug 2026), NYCU BS CS
- Research: NeurIPS 2024 first author (small LLM efficiency), ACL 2025
- Interned at MediaTek Research (LLM) and Google (Pixel team)
- Seeking ML Engineer / AI Engineer / Research Engineer roles

Rules for the message:
1. MUST be under 300 characters (LinkedIn connection request limit)
2. Mention the specific shared connection (UCLA alum, NYCU alum, or shared ML interest)
3. Reference something specific about the person's role or company
4. One concrete, low-friction ask: "Would love to chat for 15 min about your work on X"
5. NO generic phrases like "I hope this message finds you well"
6. NO direct mention of job-seeking or asking for referrals
7. Sound genuine, not like a template

Return ONLY the message text, no explanations, no quotes."""


def generate_message(target: dict, settings: Settings) -> str:
    name = target.get("name", "")
    title = target.get("title", "")
    company = target.get("company", "")
    school = target.get("school", "")
    connection_type = target.get("connection_type", "")
    notes = target.get("notes", "")

    connection_context = ""
    if school == "UCLA":
        connection_context = "fellow UCLA alum"
    elif school == "NYCU":
        connection_context = "fellow NYCU alum"
    elif connection_type == "ml_engineer":
        connection_context = "ML practitioner"

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    user_prompt = f"""Write a LinkedIn connection message for:
Name: {name}
Title: {title}
Company: {company}
Shared connection: {connection_context}
Additional context: {notes}

Jenny is an ML engineer with LLM research background (NeurIPS 2024), interned at Google and MediaTek. She wants to connect genuinely."""

    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=150,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text.strip()


def batch_generate(targets: list[dict], settings: Settings) -> list[dict]:
    results = []
    for i, target in enumerate(targets, 1):
        print(f"[CoffeeChat] [{i}/{len(targets)}] Generating message for {target.get('name')}...")
        try:
            message = generate_message(target, settings)
            target["personalized_message"] = message
            print(f"  ({len(message)} chars) {message[:80]}...")
        except Exception as e:
            print(f"  Error: {e}")
            target["personalized_message"] = ""
        results.append(target)
    return results
