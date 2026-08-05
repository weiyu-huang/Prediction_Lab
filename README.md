# Prediction Lab

Prediction Lab is a quantitative research laboratory for understanding probabilistic markets. The first milestone is a clean, reproducible dataset of Big Five European soccer matches and closing 1X2 odds.

See [Vision and Principles](docs/vision_and_principles.md), the [Roadmap](docs/roadmap.md), and the [Phase 0 dataset specification](docs/phase0_dataset.md).

## Phase 0 — Big Five Dataset v0

The dataset covers the 2024–25 and 2025–26 completed seasons for:

- Premier League (`E0`)
- Bundesliga (`D1`)
- La Liga (`SP1`)
- Serie A (`I1`)
- Ligue 1 (`F1`)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Download the league CSV files manually from [football-data.co.uk](https://www.football-data.co.uk/data.php) and place them in:

```text
data/raw/2024_25/{E0,D1,SP1,I1,F1}.csv
data/raw/2025_26/{E0,D1,SP1,I1,F1}.csv
```

Raw files are source artifacts and must not be modified.

### Build

```bash
python src/build_dataset.py
```

The command validates the inputs and writes:

- `data/processed/matches.csv`
- `data/processed/matches.parquet`

Both raw and processed datasets are intentionally versioned in Git. Kickoff times from football-data.co.uk are treated as UTC in v0; this is an explicit simplifying assumption that should be manually spot-checked.
