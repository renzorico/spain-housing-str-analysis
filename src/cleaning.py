"""Loading, cleaning and the derived columns.

Small functions. Each cleaning decision prints what it removed, so the
notebook shows a clear before/after story.
"""

import re

import pandas as pd

from . import config as cfg

# The raw licence field holds up to two labelled sections, e.g.
#   "Barcelona - Regional registration number<br />HUTB-012345<br /><br />
#    Spain - National registration number<br />ESFCTU0000...HUTB-012345"
SECTION_END = r"(?:<br /><br />|$)"
REGIONAL_SECTION = re.compile(r"Regional registration number<br />(.*?)" + SECTION_END)
NATIONAL_SECTION = re.compile(r"National registration number<br />(.*?)" + SECTION_END)

# Catalan regional codes: HUTB = tourist flat (habitatge d'ús turístic),
# HB = hotel, AJ = youth hostel, ATB = tourist-apartment building.
HUT_CODE = re.compile(r"^hut[bglt]-?\d+", re.IGNORECASE)
HOTEL_CODE = re.compile(r"^(hb|aj|atb)-?\d+", re.IGNORECASE)
# National registry (NRUA) codes: ES + unit (FC = whole home, HF = room)
# + declared use (TU = tourist, NT = non-tourist, i.e. seasonal).
NRUA_CODE = re.compile(r"^es[a-z]{2}(tu|nt)\d", re.IGNORECASE)


def load_listings() -> pd.DataFrame:
    """Read the raw file (and fail with a helpful message if it is missing)."""
    if not cfg.LISTINGS_FILE.exists():
        raise FileNotFoundError(
            "data/raw/listings.csv not found. Download the Barcelona summary "
            "file from https://insideairbnb.com/get-the-data/ (see data/README.md)."
        )
    return pd.read_csv(cfg.LISTINGS_FILE)


def _section(value: object, pattern: re.Pattern) -> str | None:
    """Return the stripped text of one labelled section, or None."""
    if pd.isna(value):
        return None
    match = pattern.search(str(value))
    return match.group(1).strip() if match else None


def regional_licence(value: object) -> str:
    """Category of the Catalan (regional) licence section.

    PRIVACY: the raw field can contain personal data under EU rules. The
    two *_licence functions are the only places it is read - everywhere
    else uses the categories they return.
    """
    text = _section(value, REGIONAL_SECTION)
    if not text:
        return "missing"
    if HUT_CODE.search(text):
        return "hut"  # tourist flat licence
    if HOTEL_CODE.search(text):
        return "hotel_or_hostel"
    if text.lower().startswith("exempt - seasonal"):
        return "exempt_seasonal"  # host declares a seasonal let
    if text.lower().startswith("exempt"):
        return "exempt_other"  # hotel, hostel, camping, ...
    return "other"


def national_licence(value: object) -> str:
    """Category of the national registry (NRUA) section."""
    text = _section(value, NATIONAL_SECTION)
    if not text:
        return "missing"
    match = NRUA_CODE.search(text)
    if match:
        return "nrua_tourist" if match.group(1).lower() == "tu" else "nrua_seasonal"
    if text.lower().startswith("exempt"):
        return "exempt"
    return "other"


def stay_band(minimum_nights: pd.Series) -> pd.Series:
    """Place each listing on the tourist / seasonal line.

    "boundary" = exactly MAX_TOURIST_NIGHTS, where the legal reading is
    ambiguous (see config). Missing minimum stays stay missing.
    """
    band = pd.Series(pd.NA, index=minimum_nights.index, dtype="string")
    band[minimum_nights < cfg.MAX_TOURIST_NIGHTS] = "tourist"
    band[minimum_nights == cfg.MAX_TOURIST_NIGHTS] = "boundary"
    band[minimum_nights > cfg.MAX_TOURIST_NIGHTS] = "seasonal"
    return band


def add_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add the handful of derived columns the notebooks use."""
    out = df.copy()
    out["is_entire_home"] = out["room_type"] == "Entire home/apt"
    out["stay_band"] = stay_band(out["minimum_nights"])
    out["is_central"] = out["neighbourhood_group"].isin(cfg.CENTRAL_DISTRICTS)
    out["is_professional"] = (
        out["calculated_host_listings_count"] >= cfg.PROFESSIONAL_MIN
    )
    out["regional_licence"] = out["license"].apply(regional_licence)
    out["national_licence"] = out["license"].apply(national_licence)
    out["has_hut"] = out["regional_licence"] == "hut"
    return out


def clean_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to the priced, active market, printing each step.

    Unlike Berlin, seasonal (> 31 nights) listings are KEPT: the seasonal
    rent cap is one of the levers under study. Split on stay_band.
    """
    df = add_columns(df)
    print(f"start:                              {len(df):>6,} listings")

    df = df[df["price"].notna() & (df["price"] > 0) & (df["price"] <= cfg.MAX_PRICE)]
    print(f"with a usable price (<= {cfg.MAX_PRICE} EUR):   {len(df):>6,}")

    # Without a minimum stay a listing cannot be put on either side of
    # the 31-night line. In this file these rows also have no open dates.
    df = df[df["minimum_nights"].notna()]
    print(f"known minimum stay:                 {len(df):>6,}")

    df = df[(df["number_of_reviews"] > 0) | (df["availability_365"] > 0)]
    print(f"active (has reviews or open dates): {len(df):>6,}")

    return df.reset_index(drop=True)
