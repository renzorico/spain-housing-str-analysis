"""Checks on the official-data helpers.

Run with:  python -m pytest -q
"""
import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src import official


def test_quarter_end_dates():
    assert official.quarter_end("2025_4T") == date(2025, 12, 31)
    assert official.quarter_end("2026_1T") == date(2026, 3, 31)
    assert official.quarter_end("2026_3T") == date(2026, 9, 30)


def test_each_snapshot_gets_the_nearest_published_register_quarter():
    assert official.register_quarter_for("2025-12-14") == "2025_4T"
    assert official.register_quarter_for("2026-03-21") == "2026_1T"
    # 2026 Q2 is not published: June goes to Q1 (85 days) rather than Q3 (98)
    assert official.register_quarter_for("2026-06-24") == "2026_1T"
    assert official.register_quarter_for("2026-09-17") == "2026_3T"
