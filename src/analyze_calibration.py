"""Generate quantile-binned calibration tables for closing 1X2 odds."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/matches.parquet"
REPORT = ROOT / "reports/phase1_market_calibration"
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
    for column in ("avg_pred", "actual", "error"):
        table[column] = table[column].map(lambda value: f"{value:.3f}")
    headers = list(table)
    rows = [headers, ["---" if name == "outcome" else "---:" for name in headers]]
    rows += list(table.itertuples(index=False, name=None))
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def observations(table: pd.DataFrame, scopes=()) -> list[str]:
    labels = [*scopes, "outcome", "bin"]

    def describe(index):
        row = table.loc[index]
        label = ", ".join(f"{name}={row[name]}" for name in labels)
        return f"{label} (error {row['error']:+.3f}, n={int(row['count'])})"

    low = (table["count"] < 50).sum()
    return [
        f"Largest positive deviation: {describe(table.error.idxmax())}.",
        f"Largest negative deviation: {describe(table.error.idxmin())}.",
        f"Largest absolute error: {describe(table.error.abs().idxmax())}.",
        (f"{low} of {len(table)} bins have fewer than 50 observations; their deviations are especially noisy."
         if low else "No bin has fewer than 50 observations."),
    ]


def write_report(overall, by_league, by_season):
    lines = [
        "# Phase 1 — Market Calibration", "", "## Research question", "",
        "How well do normalized average closing 1X2 market probabilities match observed Home / Draw / Away frequencies, and is the pattern stable across leagues and seasons?",
        "", "## Dataset and method", "",
        "The analysis uses all 3,504 Big Five matches from 2024-2025 and 2025-2026. For each match, inverse Home / Draw / Away closing odds are normalized to sum to one, removing the bookmaker overround. Each outcome is grouped into 20 quantile bins, so bins have similar sample sizes. Error is `actual probability - average inferred probability`.",
        "", "![Overall calibration](figures/overall.png)", "", "## Overall calibration", "",
    ]
    for outcome in OUTCOMES:
        lines += [f"### {outcome.title()}", "", markdown(overall[overall.outcome == outcome]), ""]
    for title, table, column, image in (
        ("By league", by_league, "league", "by_league.png"),
        ("By season", by_season, "season", "by_season.png"),
    ):
        lines += [f"## {title}", "", f"![Calibration {title.lower()}](figures/{image})", ""]
        for value in table[column].drop_duplicates():
            lines += [f"### {value}", "", markdown(table[table[column] == value]), ""]
    lines += ["## Auto-generated observations", ""]
    for label, table, scopes in (("Overall", overall, ()), ("By league", by_league, ("league",)), ("By season", by_season, ("season",))):
        lines += [f"- {label}: {text}" for text in observations(table, scopes)]
    lines += ["", "## Human analysis and follow-up hypotheses", "", "_Add interpretation, competing explanations, and the next testable questions here._", ""]
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
