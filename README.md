# The 31-Night Line

**Short-term rentals and housing rules in Barcelona and four Spanish cities:
what the data shows, and what it cannot show.**

**Live site:** https://renzorico.github.io/spain-housing-str-analysis/

![The 31-night line: Barcelona Airbnb listings by minimum stay](site/public/og-image.png)

Four quarterly snapshots of Airbnb listings (Dec 2025 – Sep 2026) for
Barcelona, plus Madrid, Valencia, Málaga and Sevilla, set against
Barcelona's official register of tourist flats and official rents of new
leases. Each housing rule is treated as a **policy lever**: what it says,
what the data shows, and what the data cannot show. No verdicts, no party
positions.

Context: Spain holds an early general election on 29 Nov 2026 and municipal
elections on 23 May 2027. Housing is a central issue in both.

---

## What the data shows

**1. Barcelona's market sits on the legal line.** In Catalonia a tourist flat
is let for "31 days or fewer". 42% of Barcelona's active listings ask for 31
nights or more, against 2–8% in the other four cities. Minimum stays pile up
at exactly 31 nights (2,504 listings) and 32 nights (2,505).

**2. 31 nights behaves like a seasonal let, not a tourist stay.** Only 0.8%
of 31-night listings show a tourist-flat (HUT) licence, against 67.9% of
listings under 31 nights. Their median asking price is €82.5 a night: close
to seasonal lets (€72) and far from tourist stays (€245).

**3. The seasonal-rent cap cannot be singled out.** Month-plus listings were
16.3 points more likely than tourist listings to leave Airbnb between
December and September (95% CI 14.9–17.8). But Valencia (+12.1), Málaga
(+21.1) and Sevilla (+15.5) show gaps of the same size, and the Catalan law
does not apply there. Only Madrid (+2.1) does not.

**4. Most licence numbers are real, and Airbnb shows less than half the
licensed market.** 83–86% of the HUT numbers on active listings exist in the
official register. Only 37–49% of the ~10,700 registered flats appear on
Airbnb with their number. The register has not shrunk ahead of the 2028
deadline.

**5. Supply is concentrated.** The largest 1% of hosts run 29% of
Barcelona's active listings (Madrid 28%, Valencia 16%). 65.7% of listings
with a tourist licence belong to hosts with 5+ listings.

**6. Rents of new leases.** Year-on-year growth went from +9.8% (Q1 2024,
just before the cap) to −8.9% (Q1 2025), then back to +4.6% (Q1 2026,
€1,137 a month). The timing is shown; the cause is not.

---

## How the conclusions were checked

- **Every comparison uses all the cities, not one.** Against Madrid alone,
  Barcelona's exit gap looked exceptional (difference +14.3 points,
  p < 10⁻²⁶). Against all four cities, it is not. The published conclusion is
  the second one. See notebook 03.
- **Suspicious numbers get a root cause before they get a sentence.** A first
  pass found only 60% of licence numbers matching the register. The cause was
  parsing: in the national registry code the HUT number is glued to other
  digits. Read from the regional field, the match is 86%. A test now pins
  this.
- **Data changes are reported, not hidden.** Airbnb added an "Exempt –
  seasonal rental" option to its licence form in June 2026, in every city,
  and every Dec 2025 snapshot has no prices. Licence categories are never
  compared across that change.
- **One definition per number.** The notebooks and the website read the same
  functions (`src/metrics.py`), and the website computes the numbers it
  quotes from the exported data.

---

## The rules checked against the data

| Lever | Rule | What the data can show |
|---|---|---|
| Tourist-licence phase-out | Existing tourist flats (HUT) need an urban-planning licence by 9 Nov 2028 or must stop; one extension of up to 5 years can be requested (Decret llei 3/2023, upheld by STC 64/2025) | Who holds licensed listings, and how the listings match the official register |
| Rent cap | New leases in stressed areas capped by the reference index since 16 Mar 2024 (Ley 12/2023); Barcelona's zone extended in Oct 2026 | The timing of rent changes, not their cause; Airbnb prices are nightly, not leases |
| Seasonal rentals | Seasonal lets not for holidays count as housing leases, so the cap applies, since 1 Jan 2026 (Llei 11/2025; parts challenged at the Constitutional Court) | How listings sit around the 31-night line, and how they changed after January |
| Owners' veto | Owners' associations can block new tourist lets by a 3/5 vote since 3 Apr 2025, not retroactively (LO 1/2025) | Nothing directly: the data has no building-level information |

