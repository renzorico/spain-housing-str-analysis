# Agent context

Barcelona / Spain short-term rental analysis, mirroring
`../berlin-airbnb-market-analysis`. Python, pandas, Jupyter, pytest.

- Run tests: `.venv/bin/python -m pytest -q`
- Thresholds, dates and laws live only in `src/config.py`.
- The raw `license` column is personal data: read it only in
  `cleaning.licence_type`, never print it.
- Neutrality: describe rules as policy levers (what it says / what the data
  shows / what it cannot show). Never name parties or give verdicts.
- Commits: small, short lowercase messages, no co-author trailer. The owner
  pushes.
