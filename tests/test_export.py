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
