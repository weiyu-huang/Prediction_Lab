"""Analyze closing-market calibration for the Big Five dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "matches.parquet"
REPORT_DIR = ROOT / "reports" / "phase1_market_calibration"
OUTCOMES = ("home", "draw", "away")
RESULT_CODES = {"home": "H", "draw": "D", "away": "A"}
ODDS_COLUMNS = {"home": "home_odds", "draw": "draw_odds", "away": "away_odds"}
LEAGUE_NAMES = {
    "E0": "Premier League",
    "D1": "Bundesliga",
    "SP1": "La Liga",
    "I1": "Serie A",
    "F1": "Ligue 1",
}
LEAGUE_ALIASES = {
    "e0": "E0",
    "epl": "E0",
    "premier league": "E0",
    "d1": "D1",
    "bundesliga": "D1",
    "sp1": "SP1",
    "laliga": "SP1",
    "la liga": "SP1",
    "i1": "I1",
    "serie a": "I1",
    "f1": "F1",
    "ligue 1": "F1",
    "ligue1": "F1",
}


class CalibrationAnalyzer:
    """Filter matches and generate quantile-binned calibration tables."""

    def __init__(
        self,
        filter: dict[str, list[str]] | None = None,
        outcome: str = "home",
        num_bins: int = 20,
        data_path: Path | str = DATA_PATH,
    ) -> None:
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}")
        if num_bins < 2:
            raise ValueError("num_bins must be at least 2")
        self.filter = filter or {}
        self.outcome = outcome
        self.num_bins = num_bins
        self.data_path = Path(data_path)
        self.matches = self._load_and_prepare()

    @staticmethod
    def _season_from_date(dates: pd.Series) -> pd.Series:
        parsed = pd.to_datetime(dates)
        start_year = parsed.dt.year.where(parsed.dt.month >= 7, parsed.dt.year - 1)
        return start_year.astype(str) + "-" + (start_year + 1).astype(str)

    @staticmethod
    def _normalize_leagues(values: Iterable[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            key = str(value).strip().lower()
            if key not in LEAGUE_ALIASES:
                raise ValueError(f"Unknown league filter: {value}")
            normalized.append(LEAGUE_ALIASES[key])
        return normalized

    def _load_and_prepare(self) -> pd.DataFrame:
        if not self.data_path.is_file():
            raise FileNotFoundError(f"Processed dataset not found: {self.data_path}")
        matches = pd.read_parquet(self.data_path)
        matches["season"] = self._season_from_date(matches["date"])

        inverse_odds = pd.DataFrame(
            {
                outcome: 1 / matches[column]
                for outcome, column in ODDS_COLUMNS.items()
            }
        )
        overround = inverse_odds.sum(axis=1)
        for outcome in OUTCOMES:
            matches[f"{outcome}_prob"] = inverse_odds[outcome] / overround

        unknown_filters = set(self.filter).difference(("league", "season"))
        if unknown_filters:
            raise ValueError(f"Unsupported filters: {sorted(unknown_filters)}")
        if "league" in self.filter:
            leagues = self._normalize_leagues(self.filter["league"])
            matches = matches[matches["league"].isin(leagues)]
        if "season" in self.filter:
            matches = matches[matches["season"].isin(self.filter["season"])]
        if matches.empty:
            raise ValueError("Filters returned no matches")
        return matches.reset_index(drop=True)

    def calibration_table(self, outcome: str | None = None) -> pd.DataFrame:
        """Return the source-of-truth calibration table for one outcome."""
        outcome = outcome or self.outcome
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}")
        probability = self.matches[f"{outcome}_prob"]
        bin_count = min(self.num_bins, probability.nunique())
        bins = pd.qcut(probability, q=bin_count, labels=False, duplicates="drop")
        working = pd.DataFrame(
            {
                "bin": bins + 1,
                "predicted": probability,
                "observed": (self.matches["result"] == RESULT_CODES[outcome]).astype(int),
            }
        )
        table = (
            working.groupby("bin", observed=True)
            .agg(avg_pred=("predicted", "mean"), actual=("observed", "mean"), count=("observed", "size"))
            .reset_index()
        )
        table["bin"] = table["bin"].astype(int)
        table["error"] = table["actual"] - table["avg_pred"]
        return table[["bin", "avg_pred", "actual", "error", "count"]]

    def all_outcomes(self) -> pd.DataFrame:
        """Return calibration tables for Home / Draw / Away."""
        tables = []
        for outcome in OUTCOMES:
            table = self.calibration_table(outcome)
            table.insert(0, "outcome", outcome)
            tables.append(table)
        return pd.concat(tables, ignore_index=True)


def _grouped_analysis(group_column: str) -> pd.DataFrame:
    base = CalibrationAnalyzer()
    if group_column == "league":
        groups = [league for league in LEAGUE_NAMES if league in set(base.matches["league"])]
    else:
        groups = sorted(base.matches[group_column].unique())
    tables = []
    for group in groups:
        analyzer = CalibrationAnalyzer(filter={group_column: [group]})
        table = analyzer.all_outcomes()
        label = LEAGUE_NAMES[group] if group_column == "league" else group
        table.insert(0, group_column, label)
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


def _markdown_table(table: pd.DataFrame) -> str:
    display = table.copy()
    for column in ("avg_pred", "actual", "error"):
        display[column] = display[column].map(lambda value: f"{value:.3f}")
    headers = list(display.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---:" if h != "outcome" else "---" for h in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in display.itertuples(index=False, name=None)
    )
    return "\n".join(lines)


def _observations(table: pd.DataFrame, scope_columns: list[str]) -> list[str]:
    labels = scope_columns + ["outcome", "bin"]
    positive = table.loc[table["error"].idxmax()]
    negative = table.loc[table["error"].idxmin()]
    absolute = table.loc[table["error"].abs().idxmax()]

    def describe(row: pd.Series) -> str:
        scope = ", ".join(f"{column}={row[column]}" for column in labels)
        return f"{scope} (error {row['error']:+.3f}, n={int(row['count'])})"

    observations = [
        f"Largest positive deviation: {describe(positive)}.",
        f"Largest negative deviation: {describe(negative)}.",
        f"Largest absolute error: {describe(absolute)}.",
    ]
    low_count = table[table["count"] < 50]
    if low_count.empty:
        observations.append("No bin has fewer than 50 observations.")
    else:
        observations.append(
            f"{len(low_count)} of {len(table)} bins have fewer than 50 observations; "
            "their deviations are especially noisy."
        )
    return observations


def _write_report(
    overall: pd.DataFrame, by_league: pd.DataFrame, by_season: pd.DataFrame
) -> None:
    lines = [
        "# Phase 1 — Market Calibration",
        "",
        "## Research question",
        "",
        "How well do normalized average closing 1X2 market probabilities match observed Home / Draw / Away frequencies, and is the pattern stable across leagues and seasons?",
        "",
        "## Dataset and method",
        "",
        "The analysis uses all 3,504 Big Five matches from 2024-2025 and 2025-2026. For each match, inverse Home / Draw / Away closing odds are normalized to sum to one, removing the bookmaker overround. Each outcome is grouped into 20 quantile bins, so bins have similar sample sizes. Error is `actual probability - average inferred probability`.",
        "",
        "![Overall calibration](figures/overall.png)",
        "",
        "## Overall calibration",
        "",
    ]
    for outcome in OUTCOMES:
        lines.extend(
            [
                f"### {outcome.title()}",
                "",
                _markdown_table(overall[overall["outcome"] == outcome]),
                "",
            ]
        )
    lines.extend(["## By league", "", "![Calibration by league](figures/by_league.png)", ""])
    for league in by_league["league"].drop_duplicates():
        lines.extend([f"### {league}", "", _markdown_table(by_league[by_league["league"] == league]), ""])
    lines.extend(["## By season", "", "![Calibration by season](figures/by_season.png)", ""])
    for season in by_season["season"].drop_duplicates():
        lines.extend([f"### {season}", "", _markdown_table(by_season[by_season["season"] == season]), ""])
    lines.extend(["## Auto-generated observations", ""])
    for observation in _observations(overall, []):
        lines.append(f"- Overall: {observation}")
    for observation in _observations(by_league, ["league"]):
        lines.append(f"- By league: {observation}")
    for observation in _observations(by_season, ["season"]):
        lines.append(f"- By season: {observation}")
    lines.extend(
        [
            "",
            "## Human analysis and follow-up hypotheses",
            "",
            "_Add interpretation, competing explanations, and the next testable questions here._",
            "",
        ]
    )
    (REPORT_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    """Generate calibration tables, figures, observations, and report."""
    try:
        from .plotting import plot_calibration, plot_grouped_calibration
    except ImportError:  # Support direct execution: python src/analyze_calibration.py
        from plotting import plot_calibration, plot_grouped_calibration

    table_dir = REPORT_DIR / "tables"
    figure_dir = REPORT_DIR / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    overall = CalibrationAnalyzer().all_outcomes()
    by_league = _grouped_analysis("league")
    by_season = _grouped_analysis("season")

    overall.to_csv(table_dir / "overall.csv", index=False)
    by_league.to_csv(table_dir / "by_league.csv", index=False)
    by_season.to_csv(table_dir / "by_season.csv", index=False)
    plot_calibration(overall, "Overall market calibration", figure_dir / "overall.png")
    plot_grouped_calibration(by_league, "league", "Market calibration by league", figure_dir / "by_league.png")
    plot_grouped_calibration(by_season, "season", "Market calibration by season", figure_dir / "by_season.png")
    _write_report(overall, by_league, by_season)
    print(f"Wrote Phase 1 analysis to {REPORT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
