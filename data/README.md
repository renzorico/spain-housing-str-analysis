# Data

Everything in `data/raw/` is downloaded by one script and never committed:

```bash
python scripts/download_data.py
```

Every URL and local path is listed once, in [`src/sources.py`](../src/sources.py).
The script skips files that already exist, so it is safe to re-run.

## Sources

| Source | What | Files | Licence |
|---|---|---|---|
| [Inside Airbnb](https://insideairbnb.com/get-the-data/) | Airbnb listings, summary file (19 columns) | Barcelona: 4 quarterly snapshots (Dec 2025 – Sep 2026). Madrid, Valencia, Málaga, Sevilla: Dec 2025 and Sep 2026. Plus each city's `neighbourhoods.geojson` | CC BY 4.0 |
| [Ajuntament de Barcelona](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/habitatges-us-turistic) | Official register of tourist flats (HUT) | Quarterly, 2025 Q1 – 2026 Q3 (2026 Q2 not published) | CC BY 4.0 |
| [Generalitat de Catalunya](https://analisi.transparenciacatalunya.cat/d/qww9-bvhh) | Average monthly rent of new leases (Incasòl deposits) | Barcelona and Girona, quarterly and yearly | CC BY 4.0 |

Layout:

```
data/raw/
├── insideairbnb/<city>/<snapshot>/listings.csv
├── insideairbnb/<city>/neighbourhoods.geojson
├── hut_register/<year>_<quarter>T.csv.zip
└── rents/incasol_rents.json
```

## Known data-quality issues

| Issue | Where | How the project handles it |
|---|---|---|
| `price` is missing on **100%** of rows | Every Dec 2025 snapshot, all cities | Price trends use Mar, Jun and Sep 2026 only. Counts and licences still use Dec |
| Listings with **zero open dates** jump to ~22–24% | Every Sep 2026 snapshot, all cities (1–6% in Dec outside Barcelona and Madrid) | Every over-time metric uses `is_active` (`availability_365 > 0`), the same rule for every snapshot. The jump is reported, not explained |
| `minimum_nights` missing on 7–18% of rows | Sep 2026 snapshots only | All such rows have zero open dates, so `is_active` already excludes them |
| No district-level rents | Generalitat publishes municipality level only | Rents appear as a Barcelona time series, not by district |

## The Inside Airbnb columns used

| Column | Meaning |
|---|---|
| `price` | Nightly asking price in **euros** |
| `minimum_nights` | Minimum stay. In Catalonia, 31 or fewer = tourist use; more = seasonal let |
| `room_type` | Entire home/apt · Private room · Shared room · Hotel room |
| `neighbourhood_group` | District |
| `calculated_host_listings_count` | How many listings this host runs in the city |
| `availability_365` | Nights bookable in the next 365 days |
| `number_of_reviews`, `number_of_reviews_ltm` | Review counts (lifetime, last 12 months) |
| `license` | Free text. See the privacy note |

Full definitions: [official data dictionary](https://docs.google.com/spreadsheets/d/1iWCNJcSutYqpULSQHlNyGInUvHg2BoUGoNRIGa6Szc4/edit).

## Privacy

**`license` (Inside Airbnb).** Under EU rules this column can contain real
host names and home addresses. Never print or commit its raw contents.

It holds up to two labelled sections, separated by `<br />`: a **regional**
one and a **national** (NRUA) one, with the same structure in every Spanish
city. The project reads it only in `cleaning.regional_licence` and
`cleaning.national_licence`, and works only with the safe categories they
return:

| Column | Categories |
|---|---|
| `regional_licence` | `tourist_flat` (confirmed codes: Catalonia `HUTB-`, Madrid `VT`, Valencia `VT-…-V` / `VUT` / `CV-VUT`, Andalucía `VFT` / `VUT`) · `hotel_or_hostel` (Catalan `HB`, `AJ`, `ATB`) · `other_code` (a registration whose type is not confirmed, e.g. Andalucía's generic `CTC-`) · `exempt_seasonal` · `exempt_other` · `missing` · `other` |
| `national_licence` | `nrua_tourist` (code `ES..TU`) · `nrua_seasonal` (code `ES..NT`, declared non-tourist) · `exempt` · `missing` · `other` |

Because unconfirmed codes are not counted as `tourist_flat`, tourist-flat
shares **outside Catalonia are a lower bound**.

**HUT register (Ajuntament).** Official public data, but it lists each flat
down to floor and door. The project only ever publishes counts by district
or neighbourhood, never addresses or coordinates of single flats.

## Attribution

> Data from Inside Airbnb (insideairbnb.com), licensed under CC BY 4.0.
> Habitatges d'ús turístic, Ajuntament de Barcelona, CC BY 4.0.
> Preu mitjà del lloguer d'habitatges per municipi, Generalitat de
> Catalunya (Incasòl), CC BY 4.0.
