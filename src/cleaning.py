"""Loading, cleaning and the derived columns.

Small functions. Each cleaning decision prints what it removed, so the
notebook shows a clear before/after story.
"""

import re

import pandas as pd

from . import config as cfg
from . import sources as src

# The raw licence field holds up to two labelled sections, e.g.
#   "Barcelona - Regional registration number<br />HUTB-012345<br /><br />
#    Spain - National registration number<br />ESFCTU0000...HUTB-012345"
# The structure is the same in every Spanish city; only the regional
# codes differ.
SECTION_END = r"(?:<br /><br />|$)"
REGIONAL_SECTION = re.compile(r"Regional registration number<br />(.*?)" + SECTION_END)
NATIONAL_SECTION = re.compile(r"National registration number<br />(.*?)" + SECTION_END)

# Regional tourist-flat licences, only prefixes confirmed in official or
# platform sources: Catalonia HUTB-; Madrid VT (with or without hyphen);
# Valencia VT-...-V, VUT and CV-VUT; Andalucía VFT and VUT (VFT was renamed
# VUT by Decreto 31/2024), with "/" or "-" separators and the frequent
# VTF typo. Andalucía's CTC- is a generic register ID for any establishment
# type, so it is NOT counted: tourist-flat shares outside Catalonia are a
# lower bound.
TOURIST_FLAT_CODE = re.compile(
    r"^(hut[bglt]-?\d|vt-?\d|(cv-)?vut-?\d|(vft|vtf|vut)[/\-][a-z]{2}[/\-])",
    re.IGNORECASE,
)
# Catalan non-flat codes: HB (hotel), AJ (youth hostel), ATB (tourist-
# apartment building).
HOTEL_CODE = re.compile(r"^(hb|aj|atb)-?\d", re.IGNORECASE)
# Any other code-like value (starts with letters, contains a digit):
# a regional registration whose type is not confirmed.
OTHER_CODE = re.compile(r"^[a-z]{1,4}[\-/]?[a-z]{0,2}[\-/]?\d", re.IGNORECASE)
# National registry (NRUA) codes: ES + unit (FC = whole home, HF = room)
# + declared use (TU = tourist, NT = non-tourist, i.e. seasonal).
NRUA_CODE = re.compile(r"^es[a-z]{2}(tu|nt)\d", re.IGNORECASE)


def load_listings() -> pd.DataFrame:
    """Read the raw file (and fail with a helpful message if it is missing)."""
    if not cfg.LISTINGS_FILE.exists():
        raise FileNotFoundError(
            f"{cfg.LISTINGS_FILE} not found. Run: python scripts/download_data.py"
        )
    return pd.read_csv(cfg.LISTINGS_FILE)


def load_snapshot(city: str, snapshot: str) -> pd.DataFrame:
    """Read one Inside Airbnb snapshot, tagged with its city and date."""
    path = src.listings_path(city, snapshot)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python scripts/download_data.py"
        )
    df = pd.read_csv(path, low_memory=False)
    return df.assign(city=city, snapshot=pd.Timestamp(snapshot))


def _section(value: object, pattern: re.Pattern) -> str | None:
    """Return the stripped text of one labelled section, or None."""
    if pd.isna(value):
        return None
    match = pattern.search(str(value))
    return match.group(1).strip() if match else None


def regional_licence(value: object) -> str:
    """Category of the regional licence section.

    PRIVACY: the raw field can contain personal data under EU rules. The
    two *_licence functions are the only places it is read - everywhere
    else uses the categories they return.
    """
    text = _section(value, REGIONAL_SECTION)
    if not text:
        return "missing"
    if TOURIST_FLAT_CODE.search(text):
        return "tourist_flat"  # e.g. Barcelona's HUT licence
    if HOTEL_CODE.search(text):
        return "hotel_or_hostel"
    if text.lower().startswith("exempt - seasonal"):
        return "exempt_seasonal"  # host declares a seasonal let
    if text.lower().startswith("exempt"):
        return "exempt_other"  # hotel, hostel, camping, ...
    if OTHER_CODE.search(text):
        return "other_code"  # registered, type not confirmed
    return "other"


HUT_NUMBER = re.compile(r"hut[bglt]-?\s*(\d+)", re.IGNORECASE)


def hut_number(value: object) -> str | None:
    """The Catalan HUT registration number in a licence entry, normalised
    to digits without leading zeros so Airbnb and the official register
    can be matched. A public register ID, not personal data; only counts
    of matches are ever reported."""
    if pd.isna(value):
        return None
    match = HUT_NUMBER.search(str(value))
    return match.group(1).lstrip("0") or "0" if match else None


def listing_hut_number(value: object) -> str | None:
    """HUT number from a listing's REGIONAL section only. In the national
    section the HUT number is glued to the NRUA code with no separator, so
    neighbouring digits get absorbed and the number no longer matches."""
    return hut_number(_section(value, REGIONAL_SECTION))


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
    """Label each listing by the minimum stay it asks, against the 31-night
    line: under_31, exactly_31 or over_31. These are observed settings, not
    legal classes (exactly 31 is where the legal reading is ambiguous; see
    config). Missing minimum stays stay missing.
    """
    band = pd.Series(pd.NA, index=minimum_nights.index, dtype="string")
    band[minimum_nights < cfg.STAY_LINE_NIGHTS] = "under_31"
    band[minimum_nights == cfg.STAY_LINE_NIGHTS] = "exactly_31"
    band[minimum_nights > cfg.STAY_LINE_NIGHTS] = "over_31"
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
    out["has_tourist_licence"] = out["regional_licence"] == "tourist_flat"
    # Same rule for every snapshot and city: missing minimum stays occur
    # only in listings with no open dates, and their share jumps in the
    # Sep 2026 snapshots of every city (see data/README.md).
    out["is_active"] = out["availability_365"] > 0
    return out


def clean_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to priced listings with open dates, printing each step.

    The population is the same one the website and src/metrics.py use:
    listings with at least one open date (is_active), so notebook and site
    numbers describe the same listings. Listings asking over 31 nights are
    KEPT: the rent limit on seasonal lets is one of the levers under study.
    Split on stay_band.
    """
    df = add_columns(df)
    print(f"start:                                  {len(df):>6,} listings")

    df = df[df["is_active"]]
    print(f"with open dates (the site's population): {len(df):>5,}")

    df = df[df["price"].notna() & (df["price"] > 0) & (df["price"] <= cfg.MAX_PRICE)]
    print(f"with a usable price (<= {cfg.MAX_PRICE} EUR):       {len(df):>6,}")

    # A listing with open dates always has a minimum stay in these files, so
    # no listing is dropped here for lacking one; the check keeps that true.
    assert df["minimum_nights"].notna().all(), "listing with open dates but no minimum stay"

    return df.reset_index(drop=True)
