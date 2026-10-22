"""Quick checks on the cleaning rules.

A test = tiny made-up data where the right answer is known + an assert.
If a rule is ever changed by accident, one of these fails loudly.

Run with:  python -m pytest -q
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src import cleaning

REGIONAL = "Barcelona - Regional registration number<br />"
NATIONAL = "Spain - National registration number<br />"
GAP = "<br /><br />"


def toy_data():
    """Six listings: a licensed tourist flat, an absurd price, a 32-night
    seasonal let, a dead one (no reviews, nothing bookable), a hostel and
    one with no minimum stay. Licence text mimics the real field."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6],
            "neighbourhood_group": [
                "Eixample",
                "Gràcia",
                "Sant Martí",
                "Ciutat Vella",
                "Les Corts",
                "Eixample",
            ],
            "room_type": [
                "Entire home/apt",
                "Private room",
                "Entire home/apt",
                "Private room",
                "Private room",
                "Entire home/apt",
            ],
            "price": [120.0, 5000.0, 90.0, 55.0, 60.0, 200.0],
            "minimum_nights": [2, 3, 32, 1, 1, np.nan],
            "number_of_reviews": [40, 12, 3, 0, 5, 50],
            "calculated_host_listings_count": [1, 8, 1, 1, 1, 1],
            "availability_365": [200, 150, 300, 0, 100, 0],
            "license": [
                REGIONAL + "HUTB-012345" + GAP + NATIONAL + "ESFCTU00000801HUTB-012345",
                NATIONAL + "ESHFTU00000801",
                NATIONAL
                + "ESFCNT00000801"
                + GAP
                + REGIONAL
                + "Exempt - seasonal rental",
                None,
                REGIONAL + "AJ000123" + GAP + NATIONAL + "Exempt - hostel",
                REGIONAL + "HUTB-054321",
            ],
        }
    )


def test_cleaning_drops_bad_price_unknown_stay_and_dead_listing():
    out = cleaning.clean_listings(toy_data())
    assert list(out["id"]) == [1, 3, 5]


def test_regional_licence_categories():
    cats = toy_data()["license"].apply(cleaning.regional_licence)
    assert cats.tolist() == [
        "hut",
        "missing",
        "exempt_seasonal",
        "missing",
        "hotel_or_hostel",
        "hut",
    ]


def test_national_licence_reads_declared_use():
    cats = toy_data()["license"].apply(cleaning.national_licence)
    assert cats.tolist() == [
        "nrua_tourist",
        "nrua_tourist",
        "nrua_seasonal",
        "missing",
        "exempt",
        "missing",
    ]


def test_seasonal_split_at_31_nights():
    out = cleaning.add_columns(toy_data())
    assert out.loc[out["id"] == 1, "is_tourist_stay"].item() == True
    assert out.loc[out["id"] == 3, "is_tourist_stay"].item() == False


def test_professional_flag():
    out = cleaning.add_columns(toy_data())
    assert out.loc[out["id"] == 2, "is_professional"].item() == True
    assert out.loc[out["id"] == 1, "is_professional"].item() == False
