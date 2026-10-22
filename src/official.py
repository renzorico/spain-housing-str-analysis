"""Loaders for the official (non-Airbnb) sources.

The HUT register lists each flat down to floor and door. Only the
aggregate functions here leave this module: nothing downstream ever sees
an address.
"""

import json
import re
import zipfile

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
