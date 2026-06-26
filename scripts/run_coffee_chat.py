#!/usr/bin/env python3
"""Workflow 3: Coffee Chat Hunter — generates search queries + personalized messages.

Semi-automated mode:
  1. Generates targeted LinkedIn search queries (no scraping)
  2. You run searches manually, paste profile info into targets.json
  3. Re-run this script to generate personalized messages
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from agents.coffee_chat_agent import batch_generate
from database.db import JobDatabase

# LinkedIn search query templates — run these manually
SEARCH_QUERIES = [
    # UCLA alumni — highest priority
    'site:linkedin.com/in "UCLA" "Machine Learning Engineer" OR "ML Engineer" OR "AI Engineer"',
    'site:linkedin.com/in "UCLA" "Research Engineer" "deep learning" OR "LLM" OR "NLP"',
    'site:linkedin.com/in "University of California Los Angeles" "Applied Scientist"',
    # NYCU / NCTU alumni
    'site:linkedin.com/in "NYCU" OR "NCTU" "Machine Learning" OR "AI" engineer',
    # ML/LLM engineers at target companies
    'site:linkedin.com/in "LLM" OR "large language model" engineer "PyTorch" "New Grad" OR "Entry Level"',
    # LinkedIn native search (use in LinkedIn search bar directly)
    "LinkedIn People Search: School=UCLA, Keywords=ML Engineer",
    "LinkedIn People Search: School=NYCU OR NCTU, Keywords=Machine Learning",
    "LinkedIn People Search: Company=[target], Keywords=Machine Learning Engineer",
]

TARGETS_FILE = "data/coffee_chat_targets.json"
OUTPUT_DIR = "output/coffee_chat_messages"


def generate_search_queries_file():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    query_file = f"{OUTPUT_DIR}/search_queries_{date_str}.md"

    lines = [
        "# LinkedIn Search Queries for Coffee Chat Targets",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
        "## How to Use",
        "1. Run these searches on LinkedIn or Google",
        "2. Find 10 targets prioritizing: UCLA alumni > NYCU alumni > ML engineers",
        f"3. Add their info to `{TARGETS_FILE}` (see template below)",
        "4. Re-run `python scripts/run_coffee_chat.py --generate-messages` to create messages",
        "",
        "## Search Queries",
        "",
    ]
    for i, q in enumerate(SEARCH_QUERIES, 1):
        lines.append(f"### Query {i}")
        lines.append(f"```")
        lines.append(q)
        lines.append(f"```")
        lines.append("")

    lines += [
        "## Target Template (save as data/coffee_chat_targets.json)",
        "",
        "```json",
        json.dumps([
            {
                "name": "First Last",
                "title": "ML Engineer",
                "company": "Example Corp",
                "linkedin_url": "https://linkedin.com/in/username",
                "school": "UCLA",
                "connection_type": "alumni",
                "notes": "Works on recommendation systems, published paper on X"
            }
        ], indent=2),
        "```",
    ]

    Path(query_file).write_text("\n".join(lines), encoding="utf-8")
    print(f"[CoffeeChat] Search queries saved to: {query_file}")
    return query_file


def generate_messages_from_targets(settings: Settings):
    targets_path = Path(TARGETS_FILE)
    if not targets_path.exists():
        print(f"[CoffeeChat] No targets file found at {TARGETS_FILE}")
        print("  Run without --generate-messages first to get search queries,")
        print(f"  then add targets to {TARGETS_FILE}")
        return

    targets = json.loads(targets_path.read_text())
    if not targets:
        print("[CoffeeChat] targets.json is empty.")
        return

    print(f"[CoffeeChat] Generating messages for {len(targets)} targets...")
    targets_with_messages = batch_generate(targets, settings)

    # Save messages to individual .md files
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_file = f"{OUTPUT_DIR}/messages_{date_str}.md"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Coffee Chat Messages — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
    ]
    for t in targets_with_messages:
        msg = t.get("personalized_message", "")
        char_count = len(msg)
        warning = " ⚠️ OVER 300 CHARS" if char_count > 300 else ""
        lines += [
            f"## {t.get('name')} — {t.get('title')} @ {t.get('company')}",
            f"LinkedIn: {t.get('linkedin_url', 'N/A')}",
            f"School: {t.get('school', 'N/A')} | Type: {t.get('connection_type', 'N/A')}",
            f"Message ({char_count} chars){warning}:",
            "",
            msg,
            "",
            "---",
            "",
        ]

    Path(output_file).write_text("\n".join(lines), encoding="utf-8")
    print(f"[CoffeeChat] Messages saved to: {output_file}")

    # Save to DB
    with JobDatabase(settings.database_path) as db:
        for t in targets_with_messages:
            db.insert_coffee_chat_target(t)
    print(f"[CoffeeChat] {len(targets_with_messages)} targets saved to database.")


def main():
    settings = Settings()
    generate_messages = "--generate-messages" in sys.argv

    print("=" * 60)
    print("Coffee Chat Hunter")
    print("=" * 60)

    if generate_messages:
        generate_messages_from_targets(settings)
    else:
        query_file = generate_search_queries_file()
        print(f"\nNext steps:")
        print(f"  1. Open {query_file} and run the search queries on LinkedIn")
        print(f"  2. Add 10 targets to {TARGETS_FILE}")
        print(f"  3. Run: python scripts/run_coffee_chat.py --generate-messages")


if __name__ == "__main__":
    main()