All dates, law numbers and primary sources (BOE / DOGC) are in
`src/config.py` (`POLICY_LEVERS`), checked on 22 Oct 2026.

---

## Limitations

- **Asking terms, not behaviour.** Prices are asking prices, and a minimum
  stay is what a host asks for, not how long guests stay.
- **Airbnb only.** Listings on other platforms, or let directly, are not
  here; less than half of Barcelona's licensed flats appear on Airbnb.
- **A missing or unmatched licence is not proof of an illegal listing.**
  Seasonal lets and rooms in the host's home need no tourist licence, and an
  unmatched number can be a typo or a licence issued or cancelled in between.
- **Short window, few comparisons.** Three quarters of data; the other
  cities have only December and September snapshots, so the Dec–Mar dip in
  Barcelona cannot be separated from an ordinary winter pattern.
- **Data quality.** All Dec 2025 snapshots lack prices. The share of
  listings with no open dates jumps in every city's Sep 2026 snapshot, so
  only active listings are counted. Tourist-licence shares outside Catalonia
  are a lower bound (only confirmed regional codes are counted).
- **Rents are city-wide.** Official rents are published per municipality,
  not per district, and change with the mix of flats rented.
- **Correlations, not causes.** Nothing here was randomly assigned.

Details: [`data/README.md`](data/README.md).

---

## Project structure

```
├── notebooks/
│   ├── 01_cleaning_eda          one Barcelona snapshot: cleaning, the 31-night line, licences
│   ├── 02_statistics            confidence intervals, t-tests, z-tests, chi-square
│   ├── 03_change_over_time      four snapshots, five cities, listing flows, robustness check
│   └── 04_register_and_rents    official register vs listings, rents of new leases
├── src/
│   ├── config.py                thresholds, settings and policy levers (dates, laws, sources)
│   ├── sources.py               every raw-data URL and local path
│   ├── cleaning.py              loading, cleaning rules, licence parsing
│   ├── metrics.py               shared metrics for the notebooks and the site
│   └── official.py              loaders for the HUT register and rents
├── scripts/
│   ├── download_data.py         fetch all raw data into data/raw/
│   ├── export_site_data.py      write the site's JSON into site/public/data/
│   └── make_social_image.py     draw the social preview image from that JSON
├── site/                        Vite + TypeScript + Observable Plot + MapLibre
├── tests/                       cleaning rules, metrics, and a privacy check on the site data
├── data/                        gitignored raw data - see data/README.md
└── reports/figures/             charts saved by the notebooks
```

---

## Running it

**Analysis** (Python 3.12):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/download_data.py      # ~51 MB into data/raw/
python -m pytest -q
jupyter lab notebooks/
```

**Website** (Node 22+):

```bash
python scripts/export_site_data.py   # refresh site/public/data/
python scripts/make_social_image.py  # refresh site/public/og-image.png

cd site
npm ci
npm run dev                          # http://localhost:5173
npm run build                        # typecheck + build into site/dist/
```

No environment variables or API keys are needed. The basemap comes from
[OpenFreeMap](https://openfreemap.org).

**Deploy:** pushing to `main` runs `.github/workflows/deploy-site.yml`. It
checks the exported data for identifying fields, builds the site and
publishes it to GitHub Pages. One-time setup: in the repository settings,
set **Pages → Source** to **GitHub Actions**.

---

## Privacy

Under EU rules the Airbnb `license` field can contain host names and
addresses, and Barcelona's register lists each flat down to the door. Raw
licence text is read in three functions only (`src/cleaning.py`), register
addresses never leave `src/official.py`, and the website data contains no
listing ids, host ids, names, licence text or addresses.
`tests/test_export.py` checks this before every deploy.

---

## Licence and attribution

Code: [MIT](LICENSE). Data: [Inside Airbnb](https://insideairbnb.com/get-the-data/),
[Ajuntament de Barcelona](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/habitatges-us-turistic)
and [Generalitat de Catalunya](https://analisi.transparenciacatalunya.cat/d/qww9-bvhh),
all [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/). Basemap ©
OpenStreetMap contributors, OpenMapTiles, OpenFreeMap.
