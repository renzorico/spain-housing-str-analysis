# Agent context

Barcelona / Spain short-term rental analysis, published as an interactive,
mobile-first website. Started from `../berlin-airbnb-market-analysis`.

- Analysis: Python, pandas, Jupyter, pytest (`src/`, `notebooks/01-04`).
- Site: Vite + strict TypeScript + Observable Plot + MapLibre (`site/`).

## Commands

- Download raw data (~51 MB, gitignored): `.venv/bin/python scripts/download_data.py`
- Tests: `.venv/bin/python -m pytest -q`
- Export site data: `.venv/bin/python scripts/export_site_data.py` (writes
  `site/public/data/`, which is committed)
- Site: `cd site && npm run dev` / `npm run build` / `npx tsc --noEmit`

## Rules

- Thresholds, dates and laws live only in `src/config.py`; URLs and local
  paths only in `src/sources.py`.
- The raw `license` column is personal data: read it only in
  `cleaning.regional_licence`, `cleaning.national_licence` and
  `cleaning.listing_hut_number`; never print it. The HUT register's
  addresses never leave `src/official.py`. `tests/test_export.py` scans the
  site data for identifying fields.
- One definition per number: notebooks and the site export both use
  `src/metrics.py`. Site text that quotes numbers computes them from the
  exported data.
- Neutrality: describe rules as policy levers (what it says / what the data
  shows / what it cannot show). Never name parties or give verdicts.
  Compare across all cities, not one hand-picked comparison.
- Commits: small, short lowercase messages, no co-author trailer. The owner
  pushes.
