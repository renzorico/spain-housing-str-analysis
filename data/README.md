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
| Listings with **zero open dates** jump to ~22–24% | Every Sep 2026 snapshot, all cities (1–6% in Dec outside Barcelona and Madrid) | Every metric on the site and in the notebooks uses one population, *listings with open dates* (`is_active`: `availability_365 > 0`), the same rule for every snapshot. The jump is reported, not explained |
| `minimum_nights` missing on 7–18% of rows | Sep 2026 snapshots only | All such rows have zero open dates, so `is_active` already excludes them |
| Airbnb's licence form changed | The *Exempt – seasonal rental* option appears between the Mar and Jun 2026 snapshots in Barcelona (0 to 2,881 listings with open dates) and is used in Madrid (6,833) and Valencia (1,450) by Sep 2026, but almost never in Málaga (4) or Sevilla (0). Empty licence fields fall in every city | Licence categories are compared within a snapshot, never as a before/after effect of a rule |
| `calculated_host_listings_count` missing | 113 listings with open dates in Barcelona Jun 2026 (0.8%) | Counted as not professional in shares; shown as host size "unknown" on the site |
| No district-level rents | Generalitat publishes municipality level only | Rents appear as a Barcelona time series, not by district |

## Definitions used everywhere

| Term | Meaning |
|---|---|
| **Listings with open dates** | Listings with at least one open date in the next 365 days (`availability_365 > 0`). The only population the site and the notebooks count, so their numbers describe the same listings. "Active" is shorthand in code only: an empty calendar can mean booked, blocked or withdrawn |
| **Listed, no open dates** | Still in a later file, but with no open dates |
| **Absent from the later scrape** | Not in the later file. May be withdrawn, re-listed under a new id, or missed by the scrape; the data cannot say which |
| **Under 31 / exactly 31 / over 31** | The minimum stay a listing asks, against the Catalan 31-day tourist-stay limit. Across cities, **31+ ("month-plus")** is only a common measurement threshold |
| **Host account** | One `host_id`. Not necessarily one owner or one company |
| **Register records / numbers** | Records are administrative case ids (the headline stock); numbers are distinct parseable HUT numbers. A few records have no usable number, so the two differ (10,721 vs 10,623 in 2026 Q3) |
| **Match to the register** | A displayed number exists in the register quarter nearest in time to the snapshot. It does not verify that the listing is that property |

## The Inside Airbnb columns used

| Column | Meaning |
|---|---|
| `price` | Nightly asking price in **euros** |
| `minimum_nights` | Minimum stay the host asks. Labelled *under 31*, *exactly 31* or *over 31* nights, never by legality: the Catalan tourist-stay limit is 31 days, and a minimum stay is a setting, not a contract or an actual stay |
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
