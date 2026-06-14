# FFTT Club Scraper

Small utilities to scrape and analyze FFTT (French table tennis) match
results for any club.

## Contents
- `src/scraping/client.py` — HTML scraping client (`FFTTClient`) that converts
  match pages into pandas DataFrames.
- `src/scraping/stats.py` — helpers to compute player/pair statistics and
  performance metrics.
- `src/scraping/plot.py` — plotting helpers for quick visualization of results.
- `src/scraping/report.py` — Excel report builder for match and player statistics.

## Requirements
- Python 3.8+
- Packages: `requests`, `pandas`, `numpy`, `beautifulsoup4`, `loguru`,
  `matplotlib`, `openpyxl`

Install dependencies (example):

```bash
python -m pip install requests pandas numpy beautifulsoup4 loguru matplotlib openpyxl
```

## Configuration
The scraper expects a local JSON config file containing an FFTT login id
(default path: repository root file named `.fftt_config`). Example content:

```json
{ "lid": "your_lid_here" }
```

Place the file at the repo root or pass a custom path to `FFTTClient` via
the `config_path` argument.

## Quick usage

```python
from scraping.client import FFTTClient
from scraping.stats import compute_perfs, analyze_home_away_performance
from scraping.plot import plot_team_series
from scraping.report import build_excel_report

# create client (reads .fftt_config by default)
client = FFTTClient()

# base URL for club schedules (example: club_id 11660007)
url = "https://www.pingpocket.fr/app/fftt/clubs/11660007/equipes/calendriers?phase="

matches_df, simples_df, doubles_df = client.scrape_club(club_id=11660007)

# compute performance stats
best, worst = compute_perfs(simples_df)

# analyze home/away
home_away = analyze_home_away_performance(simples_df)

# quick plot
plot_team_series(matches_df)

# generate Excel report
build_excel_report(matches_df, simples_df, doubles_df, output_path="report.xlsx")
```

## Notes
- The code is geared to the specific HTML structure used on the pingpocket
  FFTT pages; changes to that site may require parser updates in
  `FFTTClient._parse_match`.
- The scraper now works with any club by using the `club_id` parameter
  in `scrape_club()`. Simply provide the club ID from the FFTT website.

License: See `LICENSE` in this repository.
