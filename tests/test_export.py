"""Privacy and sanity checks on the website's exported data.

Skipped until scripts/export_site_data.py has been run.

Run with:  python -m pytest -q
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATA_DIR = Path(__file__).resolve().parents[1] / "site" / "public" / "data"
FILES = sorted(DATA_DIR.glob("*.json")) + sorted(DATA_DIR.glob("*.geojson"))

# Field names that would identify a host, a listing or a flat.
FORBIDDEN_KEYS = {"id", "host_id", "host_name", "name", "license", "address", "street"}
# Raw licence text and register address fields must never leak.
FORBIDDEN_TEXT = ["<br", "registration number", "First name", "Legal entity", "HUTB-", "CARRER", "PORTA"]

pytestmark = pytest.mark.skipif(not FILES, reason="run scripts/export_site_data.py first")


def all_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from all_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from all_keys(value)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_identifying_fields_or_raw_text(path):
    text = path.read_text()
    payload = json.loads(text)       # also proves the file is valid JSON (no NaN)
    assert not FORBIDDEN_KEYS & set(all_keys(payload)), path.name
    for fragment in FORBIDDEN_TEXT:
        assert fragment not in text, f"{fragment!r} in {path.name}"


def test_map_points_have_equal_length_columns():
    for path in DATA_DIR.glob("barcelona_points_*.json"):
        points = json.loads(path.read_text())
        columns = {k: len(v) for k, v in points.items() if k != "legend"}
        assert len(set(columns.values())) == 1, (path.name, columns)


def load(name):
    return json.loads((DATA_DIR / name).read_text())


def test_neighbourhoods_are_unique_and_every_one_has_an_outline():
    rows = load("neighbourhoods.json")
    names = [r["neighbourhood"] for r in rows]
    assert len(names) == len(set(names)), "a neighbourhood appears more than once"
    outlines = [f["properties"]["neighbourhood"] for f in load("neighbourhoods.geojson")["features"]]
    assert sorted(outlines) == sorted(names)


def test_neighbourhood_totals_reconcile_with_the_city_totals():
    rows = load("neighbourhoods.json")
    rec = load("register.json")["neighbourhood_reconciliation"]
    barcelona = next(c for c in load("cities.json") if c["city"] == "barcelona")
    latest_listings = barcelona["rounds"]["Sep 2026"]["active"]
    assert sum(r["active_listings"] for r in rows) == latest_listings == rec["listings_total"]
    assert (
        sum(r["registered_huts"] for r in rows) + rec["register_without_known_neighbourhood"]
        == rec["register_total"]
    )


def test_every_published_share_matches_its_own_counts():
    for row in load("cities.json"):
        for round_name, summary in row["rounds"].items():
            assert summary["population"] == "listings with open dates"
            for name, (numerator, denominator) in summary["counts"].items():
                assert denominator == summary["active"], (row["city"], round_name, name)
                assert summary[name] == round(100 * numerator / denominator, 1), (row["city"], round_name, name)


def test_availability_sensitivity_populations_are_nested():
    for row in load("cities.json"):
        check = row["availability_sensitivity"]
        sizes = [check[k]["listings"] for k in ("open_dates", "open_dates_or_reviewed_12m", "all_listings")]
        assert sizes == sorted(sizes), row["city"]
        for population in check.values():
            assert population["known_minimum_stay"] + population["unknown_minimum_stay"] == population["listings"]


def test_exit_gap_cohorts_match_the_transition_tables():
    transitions = load("transitions.json")["cities"]
    for row in load("cities.json"):
        gap, table = row["exit_gap"], transitions[row["city"]]
        sums = {band: sum(counts) for band, counts in zip(table["from"], table["counts"])}
        assert gap["month_plus_listings"] == sums["boundary"] + sums["seasonal"], row["city"]
        assert gap["shorter_listings"] == sums["tourist"], row["city"]
        assert gap["ci_low"] <= gap["points"] <= gap["ci_high"], row["city"]
        # the account-level interval must not be narrower than the naive one
        assert gap["ci_high"] - gap["ci_low"] >= gap["listing_level_ci_high"] - gap["listing_level_ci_low"]


def test_contrasts_are_barcelona_minus_the_city():
    cities = {row["city"]: row["exit_gap"] for row in load("cities.json")}
    assert cities["barcelona"]["vs_barcelona"] is None
    for city, gap in cities.items():
        if city == "barcelona":
            continue
        contrast = gap["vs_barcelona"]
        assert contrast["difference_points"] == round(cities["barcelona"]["points"] - gap["points"], 1)
        assert contrast["ci_low"] <= contrast["difference_points"] <= contrast["ci_high"]
