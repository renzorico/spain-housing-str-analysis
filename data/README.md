# Data

One file, downloaded by hand.

## How to get it

1. Open **https://insideairbnb.com/get-the-data/**
2. Scroll to **Barcelona, Catalonia, Spain**
3. Download **`listings.csv`**, the row described as *"Summary information
   and metrics for listings in Barcelona"*
4. Save it as **`data/raw/listings.csv`**
5. Write the snapshot date into `SNAPSHOT_DATE` in `src/config.py`

> Take `listings.csv`, **not** `listings.csv.gz`. Both are called
> "listings", but the `.gz` one is a different, much larger file.

## The main columns

| Column | Meaning |
|---|---|
| `price` | Nightly price in **euros** |
| `minimum_nights` | Minimum stay. 31 or fewer = tourist use in Catalonia; more = seasonal let |
| `room_type` | Entire home/apt · Private room · Shared room · Hotel room |
| `neighbourhood_group` | Barcelona district (10 values) |
| `calculated_host_listings_count` | How many Barcelona listings this host runs |
| `availability_365` | Nights bookable in the next 365 days |
| `number_of_reviews`, `reviews_per_month` | Review counts (whole lifetime) |
| `license` | Free text. See the privacy note |

Full definitions: [official data dictionary](https://docs.google.com/spreadsheets/d/1iWCNJcSutYqpULSQHlNyGInUvHg2BoUGoNRIGa6Szc4/edit).

## Privacy: the `license` column

Under EU rules this column can contain real host **names and home
addresses**. Never print or commit its raw contents.

In the Barcelona file it holds up to two labelled sections, separated by
`<br />`: a **regional** (Catalan) one and a **national** (NRUA) one. The
project reads it only in `cleaning.regional_licence` and
`cleaning.national_licence`, and works only with the safe categories they
return:

| Column | Categories |
|---|---|
| `regional_licence` | `hut` (tourist flat, `HUTB-`) · `hotel_or_hostel` (`HB`, `AJ`, `ATB`) · `exempt_seasonal` · `exempt_other` · `missing` · `other` |
| `national_licence` | `nrua_tourist` (code `ES..TU`) · `nrua_seasonal` (code `ES..NT`, declared non-tourist) · `exempt` · `missing` · `other` |

`minimum_nights` is missing on ~2,000 rows; all of them have no open dates.
They are dropped in cleaning because they cannot be placed on either side
of the 31-night line.

## Attribution

> Data from Inside Airbnb (insideairbnb.com), Barcelona snapshot,
> licensed under CC BY 4.0.
