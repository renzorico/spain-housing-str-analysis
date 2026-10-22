"""Checks on the shared metrics, with tiny made-up data.

Run with:  python -m pytest -q
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src import cleaning, metrics, official


def listings(ids, nights, open_dates, hosts=None):
    """Minimal frame with the columns the metrics read."""
    n = len(ids)

    return pd.DataFrame(
        {
            "id": ids,
            "stay_band": cleaning.stay_band(pd.Series(nights, dtype="float")),
            "is_active": [d > 0 for d in open_dates],
            "host_id": hosts if hosts is not None else list(range(n)),
        }
    )


def test_transitions_track_moves_inactivity_and_exits():
    december = listings([1, 2, 3, 4], [2, 2, 2, 32], [100, 100, 100, 100])
    september = listings([1, 2, 4, 9], [32, 2, 32, 2], [100, 0, 100, 100])
    table = metrics.transitions(december, september)
    assert table.loc["tourist", "seasonal"] == 1  # id 1 moved
    assert table.loc["tourist", "inactive"] == 1  # id 2 no open dates
    assert table.loc["tourist", "gone"] == 1  # id 3 left the file
    assert table.loc["seasonal", "seasonal"] == 1  # id 4 stayed
    assert table.to_numpy().sum() == 4  # new id 9 not counted


def test_concentration_curve_ends_at_100_percent():
    # host 1 runs 3 listings, hosts 2 and 3 one each
    df = listings([1, 2, 3, 4, 5], [2] * 5, [10] * 5, hosts=[1, 1, 1, 2, 3])
    curve = metrics.concentration_curve(df)
    assert curve["listing_share"].iloc[0] == 60.0  # biggest third of hosts: 3 of 5
    assert curve["host_share"].iloc[-1] == 100.0
    assert curve["listing_share"].iloc[-1] == 100.0


def test_place_names_match_across_sources():
    assert official.normalise_place_name(
        "Sant Pere, Santa Caterina i la Ribera"
    ) == official.normalise_place_name("Sant Pere Santa Caterina i la Ribera")


def test_exit_gap_in_points():
    # 1 of 2 month-plus listings gone (50%), 0 of 2 tourist gone (0%)
    table = pd.DataFrame(
        {"tourist": [2, 0, 0], "boundary": [0, 1, 0], "seasonal": [0, 0, 0],
         "inactive": [0, 0, 0], "gone": [0, 0, 1]},
        index=["tourist", "boundary", "seasonal"],
    )
    gap, se = metrics.exit_gap(table)
    assert gap == 50.0
    assert se > 0


def test_availability_sensitivity_keeps_unknown_stays_apart():
    df = pd.DataFrame(
        {
            "availability_365": [10, 10, 0, 0, 0],
            "number_of_reviews_ltm": [0, 0, 4, 0, 0],
            "minimum_nights": [31.0, 2.0, float("nan"), 40.0, 3.0],
        }
    )
    result = metrics.availability_sensitivity(df)
    assert result["open_dates"]["month_plus_pct"] == 50.0
    # the reviewed listing has an unknown stay: counted as unknown, not as short
    assert result["open_dates_or_reviewed_12m"]["unknown_minimum_stay"] == 1
    assert result["open_dates_or_reviewed_12m"]["known_minimum_stay"] == 2
    assert result["all_listings"]["month_plus_pct"] == 50.0
    assert result["all_listings"]["known_minimum_stay"] == 4
