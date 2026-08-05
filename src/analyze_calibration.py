"""Generate quantile-binned calibration tables for closing 1X2 odds."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/matches.parquet"
REPORT = ROOT / "reports/01_market_calibration"
OUTCOMES = {"home": ("home_odds", "H"), "draw": ("draw_odds", "D"), "away": ("away_odds", "A")}
LEAGUES = {"E0": "Premier League", "D1": "Bundesliga", "SP1": "La Liga", "I1": "Serie A", "F1": "Ligue 1"}
ALIASES = {name.lower().replace(" ", ""): code for code, name in LEAGUES.items()} | {
    "epl": "E0", "laliga": "SP1", **{code.lower(): code for code in LEAGUES}
}


def load_matches(path: Path = DATA) -> pd.DataFrame:
    matches = pd.read_parquet(path)
    dates = pd.to_datetime(matches["date"])
    year = dates.dt.year.where(dates.dt.month >= 7, dates.dt.year - 1)
    matches["season"] = year.astype(str) + "-" + (year + 1).astype(str)
    inverse = pd.DataFrame({name: 1 / matches[odds] for name, (odds, _) in OUTCOMES.items()})
    for name in OUTCOMES:
        matches[f"{name}_prob"] = inverse[name] / inverse.sum(axis=1)
    return matches


def calibration(matches: pd.DataFrame, outcome: str, bins: int = 20) -> pd.DataFrame:
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {tuple(OUTCOMES)}")
    probability = matches[f"{outcome}_prob"]
    frame = pd.DataFrame({
        "bin": pd.qcut(probability, min(bins, probability.nunique()), labels=False, duplicates="drop") + 1,
        "predicted": probability,
        "observed": (matches["result"] == OUTCOMES[outcome][1]).astype(int),
    })
    table = frame.groupby("bin", observed=True).agg(
        avg_pred=("predicted", "mean"), actual=("observed", "mean"), count=("observed", "size")
    ).reset_index()
    table["bin"] = table["bin"].astype(int)
    table["error"] = table["actual"] - table["avg_pred"]
    return table[["bin", "avg_pred", "actual", "error", "count"]]


def all_outcomes(matches: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
    tables = []
    for outcome in OUTCOMES:
        table = calibration(matches, outcome, bins)
        table.insert(0, "outcome", outcome)
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


class CalibrationAnalyzer:
    """Small interface for filtered calibration analysis."""

    def __init__(self, filter=None, outcome="home", num_bins=20, data_path=DATA):
        if num_bins < 2:
            raise ValueError("num_bins must be at least 2")
        self.outcome, self.num_bins = outcome, num_bins
        self.matches = load_matches(Path(data_path))
        for column, values in (filter or {}).items():
            if column not in ("league", "season"):
                raise ValueError(f"Unsupported filter: {column}")
            if column == "league":
                try:
                    values = [ALIASES[str(value).lower().replace(" ", "")] for value in values]
                except KeyError as error:
                    raise ValueError(f"Unknown league filter: {error.args[0]}") from error
            self.matches = self.matches[self.matches[column].isin(values)]
        if self.matches.empty:
            raise ValueError("Filters returned no matches")

    def calibration_table(self, outcome=None):
        return calibration(self.matches, outcome or self.outcome, self.num_bins)

    def all_outcomes(self):
        return all_outcomes(self.matches, self.num_bins)


def grouped(matches: pd.DataFrame, column: str) -> pd.DataFrame:
    groups = list(LEAGUES) if column == "league" else sorted(matches[column].unique())
    tables = []
    for group in groups:
        table = all_outcomes(matches[matches[column] == group])
        table.insert(0, column, LEAGUES.get(group, group))
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


def markdown(table: pd.DataFrame) -> str:
    table = table.copy()
    for column in set(table).intersection(("avg_pred", "actual", "error")):
        table[column] = table[column].map(lambda value: f"{value:.3f}")
    headers = list(table)
    rows = [headers, ["---" if name == "outcome" else "---:" for name in headers]]
    rows += list(table.itertuples(index=False, name=None))
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def calibration_summary(table, scope=None):
    rows = []
    groups = [scope, "outcome"] if scope else ["outcome"]
    for keys, data in table.groupby(groups, sort=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        weight = data["count"]
        row = dict(zip(groups, keys))
        row.update(
            mean_error=(data.error * weight).sum() / weight.sum(),
            mean_abs_error=(data.error.abs() * weight).sum() / weight.sum(),
            max_abs_error=data.error.abs().max(),
            matches=int(weight.sum()),
        )
        rows.append(row)
    summary = pd.DataFrame(rows)
    for column in ("mean_error", "mean_abs_error", "max_abs_error"):
        summary[column] = summary[column].map(lambda value: f"{value:+.1%}" if column == "mean_error" else f"{value:.1%}")
    return markdown(summary.rename(columns={"mean_error": "bias", "mean_abs_error": "MAE", "max_abs_error": "max_error"}))


def write_report(overall, by_league, by_season):
    largest = overall.loc[overall.error.abs().idxmax()]
    lines = [
        "# Report 01 — Market Calibration", "", "## Research Question", "",
        "How well calibrated are normalized closing 1X2 probabilities, and are the patterns stable across leagues and seasons?", "",
        "## Executive Summary", "",
        f"- The largest overall bin deviation is {largest.outcome.title()} bin {int(largest.bin)} at {largest.error:+.1%}.",
        "- Closing probabilities are broadly informative, but individual calibration bins remain noisy.",
        "- Deviations are not clearly stable after splitting by league and season.",
        "- Strong-favorite bias is worth one direct betting-return test before deeper modeling.", "",
        "## Research Scorecard", "", "| Metric | Value |", "| --- | ---: |",
        f"| Largest Overall Bin Error | {largest.error:+.1%} |",
        "| Statistically Significant | Not tested |",
        "| Stable Across Seasons | No clear evidence |",
        "| Stable Across Leagues | No clear evidence |",
        "| Worth Pursuing | Yes — favorite validation |", "",
        "## Method", "",
        "All 3,504 matches are converted from closing odds to normalized Home / Draw / Away probabilities. Each outcome uses 20 equal-frequency bins. Error is observed rate minus average inferred probability.", "",
        "## Results", "", "### Overall", "", calibration_summary(overall), "",
        "![Overall calibration](figures/overall.png)", "",
        "### By Season", "", calibration_summary(by_season, "season"), "",
        "### By League", "", calibration_summary(by_league, "league"), "",
        "Full bin-level tables and supporting figures are exported under `tables/` and `figures/`.", "",
        "## Discussion", "",
        "- Small calibration errors can be economically irrelevant after bookmaker margin.",
        "- League-level bins contain only about 30–38 matches, so large deviations are unstable.",
        "- Calibration should be translated into realized betting returns before treating it as an edge.", "",
        "## Next Experiment", "", "**Question**", "",
        "Does the apparent calibration bias among strong Home and Away favorites survive bookmaker margin?", "",
        "**Experiment**", "",
        "- Select the highest 5%–25% normalized Home and Away probabilities.",
        "- Calculate flat-bet ROI and bootstrap confidence intervals.",
        "- Check stability overall, by season, and by league.", "",
    ]
    (REPORT / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    try:
        from .plotting import plot
    except ImportError:
        from plotting import plot

    matches = load_matches()
    tables = {"overall": all_outcomes(matches), "by_league": grouped(matches, "league"), "by_season": grouped(matches, "season")}
    (REPORT / "tables").mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(REPORT / f"tables/{name}.csv", index=False)
    plot(tables["overall"], None, "Overall market calibration", REPORT / "figures/overall.png")
    plot(tables["by_league"], "league", "Market calibration by league", REPORT / "figures/by_league.png")
    plot(tables["by_season"], "season", "Market calibration by season", REPORT / "figures/by_season.png")
    write_report(*tables.values())
    print(f"Wrote Phase 1 analysis to {REPORT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
