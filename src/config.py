"""All the project's settings and thresholds in one place.

If a number can be argued with ("why 31 and not 30?"), it lives here,
so there is exactly one copy to find and change.
"""

from pathlib import Path

# ---- paths -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LISTINGS_FILE = PROJECT_ROOT / "data" / "raw" / "listings.csv"
CLEAN_FILE = PROJECT_ROOT / "data" / "listings_clean.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# The date Inside Airbnb scraped this file. They publish a new one every
# quarter, so without this date the numbers cannot be reproduced.
SNAPSHOT_DATE = "2026-09-17"

# ---- cleaning thresholds ---------------------------------------------
# Same cap as the Berlin project; re-check against the 99th percentile
# of the Barcelona file in notebook 01.
MAX_PRICE = 1000

# In Catalonia a stay of 31 days or fewer is tourist use and needs an HUT
# licence (Decret 75/2020, art. 241-1). Longer stays are seasonal
# (temporada) lets, a different legal market.
MAX_TOURIST_NIGHTS = 31

# A host with this many listings or more is treated as professional.
PROFESSIONAL_MIN = 5

# ---- geography --------------------------------------------------------
# Barcelona's 10 districts, copied EXACTLY as they appear in the file.
# Check against df["neighbourhood_group"].unique() after download.
CENTRAL_DISTRICTS = [
    "Ciutat Vella",
    "Eixample",
    "Gràcia",
]

# ---- policy levers ----------------------------------------------------
# The rules the analysis checks against the data. Neutral by design:
# what the rule says and when it applies, never who proposed it.
# Dates marked VERIFY come from secondary sources and must be checked
# against the BOE / DOGC before the findings are published.
POLICY_LEVERS = {
    "tourist_licence_phase_out": {
        "rule": "Barcelona's ~10,000 HUT licences are not renewed",
        "law": "Decret llei 3/2023 (Generalitat de Catalunya)",
        "applies_from": "2028-11-01",  # VERIFY exact day
    },
    "rent_cap": {
        "rule": "New leases in stressed areas capped by the reference index",
        "law": "Ley 12/2023 por el derecho a la vivienda",
        "applies_from": "2024-03-16",  # VERIFY (Catalan zones in force)
    },
    "seasonal_rentals": {
        "rule": "Rent cap also covers seasonal (temporada) lets",
        "law": "Llei 11/2025 (Catalonia)",
        "applies_from": "2026-01-01",  # VERIFY
    },
    "owners_veto": {
        "rule": "Owners' associations can block new tourist lets by 3/5 vote",
        "law": "Ley Orgánica 1/2025 (Ley de Propiedad Horizontal, art. 17.12)",
        "applies_from": "2025-04-03",  # VERIFY
    },
}

# Dated events that frame the snapshot. Context only, not analysed.
CONTEXT_EVENTS = {
    "general_election": "2026-11-29",
    "municipal_election": "2027-05-23",
}

SEED = 42
