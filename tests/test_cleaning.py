"""Quick checks on the cleaning rules.

A test = tiny made-up data where the right answer is known + an assert.
If a rule is ever changed by accident, one of these fails loudly.

Run with:  python -m pytest -q
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src import cleaning


def toy_data():
    """Five listings: a licensed tourist flat, an absurd price, a 32-night
    seasonal let, a dead one (no reviews, nothing bookable) and an
    'exempt' one."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "neighbourhood_group": [
                "Eixample",
                "Gràcia",
                "Sant Martí",
                "Ciutat Vella",
                "Les Corts",
            ],
            "room_type": [
                "Entire home/apt",
                "Private room",
                "Entire home/apt",
                "Private room",
                "Private room",
            ],
            "price": [120.0, 5000.0, 90.0, 55.0, 60.0],
            "minimum_nights": [2, 3, 32, 1, 1],
            "number_of_reviews": [40, 12, 3, 0, 5],
            "calculated_host_listings_count": [1, 8, 1, 1, 1],
            "availability_365": [200, 150, 300, 0, 100],
            "license": [
                "HUTB-012345",
                "ESFCTU00000801200012345678900000000000000HUTB-0123456",
                None,
                "First name and Last name: Test Person",
                "Exempt",
            ],
        }
    )


def test_cleaning_drops_bad_price_and_dead_listing():
    out = cleaning.clean_listings(toy_data())
    assert list(out["id"]) == [1, 3, 5]


def test_licence_type_gives_safe_categories():
    cats = toy_data()["license"].apply(cleaning.licence_type)
    assert cats.tolist() == ["hut", "hut", "missing", "person", "exempt"]


def test_nrua_without_hut():
    assert cleaning.licence_type("ESFCTU0000080120001234") == "nrua"


def test_seasonal_split_at_31_nights():
    out = cleaning.add_columns(toy_data())
    assert out.loc[out["id"] == 1, "is_tourist_stay"].item() == True
    assert out.loc[out["id"] == 3, "is_tourist_stay"].item() == False


def test_professional_flag():
    out = cleaning.add_columns(toy_data())
    assert out.loc[out["id"] == 2, "is_professional"].item() == True
    assert out.loc[out["id"] == 1, "is_professional"].item() == False
