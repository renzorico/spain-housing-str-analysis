"""Loading, cleaning and the derived columns.

Four small functions. Each cleaning decision prints what it removed, so
the notebook shows a clear before/after story.
"""

import re

import pandas as pd

from . import config as cfg

# Catalan tourist-use licence, e.g. "HUTB-012345" (B = Barcelona province).
HUT_PATTERN = re.compile(r"(?<![a-z])hut[bglt]-?\d+", re.IGNORECASE)
# National registry code (NRUA), e.g. "ESFCTU0000080... ". Starts with ES.
NRUA_PATTERN = re.compile(r"\bes[a-z]{4}\d{6,}", re.IGNORECASE)


def load_listings() -> pd.DataFrame:
    """Read the raw file (and fail with a helpful message if it is missing)."""
    if not cfg.LISTINGS_FILE.exists():
        raise FileNotFoundError(
            "data/raw/listings.csv not found. Download the Barcelona summary "
            "file from https://insideairbnb.com/get-the-data/ (see data/README.md)."
        )
    return pd.read_csv(cfg.LISTINGS_FILE)


def licence_type(value: object) -> str:
    """Turn one raw licence entry into a safe category.

    PRIVACY: under EU rules this column can contain real host names and
    home addresses. This function is the only place the raw text is
    read - everywhere else uses the category it returns.
    """
    if pd.isna(value) or str(value).strip() == "":
        return "missing"
    text = str(value).lower()
    if HUT_PATTERN.search(text):
        return "hut"  # Catalan tourist licence
    if NRUA_PATTERN.search(text):
        return "nrua"  # national registry code only
    if "exempt" in text:
        return "exempt"  # host claims no licence is needed
    if "legal entity" in text:
        return "company"
    if "first name" in text:
        return "person"
    return "other"


def add_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add the handful of derived columns the notebooks use."""
    out = df.copy()
    out["is_entire_home"] = out["room_type"] == "Entire home/apt"
    out["is_tourist_stay"] = out["minimum_nights"] <= cfg.MAX_TOURIST_NIGHTS
    out["is_central"] = out["neighbourhood_group"].isin(cfg.CENTRAL_DISTRICTS)
    out["is_professional"] = (
        out["calculated_host_listings_count"] >= cfg.PROFESSIONAL_MIN
    )
    out["licence_type"] = out["license"].apply(licence_type)
    out["has_hut"] = out["licence_type"] == "hut"
    return out


def clean_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to the priced, active market, printing each step.

    Unlike Berlin, seasonal (> 31 nights) listings are KEPT: the seasonal
    rent cap is one of the levers under study. Split on is_tourist_stay.
    """
    df = add_columns(df)
    print(f"start:                              {len(df):>6,} listings")

    df = df[df["price"].notna() & (df["price"] > 0) & (df["price"] <= cfg.MAX_PRICE)]
    print(f"with a usable price (<= {cfg.MAX_PRICE} EUR):   {len(df):>6,}")

    df = df[(df["number_of_reviews"] > 0) | (df["availability_365"] > 0)]
    print(f"active (has reviews or open dates): {len(df):>6,}")

    return df.reset_index(drop=True)
