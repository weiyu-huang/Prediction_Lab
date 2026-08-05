"""Build the Phase 0 Big Five match dataset from manually downloaded CSVs."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SEASONS = ("2024-2025", "2025-2026")
LEAGUE_FILES = {
    "E0": "premier_league.csv",
    "D1": "bundesliga.csv",
    "SP1": "laliga.csv",
    "I1": "serie_a.csv",
    "F1": "ligue1.csv",
}
LEAGUES = tuple(LEAGUE_FILES)
RAW_COLUMNS = (
    "Div",
    "Date",
    "Time",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
    "AvgCH",
    "AvgCD",
    "AvgCA",
)
FINAL_COLUMNS = (
    "match_id",
    "league",
    "date",
    "time",
    "kickoff_time_utc",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    "home_odds",
    "draw_odds",
    "away_odds",
)


def load_matches() -> pd.DataFrame:
    """Load and concatenate all expected raw league CSV files."""
    missing_files: list[str] = []
    frames: list[pd.DataFrame] = []

    for season in SEASONS:
        for league, filename in LEAGUE_FILES.items():
            path = RAW_DIR / season / filename
            if not path.is_file():
                missing_files.append(str(path.relative_to(ROOT)))
                continue
            frame = pd.read_csv(path, encoding="utf-8-sig")
            actual_leagues = set(frame["Div"].dropna().unique()) if "Div" in frame else set()
            if actual_leagues != {league}:
                raise ValueError(
                    f"{path.relative_to(ROOT)} should contain Div={league}, "
                    f"found {sorted(actual_leagues)}"
                )
            frame = frame[list(RAW_COLUMNS)].copy()
            frame["_season"] = season
            frame["_source_file"] = str(path.relative_to(ROOT))
            frames.append(frame)

    if missing_files:
        formatted = "\n  - ".join(missing_files)
        raise FileNotFoundError(f"Missing expected raw CSV files:\n  - {formatted}")

    return pd.concat(frames, ignore_index=True, sort=False)


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


def sanity_check(matches: pd.DataFrame, *, processed: bool = False) -> None:
    """Validate schema, values, missing data, duplicates, and row counts."""
    required = set(FINAL_COLUMNS if processed else RAW_COLUMNS)
    missing_columns = sorted(required.difference(matches.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    missing_counts = matches[list(required)].isna().sum()
    missing_counts = missing_counts[missing_counts > 0]
    if not missing_counts.empty:
        raise ValueError(f"Required values are missing:\n{missing_counts.to_string()}")

    if processed:
        if matches["match_id"].duplicated().any():
            duplicates = matches.loc[matches["match_id"].duplicated(False), "match_id"]
            raise ValueError(f"Duplicate match_id values:\n{duplicates.to_string(index=False)}")
        if matches.duplicated().any():
            raise ValueError("Exact duplicate processed rows remain")
        if not matches["result"].isin(("H", "D", "A")).all():
            raise ValueError("result must contain only H, D, or A")
        for column in ("home_goals", "away_goals"):
            if (matches[column] < 0).any():
                raise ValueError(f"{column} contains negative values")
        for column in ("home_odds", "draw_odds", "away_odds"):
            if (matches[column] <= 1).any():
                raise ValueError(f"{column} must be greater than 1")
        if pd.to_datetime(matches["kickoff_time_utc"], utc=True, errors="coerce").isna().any():
            raise ValueError("kickoff_time_utc contains invalid timestamps")

        counts = matches.groupby(["_season", "league"]).size()
        expected_groups = pd.MultiIndex.from_product(
            [SEASONS, LEAGUES], names=["_season", "league"]
        )
        counts = counts.reindex(expected_groups, fill_value=0)
        implausible = counts[(counts < 250) | (counts > 420)]
        if not implausible.empty:
            raise ValueError(
                "Implausible row counts (expected 250–420 per league-season):\n"
                f"{implausible.to_string()}"
            )


def process_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Select, rename, lightly normalize, sort, and deduplicate matches."""
    columns = list(RAW_COLUMNS) + ["_season", "_source_file"]
    result = matches[columns].copy()
    result = result.rename(
        columns={
            "Div": "league",
            "Date": "date",
            "Time": "time",
            "HomeTeam": "home_team",
            "AwayTeam": "away_team",
            "FTHG": "home_goals",
            "FTAG": "away_goals",
            "FTR": "result",
            "AvgCH": "home_odds",
            "AvgCD": "draw_odds",
            "AvgCA": "away_odds",
        }
    )

    parsed_dates = pd.to_datetime(result["date"], dayfirst=True, errors="coerce")
    if parsed_dates.isna().any():
        bad = result.loc[parsed_dates.isna(), ["_source_file", "date"]]
        raise ValueError(f"Invalid dates:\n{bad.to_string(index=False)}")
    result["date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    result["time"] = result["time"].astype("string").str.strip()
    result["kickoff_time_utc"] = pd.to_datetime(
        result["date"] + " " + result["time"], utc=True, errors="coerce"
    )
    if result["kickoff_time_utc"].isna().any():
        bad = result.loc[
            result["kickoff_time_utc"].isna(), ["_source_file", "date", "time"]
        ]
        raise ValueError(f"Invalid or missing kickoff times:\n{bad.to_string(index=False)}")

    result["match_id"] = result.apply(
        lambda row: (
            f"{row['league']}_{row['date']}_"
            f"{_slug(str(row['home_team']))}_{_slug(str(row['away_team']))}"
        ),
        axis=1,
    )

    result = result.drop_duplicates(subset=list(FINAL_COLUMNS)).sort_values(
        ["kickoff_time_utc", "league", "match_id"], ignore_index=True
    )
    return result


def main() -> None:
    """Build and save the processed CSV and Parquet datasets."""
    matches = load_matches()
    sanity_check(matches)
    processed = process_matches(matches)
    sanity_check(processed, processed=True)

    output = processed[list(FINAL_COLUMNS)]
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(PROCESSED_DIR / "matches.csv", index=False)
    output.to_parquet(PROCESSED_DIR / "matches.parquet", index=False)
    print(f"Built {len(output):,} matches in {PROCESSED_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
