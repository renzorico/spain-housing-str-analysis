"""The raw-data manifest ties every export to its exact inputs.

Run with:  python -m pytest -q
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from scripts.download_data import all_downloads
from src import sources

SHA256 = re.compile(r"^[0-9a-f]{64}$")
META = ROOT / "site" / "public" / "data" / "meta.json"

pytestmark = pytest.mark.skipif(not sources.MANIFEST_PATH.exists(), reason="run scripts/download_data.py first")


def test_manifest_covers_every_raw_file_with_a_hash():
    entries = {e["path"]: e for e in json.loads(sources.MANIFEST_PATH.read_text())}
    for url, target in all_downloads():
        entry = entries[str(target.relative_to(sources.RAW_DIR))]
        assert entry["url"] == url
        assert SHA256.match(entry["sha256"]) and entry["bytes"] > 0


@pytest.mark.skipif(not META.exists(), reason="run scripts/export_site_data.py first")
def test_the_committed_export_was_made_from_this_manifest_and_config():
    """Fails when inputs or config changed without re-running the export."""
    provenance = json.loads(META.read_text())["provenance"]
    assert provenance["raw_manifest_sha256"] == hashlib.sha256(sources.MANIFEST_PATH.read_bytes()).hexdigest()
    config = (ROOT / "src" / "config.py").read_bytes()
    assert provenance["config_sha256"] == hashlib.sha256(config).hexdigest()
