"""Validate whether strong-favorite calibration bias produces betting returns."""

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .analyze_calibration import LEAGUES, ROOT, load_matches, markdown
except ImportError:
    from analyze_calibration import LEAGUES, ROOT, load_matches, markdown


REPORT = ROOT / "reports/02_favorite_edge_validation"
OUTCOMES = {"home": ("home_prob", "home_odds", "H"), "away": ("away_prob", "away_odds", "A")}
TOP_PERCENTS = (5, 10, 15, 20, 25)
BOOTSTRAPS = 10_000


def evaluate(matches, outcome, top_percent, rng):
    probability, odds, result = OUTCOMES[outcome]
    cutoff = matches[probability].quantile(1 - top_percent / 100)
    bets = matches[matches[probability] >= cutoff]
    wins = bets["result"].eq(result)
    profits = np.where(wins, bets[odds] - 1, -1).astype(float)
    bootstrap_roi = rng.choice(profits, (BOOTSTRAPS, len(profits)), replace=True).mean(axis=1)
    average_probability, average_odds, win_rate = bets[probability].mean(), bets[odds].mean(), wins.mean()
    return {
        "outcome": outcome,
        "top_percent": top_percent,
        "probability_cutoff": cutoff,
        "bets": len(bets),
        "avg_implied_probability": average_probability,
        "avg_closing_odds": average_odds,
        "observed_win_rate": win_rate,
        "break_even_win_rate": 1 / average_odds,
        "calibration_edge": win_rate - average_probability,
        "betting_edge": win_rate - 1 / average_odds,
        "roi": profits.mean(),
        "roi_ci_low": np.quantile(bootstrap_roi, 0.025),
        "roi_ci_high": np.quantile(bootstrap_roi, 0.975),
    }


def analyze(matches, rng):
    return pd.DataFrame(
        evaluate(matches, outcome, percent, rng)
        for outcome in OUTCOMES
        for percent in TOP_PERCENTS
    )


def grouped(matches, column, rng):
    groups = list(LEAGUES) if column == "league" else sorted(matches[column].unique())
    tables = []
    for group in groups:
        table = analyze(matches[matches[column] == group], rng)
        table.insert(0, column, LEAGUES.get(group, group))
        tables.append(table)
    return pd.concat(tables, ignore_index=True)


def compact_table(table, scope=None):
    columns = ([scope] if scope else []) + ["outcome", "top_percent", "bets", "avg_implied_probability", "avg_closing_odds", "observed_win_rate", "break_even_win_rate", "calibration_edge", "betting_edge", "roi"]
    display = table[columns].copy()
    display["95% CI"] = table.apply(lambda row: f"[{row.roi_ci_low:+.1%}, {row.roi_ci_high:+.1%}]", axis=1)
    for column in ("avg_implied_probability", "observed_win_rate", "break_even_win_rate", "calibration_edge", "betting_edge", "roi"):
        display[column] = display[column].map(lambda value: f"{value:+.1%}" if column in ("calibration_edge", "betting_edge", "roi") else f"{value:.1%}")
    display["avg_closing_odds"] = display["avg_closing_odds"].map(lambda value: f"{value:.2f}")
    return markdown(display.rename(columns={
        "top_percent": "top_%", "avg_implied_probability": "avg_prob", "avg_closing_odds": "avg_odds",
        "observed_win_rate": "win_rate", "break_even_win_rate": "break_even",
        "calibration_edge": "cal_edge", "betting_edge": "bet_edge",
    }))


def write_report(overall, by_league, by_season):
    best = overall.loc[overall.roi.idxmax()]
    league_positive = by_league[by_league.roi_ci_low > 0]
    season_positive = by_season[by_season.roi_ci_low > 0]
    season_target = by_season[(by_season.outcome == best.outcome) & (by_season.top_percent == best.top_percent)]
    league_best = by_league.loc[by_league.groupby("league").roi.idxmax()]
    lines = [
        "# Report 02 — Favorite Edge Validation", "", "## Research Question", "",
        "Does the calibration bias of strong Home and Away favorites translate into positive betting returns after bookmaker margin?", "",
        "## Executive Summary", "",
        f"- Best overall result: {best.outcome.title()} Top {int(best.top_percent)}%, ROI {best.roi:+.1%} with 95% CI [{best.roi_ci_low:+.1%}, {best.roi_ci_high:+.1%}].",
        "- No overall or season-level result is statistically significant at the 95% level.",
        "- The signal is not stable across seasons; the best overall rule is positive in one season and negative in the other.",
        "- La Liga Home favorites merit one focused out-of-sample test, but the broad favorite-edge hypothesis is not supported.", "",
        "## Research Scorecard", "",
        "| Metric | Value |", "| --- | ---: |",
        f"| Best ROI | {best.roi:+.1%} |",
        "| Statistically Significant | No |",
        "| Stable Across Seasons | No |",
        "| Stable Across Leagues | Partial — La Liga only |",
        "| Worth Pursuing | Yes — one focused test |", "",
        "## Method", "",
        "For Home and Away separately, each scope selects its highest 5%, 10%, 15%, 20%, and 25% normalized implied probabilities. Each bet risks one unit at closing odds. ROI intervals use 10,000 deterministic bootstrap resamples. Percentile subsets are nested and ties at the cutoff are included.",
        "", "## Results", "", "### Overall", "", compact_table(overall), "",
        "### By Season", "", f"The best overall rule ({best.outcome.title()} Top {int(best.top_percent)}%) is not stable:", "", compact_table(season_target, "season"), "",
        "### By League", "", "Best point estimate within each league:", "", compact_table(league_best, "league"), "",
        f"All {len(league_positive)} positive league-level confidence intervals are nested La Liga Home thresholds. Full league and season tables are exported under `tables/`.", "",
        "## Discussion", "",
        "- Calibration edge does not automatically translate into betting edge after margin.",
        "- Positive point estimates are insufficient when the 95% interval includes zero.",
        "- Season stability is more persuasive than one league's nested in-sample thresholds.",
        "- Because odds vary, per-bet ROI is definitive; `1 / average odds` is only a summary break-even approximation.", "",
        "## Next Experiment", "", "**Question**", "",
        "Does the La Liga Home favorite signal persist out-of-sample, or is it explained by threshold selection and sampling variance?", "",
        "**Experiment**", "",
        "- Select non-overlapping probability bands using 2024-2025 only.",
        "- Evaluate the locked bands on 2025-2026.",
        "- Reverse the train/test seasons and compare direction, ROI, and confidence intervals.", "",
    ]
    (REPORT / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    matches, rng = load_matches(), np.random.default_rng(42)
    tables = {
        "overall": analyze(matches, rng),
        "by_league": grouped(matches, "league", rng),
        "by_season": grouped(matches, "season", rng),
    }
    (REPORT / "tables").mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(REPORT / f"tables/{name}.csv", index=False)
    write_report(*tables.values())
    print(f"Wrote Report 02 to {REPORT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
