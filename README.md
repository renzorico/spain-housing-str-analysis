# Barcelona's Short-Term Rental Market and the Rules Around It

Airbnb listings in Barcelona (Inside Airbnb snapshot), analysed in Python
against the housing rules now in force in Catalonia and Spain. Each rule is
treated as a **policy lever**: what it says, what the data shows, and what
the data cannot show. No verdicts, no party positions.

Context: Spain holds an early general election on 29 Nov 2026, and
municipal elections on 23 May 2027. Housing is a central issue in both.

---

## Policy levers checked against the data

| Lever | Rule | What the data can show |
|---|---|---|
| Tourist-licence phase-out | Existing tourist flats (HUT) need an urban-planning licence by 9 Nov 2028 or must stop; one extension of up to 5 years can be requested (Decret llei 3/2023, upheld by STC 64/2025) | Share of listings with an HUT number, by district and host type |
| Rent cap | New leases in stressed areas capped by the reference index since 16 Mar 2024 (Ley 12/2023); Barcelona's zone extended in Oct 2026 | Not directly: Airbnb prices are nightly, not leases |
| Seasonal rentals | Seasonal lets not for holidays count as housing leases, so the cap applies, since 1 Jan 2026 (Llei 11/2025; parts challenged at the Constitutional Court) | Whether minimum stays bunch around the 31-day line |
| Owners' veto | Owners' associations can block new tourist lets by a 3/5 vote since 3 Apr 2025, not retroactively (LO 1/2025) | Not directly: no building-level data in the file |

All dates, law numbers and primary sources (BOE / DOGC) are in
`src/config.py` (`POLICY_LEVERS`), checked on 22 Oct 2026.

---

## Project Structure

```
├── notebooks/       the analysis, in order
├── src/
│   ├── config.py    all thresholds, settings and policy levers in one place
│   └── cleaning.py  loading, cleaning rules, derived columns
├── tests/           quick checks on the cleaning rules
├── data/            gitignored - see data/README.md
└── reports/figures/ charts saved by the notebooks
```

---

## Running It

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# download listings.csv (Barcelona) from https://insideairbnb.com/get-the-data/
# and save it as data/raw/listings.csv

python -m pytest -q
jupyter lab notebooks/
```

No environment variables are needed.

---

## Licence

Code: MIT. Data © Inside Airbnb, [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/).
