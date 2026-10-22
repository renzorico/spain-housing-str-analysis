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


def test_match_summary_keeps_its_units_apart():
    import pandas as pd

    shown = pd.Series(["1", "1", "2", "9"])      # four listings, three distinct numbers
    register = {"1", "2", "3", "4"}             # four numbers in the register
    result = official.summarise_match(shown, register)
    assert result["listings_showing_number"] == 4
    assert result["displayed_numbers"] == 3
    assert result["displayed_numbers_found_in_register"] == 2
    assert result["displayed_found_pct"] == 66.7          # 2 of 3 displayed numbers exist
    assert result["register_numbers_displayed_pct"] == 50.0   # 2 of 4 register numbers shown
    assert result["numbers_on_2plus_listings"] == 1
