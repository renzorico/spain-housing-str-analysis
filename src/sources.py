"""Where every raw file comes from.

One manifest, used by scripts/download_data.py and by the loaders, so a
file's URL and its local path are defined in exactly one place.
All sources are licensed CC BY 4.0.
"""

from pathlib import Path
from urllib.parse import quote

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# ---- Inside Airbnb ----------------------------------------------------
# Quarterly snapshots kept on the public site (Dec 2025 - Sep 2026).
# Folder dates are the scrape dates Inside Airbnb uses in its URLs.
INSIDE_AIRBNB_ROOT = "https://data.insideairbnb.com/spain"
CITY_PATHS = {
    "barcelona": "catalonia/barcelona",
    "madrid": "comunidad-de-madrid/madrid",
    "valencia": "vc/valencia",
    "malaga": "andalucía/malaga",
    "sevilla": "andalucía/sevilla",
}
SNAPSHOTS = {
    "barcelona": ["2025-12-14", "2026-03-21", "2026-06-24", "2026-09-17"],
    "madrid": ["2025-12-14", "2026-09-17"],
    "valencia": ["2025-12-27", "2026-09-20"],
    "malaga": ["2025-12-31", "2026-09-28"],
    "sevilla": ["2025-12-30", "2026-09-25"],
}

# ---- Ajuntament de Barcelona: official tourist-flat (HUT) register ------
# Quarterly copies; 2026 Q2 is not published on the portal.
HUT_REGISTER_DATASET = (
    "https://opendata-ajuntament.barcelona.cat/data/ca/dataset/habitatges-us-turistic"
)
HUT_REGISTER_URLS = {
    "2025_1T": "https://opendata-ajuntament.barcelona.cat/data/dataset/c748799e-1079-44b1-9e60-88d936a3fe70/resource/6cd8682e-c59e-4b47-84f6-2cc15d3f4188/download",
    "2025_2T": "https://opendata-ajuntament.barcelona.cat/data/dataset/c748799e-1079-44b1-9e60-88d936a3fe70/resource/d92e7521-c94c-4f97-8a23-4b8b3c4825ec/download",
    "2025_3T": "https://opendata-ajuntament.barcelona.cat/data/dataset/c748799e-1079-44b1-9e60-88d936a3fe70/resource/6b4a2c03-f0c4-479c-b1e9-f0457133a4df/download",
    "2025_4T": "https://opendata-ajuntament.barcelona.cat/data/dataset/c748799e-1079-44b1-9e60-88d936a3fe70/resource/b31a81d8-d578-4ec4-8cce-4f3648a92975/download",
    "2026_1T": "https://opendata-ajuntament.barcelona.cat/data/dataset/c748799e-1079-44b1-9e60-88d936a3fe70/resource/297cf7da-2b43-4c83-91e2-210bfe5c33e9/download",
    "2026_3T": "https://opendata-ajuntament.barcelona.cat/data/dataset/c748799e-1079-44b1-9e60-88d936a3fe70/resource/2214883c-3a56-43f8-b7c5-9ddc42c2ebbe/download",
}

# ---- Generalitat de Catalunya: average rent (Incasòl deposits) ---------
# Municipality level only; no current district-level series is published.
RENTS_DATASET = "https://analisi.transparenciacatalunya.cat/d/qww9-bvhh"
RENTS_API = "https://analisi.transparenciacatalunya.cat/resource/qww9-bvhh.json"
RENTS_MUNICIPALITIES = ["Barcelona", "Girona"]


def listings_path(city: str, snapshot: str) -> Path:
    return RAW_DIR / "insideairbnb" / city / snapshot / "listings.csv"


def neighbourhoods_path(city: str) -> Path:
    return RAW_DIR / "insideairbnb" / city / "neighbourhoods.geojson"


def hut_register_path(quarter: str) -> Path:
    return RAW_DIR / "hut_register" / f"{quarter}.csv.zip"


RENTS_PATH = RAW_DIR / "rents" / "incasol_rents.json"


def listings_url(city: str, snapshot: str, filename: str = "listings.csv") -> str:
    """URL of one Inside Airbnb summary file (quoted: paths contain accents)."""
    raw = (
        f"{INSIDE_AIRBNB_ROOT}/{CITY_PATHS[city]}/{snapshot}/visualisations/{filename}"
    )
    return quote(raw, safe=":/")


def rents_url() -> str:
    """Socrata query for the rent rows of the selected municipalities."""
    names = ",".join(f"'{name}'" for name in RENTS_MUNICIPALITIES)
    query = f"$where=nom_territori in({names})&$limit=50000"
    return f"{RENTS_API}?{quote(query, safe='=&$')}"
