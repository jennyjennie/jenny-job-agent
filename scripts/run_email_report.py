#!/usr/bin/env python3
"""Workflow 4: Daily Email Report — query DB, render, send."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings
from agents.email_report_agent import run_daily_report


def main():
    settings = Settings()
    print("=" * 60)
    print("Daily Email Report starting")
    print("=" * 60)
    run_daily_report(settings)


if __name__ == "__main__":
    main()
