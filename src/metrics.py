"""Metrics shared by the notebooks and the site export.

Every function takes listings already passed through cleaning.add_columns,
so one definition of each number serves both the analysis and the site.
"""

import numpy as np
import pandas as pd

from . import config as cfg

BANDS = ["tourist", "boundary", "seasonal"]
# Status of a listing in a later snapshot, used for transitions.
GONE = "gone"
INACTIVE = "inactive"


def active(df: pd.DataFrame) -> pd.DataFrame:
    """Listings with at least one open date - the same rule for every
    snapshot and city (see data/README.md)."""
    return df[df["is_active"]]


def share(mask: pd.Series) -> float:
    """Share of True values, as a percentage rounded for display."""
    return round(float(mask.mean()) * 100, 1) if len(mask) else float("nan")


def snapshot_summary(df: pd.DataFrame) -> dict:
    """Headline numbers for one city snapshot (active listings only).

    Month-plus = minimum stay of 31 nights or more. It is a neutral,
    city-independent measure: the legal tourist/seasonal line differs
    between regions, so cross-city comparisons do not use stay bands.
    """
    act = active(df)
    priced = act[act["price"].between(1, cfg.MAX_PRICE)]
    return {
        "listings": int(len(df)),
        "active": int(len(act)),
        "share_31_nights": share(act["minimum_nights"] == cfg.MAX_TOURIST_NIGHTS),
        "share_month_plus": share(act["minimum_nights"] >= cfg.MAX_TOURIST_NIGHTS),
        "share_tourist_licence": share(act["has_tourist_licence"]),
        "share_nrua_seasonal": share(act["national_licence"] == "nrua_seasonal"),
        "share_professional": share(act["is_professional"]),
        "share_entire_home": share(act["is_entire_home"]),
        "median_price": float(priced["price"].median()) if len(priced) else None,
    }


def band_counts(df: pd.DataFrame) -> dict:
    """Active listings per stay band (Catalan legal line)."""
    counts = active(df)["stay_band"].value_counts()
    return {band: int(counts.get(band, 0)) for band in BANDS}


def concentration_curve(df: pd.DataFrame, points: int = 50) -> pd.DataFrame:
    """Lorenz-style curve: the top X% of hosts run Y% of active listings.

    Hosts are ranked from largest to smallest so the curve reads
    "the biggest 1% of hosts run ...". Uses host_id, never host names.
    """
    per_host = active(df).groupby("host_id")["id"].count().sort_values(ascending=False)
    host_share = np.arange(1, len(per_host) + 1) / len(per_host) * 100
    listing_share = per_host.cumsum().to_numpy() / per_host.sum() * 100
    picks = np.unique(np.linspace(0, len(per_host) - 1, points).round().astype(int))
    return pd.DataFrame(
        {
            "host_share": host_share[picks].round(2),
            "listing_share": listing_share[picks].round(2),
        }
    )


def top_host_share(df: pd.DataFrame, top_percent: float) -> float:
    """Share of active listings run by the largest top_percent of hosts."""
    curve = concentration_curve(df, points=1000)
    return float(
        np.interp(top_percent, curve["host_share"], curve["listing_share"]).round(1)
    )


def status_in(later: pd.DataFrame) -> pd.Series:
    """Each listing's status in a later snapshot: its stay band if
    active, otherwise 'inactive'. Indexed by listing id."""
    status = later["stay_band"].astype("object").where(later["is_active"], INACTIVE)
    return status.set_axis(later["id"]).fillna(INACTIVE)


def transitions(earlier: pd.DataFrame, later: pd.DataFrame) -> pd.DataFrame:
    """Where did the active listings of `earlier` end up in `later`?

    Rows: stay band in the earlier snapshot. Columns: stay band in the
    later one, 'inactive' (still listed, no open dates) or 'gone'
    (no longer in the file). Values are listing counts.
    """
    start = active(earlier).set_index("id")["stay_band"]
    end = status_in(later).reindex(start.index).fillna(GONE)
    order = BANDS + [INACTIVE, GONE]
    table = pd.crosstab(start, end).reindex(index=BANDS, columns=order, fill_value=0)
    return table.astype(int)


def exit_gap(table: pd.DataFrame) -> tuple[float, float]:
    """From a transitions table: (exit rate of month-plus listings) minus
    (exit rate of tourist listings), in percentage points, with its
    standard error. Month-plus = boundary + seasonal (31+ nights)."""
    month_plus = table.loc[["boundary", "seasonal"]].sum()
    tourist = table.loc["tourist"]
    p1, n1 = month_plus[GONE] / month_plus.sum(), month_plus.sum()
    p2, n2 = tourist[GONE] / tourist.sum(), tourist.sum()
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return float((p1 - p2) * 100), float(se * 100)
