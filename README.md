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
| Tourist-licence phase-out | Barcelona's ~10,000 HUT licences end in Nov 2028 (Decret llei 3/2023) | Share of listings with an HUT number, by district and host type |
| Rent cap | New leases in stressed areas capped by the reference index (Ley 12/2023) | Not directly: Airbnb prices are nightly, not leases |
| Seasonal rentals | Cap extended to seasonal (temporada) lets (Llei 11/2025) | Whether minimum stays bunch just above 31 nights |
| Owners' veto | Owners' associations can block new tourist lets (LO 1/2025) | Not directly: no building-level data in the file |

All dates and law numbers are in `src/config.py` (`POLICY_LEVERS`).

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
