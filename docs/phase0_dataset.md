# Prediction Lab — Big Five Dataset v0

## Goal

Build a minimal, reproducible dataset containing the past two completed seasons of Big Five European soccer matches: Premier League, Bundesliga, La Liga, Serie A, and Ligue 1.

Use manually downloaded CSV files from `football-data.co.uk`. The dataset contains one row per match, with closing 1X2 market odds and the final result.

## Inputs and outputs

Original, unmodified files belong under `data/raw/2024-2025/` and `data/raw/2025-2026/`. Each season directory contains `premier_league.csv`, `laliga.csv`, `bundesliga.csv`, `serie_a.csv`, and `ligue1.csv`. The build produces `data/processed/matches.csv` and `data/processed/matches.parquet`. Both raw and processed data are committed to Git.

## Processed schema

| Raw | Processed |
| --- | --- |
| `Div` | `league` |
| `Date` | `date` |
| `Time` | `time` |
| `HomeTeam` | `home_team` |
| `AwayTeam` | `away_team` |
| `FTHG` | `home_goals` |
| `FTAG` | `away_goals` |
| `FTR` | `result` |
| `AvgCH` | `home_odds` |
| `AvgCD` | `draw_odds` |
| `AvgCA` | `away_odds` |

The build adds a deterministic `match_id` and a UTC-aware `kickoff_time_utc`. The match ID is formed from league, date, normalized home team, and normalized away team; displayed team names remain unchanged.

## Processing and validation

The single-file pipeline loads all inputs, validates raw data, processes matches, validates the output, and saves both formats. It rejects missing inputs or values, invalid results, negative goals, odds at or below 1, invalid kickoff times, duplicate match IDs, and implausible league-season row counts.

Football-data kickoff values are interpreted as UK local time using `Europe/London` timezone rules, including GMT/BST daylight-saving transitions, and converted to UTC. The original source clock value is preserved in `time`. Several matches should be manually verified against an independent source before the dataset is considered final.

## Scope boundaries

Phase 0 does not download data programmatically, calculate probabilities or vig, add ratings or model features, ingest prediction-market data, globally normalize team names, add extra match statistics, or introduce notebooks and experiment infrastructure.
