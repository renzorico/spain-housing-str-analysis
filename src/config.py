"""All the project's settings and thresholds in one place.

If a number can be argued with ("why 31 and not 30?"), it lives here,
so there is exactly one copy to find and change.
"""

from pathlib import Path

from . import sources

# The Barcelona snapshot notebooks 01-02 analyse in depth. Inside Airbnb
# publishes a new one every quarter, so without this date the numbers
# cannot be reproduced. All snapshots are listed in src/sources.py.
SNAPSHOT_DATE = "2026-09-17"

# ---- paths -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LISTINGS_FILE = sources.listings_path("barcelona", SNAPSHOT_DATE)
CLEAN_FILE = PROJECT_ROOT / "data" / "listings_clean.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ---- cleaning thresholds ---------------------------------------------
# Same cap as the Berlin project, kept for comparability. In Barcelona it
# removes 295 listings (2.7% of priced ones), almost all tourist entire
# homes; the 99th percentile is ~2,000 EUR.
MAX_PRICE = 1000

# In Catalonia a tourist flat (HUT) is let for an "estada de temporada":
# "a continuous period of 31 days or fewer" (Decret 75/2020, art. 221-1,
# as quoted in STC 64/2025, BOE-A-2025-7430). Longer stays are seasonal
# (temporada) lets, a different legal market. An HUT must be let whole
# (Llei 13/2002, art. 50 bis), so private rooms cannot hold one.
# Whether a 31-NIGHT booking counts as "31 days or fewer" is ambiguous, so
# listings with exactly this minimum get their own "boundary" stay band.
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
# Checked against BOE texts on 2026-10-22; "source" is the primary text.
# "notes" holds what a one-line rule would hide (extensions, challenges).
POLICY_LEVERS = {
    "tourist_licence_phase_out": {
        "rule": (
            "Existing HUTs in stressed municipalities, Barcelona included, "
            "must obtain an urban-planning licence within 5 years or stop"
        ),
        "law": "Decret llei 3/2023, de 7 de novembre (DOGC 9036, 8 Nov 2023)",
        "applies_from": "2023-11-09",
        "deadline": "2028-11-09",
        "source": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-7430",
        "notes": (
            "Owners can request one extension of up to 5 more years "
            "(transitional provision 1.2). Ratified by the Catalan "
            "Parliament 20 Dec 2023. Appeal dismissed in full by "
            "STC 64/2025 (13 Mar 2025)."
        ),
    },
    "rent_cap": {
        "rule": "New leases in stressed areas capped by the reference index",
        "law": "Ley 12/2023, de 24 de mayo; Resolució TER/800/2024 (Catalan zones)",
        "applies_from": "2024-03-16",
        "deadline": None,
        "source": "https://www.boe.es/boe/dias/2024/03/15/pdfs/BOE-A-2024-5214.pdf",
        "notes": (
            "Zone valid 3 years from 16 Mar 2024. Extended in 118 "
            "municipalities by Resolució TER/3739/2026 (DOGC 19 Oct 2026); "
            "Barcelona is on the Generalitat's extension list. Extension "
            "end date not yet checked."
        ),
    },
    "seasonal_rentals": {
        "rule": (
            "Seasonal lets not for holidays or leisure count as housing "
            "leases, so the stressed-zone rent cap applies to them"
        ),
        "law": "Llei 11/2025, de 29 de desembre (DOGC 9574, 31 Dec 2025)",
        "applies_from": "2026-01-01",
        "deadline": None,
        "source": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-5547",
        "notes": (
            "Adds art. 66 bis-ter to Llei 18/2007; room lets capped at the "
            "whole-flat maximum. Parts of the law (incl. art. 5) are "
            "challenged at the Constitutional Court (recurso 2415-2026, "
            "BOE-A-2026-13028); no ruling yet."
        ),
    },
    "owners_veto": {
        "rule": "Owners' associations can block new tourist lets by a 3/5 vote",
        "law": "Ley Orgánica 1/2025, de 2 de enero (BOE 3 Jan 2025), LPH art. 17.12",
        "applies_from": "2025-04-03",
        "deadline": None,
        "source": "https://www.boe.es/buscar/act.php?id=BOE-A-2025-76",
        "notes": (
            "Not retroactive: tourist lets already operating before "
            "3 Apr 2025 can continue."
        ),
    },
}

# Dated events that frame the snapshot. Context only, not analysed.
CONTEXT_EVENTS = {
    "general_election": "2026-11-29",
    "municipal_election": "2027-05-23",
}

SEED = 42
