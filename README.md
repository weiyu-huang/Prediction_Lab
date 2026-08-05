# Prediction Lab

Prediction Lab is a quantitative research laboratory for understanding probabilistic markets. The first milestone is a clean, reproducible dataset of Big Five European soccer matches and closing 1X2 odds.

See [Vision and Principles](docs/vision_and_principles.md), the [Roadmap](docs/roadmap.md), and the [v0 validation report](reports/validation_report_v0.md).

## Phase 0 — Big Five Dataset v0

The dataset covers the 2024–25 and 2025–26 completed seasons for:

- Premier League (`E0`)
- Bundesliga (`D1`)
- La Liga (`SP1`)
- Serie A (`I1`)
- Ligue 1 (`F1`)

### Environment

```bash
conda activate soccer
python -m pip install -r requirements.txt
```

The project uses the existing Conda environment named `soccer`. The requirements file records the reproducible dependency versions for the dataset build.

Download the league CSV files manually from [football-data.co.uk](https://www.football-data.co.uk/data.php) and place them in:

```text
data/raw/
├── 2024-2025/
│   ├── premier_league.csv
│   ├── laliga.csv
│   ├── bundesliga.csv
│   ├── serie_a.csv
│   └── ligue1.csv
└── 2025-2026/
    ├── premier_league.csv
    ├── laliga.csv
    ├── bundesliga.csv
    ├── serie_a.csv
    └── ligue1.csv
```

Raw files are source artifacts and must not be modified.

### Build

```bash
python src/build_dataset.py
```

The command validates the inputs and writes:

- `data/processed/matches.csv`
- `data/processed/matches.parquet`

Both raw and processed datasets are intentionally versioned in Git. Football-data.co.uk kickoff values are interpreted as UK local time, including GMT/BST daylight-saving rules, and converted to UTC for `kickoff_time_utc`. The original source clock value remains unchanged in `time`.

## Phase 1 — Market Calibration

Run the complete calibration analysis with:

```bash
python src/analyze_calibration.py
```

The analysis removes the 1X2 bookmaker overround by normalizing inverse closing odds, then measures Home / Draw / Away calibration overall, by league, and by season using 20 quantile bins. Tables, supporting figures, and the generated report are written to `reports/phase1_market_calibration/`.
