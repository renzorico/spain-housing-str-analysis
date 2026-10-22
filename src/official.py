"""Loaders for the official (non-Airbnb) sources.

The HUT register lists each flat down to floor and door. Only the
aggregate functions here leave this module: nothing downstream ever sees
an address.
"""

import json
import re
import zipfile
from datetime import date

import pandas as pd

from . import cleaning
from . import sources as src

# Incasòl publishes quarters, half-years, nine-month and full-year
# periods. Only single quarters are kept, dated at the quarter's start.
QUARTER_START_MONTH = {
    "gener-març": 1,
    "abril-juny": 4,
    "juliol-setembre": 7,
    "octubre-desembre": 10,
}


def quarter_end(code: str) -> date:
    """'2026_3T' -> 30 Sep 2026. The register file for a quarter holds the
    data published in that quarter's last week."""
    year, quarter = code.split("_")
    month = int(quarter.rstrip("T")) * 3
    last_day = {3: 31, 6: 30, 9: 30, 12: 31}[month]
    return date(int(year), month, last_day)


def register_quarter_for(snapshot: str) -> str:
    """The published register quarter nearest in time to an Inside Airbnb
    snapshot date ('2026-06-24').

    2026 Q2 is missing from the portal, so the June 2026 snapshot is matched
    to 2026 Q1 (85 days away, against 98 for Q3). Ties go to the earlier
    quarter.
    """
    day = date.fromisoformat(snapshot)
    return min(
        src.HUT_REGISTER_URLS,
        key=lambda code: (abs((quarter_end(code) - day).days), quarter_end(code)),
    )


def normalise_place_name(name: str) -> str:
    """Match neighbourhood names across sources: the register writes
    'Sant Pere Santa Caterina i la Ribera', the geojson
    'Sant Pere, Santa Caterina i la Ribera'."""
    return re.sub(r"\s+", " ", str(name).replace(",", "")).strip().lower()


def hut_counts_by_neighbourhood(quarter: str) -> pd.Series:
    """Number of registered tourist flats per neighbourhood in one quarter."""
    path = src.hut_register_path(quarter)
    with zipfile.ZipFile(path) as archive, archive.open(
        archive.infolist()[0]
    ) as handle:
        register = pd.read_csv(handle, usecols=["N_EXPEDIENT", "NOM_BARRI"])
    counts = register.groupby(register["NOM_BARRI"].map(normalise_place_name))[
        "N_EXPEDIENT"
    ].nunique()
    return counts.rename("registered_huts")


def register_record_count(quarter: str) -> int:
    """Distinct administrative records (case ids) in one register quarter.
    Not the same unit as the HUT numbers: a few records have no usable
    number, and the headline stock counts records."""
    path = src.hut_register_path(quarter)
    with zipfile.ZipFile(path) as archive, archive.open(archive.infolist()[0]) as handle:
        register = pd.read_csv(handle, usecols=["N_EXPEDIENT"], dtype=str)
    return int(register["N_EXPEDIENT"].nunique())


def registered_hut_numbers(quarter: str) -> set[str]:
    """Normalised HUT numbers in the official register (see
    cleaning.hut_number), for matching against Airbnb listings."""
    path = src.hut_register_path(quarter)
    with zipfile.ZipFile(path) as archive, archive.open(
        archive.infolist()[0]
    ) as handle:
        numbers = pd.read_csv(
            handle, usecols=["NUMERO_REGISTRE_GENERALITAT"], dtype=str
        )
    # dropna, not a truthiness check: map turns None into NaN, which is truthy
    return set(numbers["NUMERO_REGISTRE_GENERALITAT"].map(cleaning.hut_number).dropna())


def summarise_match(shown: pd.Series, register_numbers: set[str]) -> dict:
    """How the HUT numbers shown on listings relate to a register quarter.

    `shown` has one normalised HUT number per listing that shows one (see
    cleaning.listing_hut_number). Three units stay apart: listings, distinct
    displayed numbers and register numbers. A match shows that a number
    exists in the register; it does not verify that the listing is that
    property, and it cannot show how many licensed flats are absent from the
    platform.
    """
    displayed = set(shown)
    matched = displayed & register_numbers
    return {
        "listings_showing_number": int(len(shown)),
        "displayed_numbers": len(displayed),
        "displayed_numbers_found_in_register": len(matched),
        "displayed_found_pct": round(len(matched) / len(displayed) * 100, 1),
        "register_numbers_displayed_pct": round(len(matched) / len(register_numbers) * 100, 1),
        "numbers_on_2plus_listings": int((shown.value_counts() > 1).sum()),
    }


def hut_totals() -> pd.Series:
    """Registered tourist flats in Barcelona, per published quarter."""
    totals = {
        quarter: hut_counts_by_neighbourhood(quarter).sum()
        for quarter in src.HUT_REGISTER_URLS
    }
    return pd.Series(totals, name="registered_huts")


def load_rents(municipality: str = "Barcelona") -> pd.DataFrame:
    """Quarterly average monthly rent of new leases (Incasòl deposits)."""
    rows = pd.DataFrame(json.loads(src.RENTS_PATH.read_text()))
    rows = rows[
        (rows["nom_territori"] == municipality)
        & rows["periode"].isin(QUARTER_START_MONTH)
    ]
    quarter_start = pd.to_datetime(
        dict(
            year=rows["any"].astype(int),
            month=rows["periode"].map(QUARTER_START_MONTH),
            day=1,
        )
    )
    return (
        pd.DataFrame(
            {
                "quarter_start": quarter_start,
                "avg_rent": rows["renda"].astype(float).round(2),
                "new_leases": rows["habitatges"].astype(int),
            }
        )
        .sort_values("quarter_start")
        .reset_index(drop=True)
    )
