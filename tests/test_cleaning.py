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
        "tourist_flat",
        "missing",
        "exempt_seasonal",
        "missing",
        "hotel_or_hostel",
        "tourist_flat",
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


def test_stay_band_splits_at_31_nights():
    bands = cleaning.stay_band(pd.Series([30, 31, 32, np.nan]))
    assert bands.tolist()[:3] == ["tourist", "boundary", "seasonal"]
    assert pd.isna(bands.iloc[3])


def test_professional_flag():
    out = cleaning.add_columns(toy_data())
    assert out.loc[out["id"] == 2, "is_professional"].item() == True
    assert out.loc[out["id"] == 1, "is_professional"].item() == False


def test_tourist_flat_codes_in_other_regions():
    section = "Region - Regional registration number<br />"
    codes = {
        "VT-12345": "tourist_flat",  # Madrid
        "VT-12345-V": "tourist_flat",  # Valencia
        "VT12345": "tourist_flat",  # Madrid, no hyphen
        "CV-VUT0012345-V": "tourist_flat",  # Valencia
        "VFT/MA/12345": "tourist_flat",  # Andalucía
        "VUT-SE-12345": "tourist_flat",  # Andalucía, hyphen variant
        "CTC-2024123456": "other_code",  # generic Andalusian register ID
        "HM-1234": "other_code",  # type not confirmed
        "not available": "other",
    }
    for code, expected in codes.items():
        assert cleaning.regional_licence(section + code) == expected


def test_hut_number_matches_register_format():
    assert cleaning.hut_number(REGIONAL + "HUTB-012345") == "12345"
    assert cleaning.hut_number("HUTB- 012345") == "12345"   # register spacing
    assert cleaning.hut_number(REGIONAL + "Exempt - seasonal rental") is None


def test_listing_hut_number_ignores_national_section():
    glued = NATIONAL + "ESFCTU0000080190000123450000000000HUTB-0123456789"
    assert cleaning.listing_hut_number(glued) is None
    assert cleaning.listing_hut_number(REGIONAL + "HUTB-012345" + GAP + glued) == "12345"
