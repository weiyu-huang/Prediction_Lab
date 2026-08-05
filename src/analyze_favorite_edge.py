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
        "total_profit": profits.sum(),
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


def summary(overall):
    best = overall.loc[overall.roi.idxmax()]
    significant = overall[overall.roi_ci_low > 0]
    confidence = (
        f"{len(significant)} of {len(overall)} overall subsets have a 95% ROI interval fully above zero."
        if len(significant)
        else "No overall subset has a 95% ROI interval fully above zero."
    )
    return (
        f"The best overall result is {best.outcome.title()} Top {int(best.top_percent)}%: "
        f"ROI {best.roi:+.2%} across {int(best.bets)} bets "
        f"(95% CI {best.roi_ci_low:+.2%} to {best.roi_ci_high:+.2%}). {confidence}"
    )


def table_markdown(table):
    columns = [
        *([table.columns[0]] if table.columns[0] in ("league", "season") else []),
        "outcome", "top_percent", "bets", "avg_implied_probability", "avg_closing_odds",
        "observed_win_rate", "break_even_win_rate", "calibration_edge", "betting_edge",
        "roi", "total_profit", "roi_ci_low", "roi_ci_high",
    ]
    display = table[columns].copy()
    for column in display.select_dtypes("number"):
        if column not in ("top_percent", "bets"):
            display[column] = display[column].map(lambda value: f"{value:.3f}")
    return markdown(display.rename(columns={
        "top_percent": "top_%", "avg_implied_probability": "avg_prob", "avg_closing_odds": "avg_odds",
        "observed_win_rate": "win_rate", "break_even_win_rate": "break_even",
        "calibration_edge": "cal_edge", "betting_edge": "bet_edge", "total_profit": "profit",
        "roi_ci_low": "ci_low", "roi_ci_high": "ci_high",
    }))


def write_report(overall, by_league, by_season):
    best = overall.loc[overall.roi.idxmax()]
    league_positive = by_league[by_league.roi_ci_low > 0]
    season_positive = by_season[by_season.roi_ci_low > 0]
    learned = (
        f"Across cumulative favorite thresholds, the strongest overall result was {best.outcome.title()} "
        f"Top {int(best.top_percent)}% with ROI {best.roi:+.2%}; uncertainty and subgroup stability determine "
        "whether this is evidence of an edge or sampling noise."
    )
    lines = [
        "# Report 02 — Favorite Edge Validation", "", "## Executive Summary", "", summary(overall), "",
        "## Method", "",
        "For Home and Away separately, each scope selects matches at or above its own 95th, 90th, 85th, 80th, and 75th probability percentiles. Ties at the cutoff are included. Inverse closing odds are normalized across 1X2 outcomes to remove overround. Each selected bet risks one unit; a win returns `decimal odds - 1` profit and a loss returns `-1`. ROI confidence intervals use 10,000 deterministic bootstrap resamples of per-bet profit.",
        "", "## Overall Results", "", table_markdown(overall), "",
        "## By League", "", table_markdown(by_league), "",
        "## By Season", "", table_markdown(by_season), "",
        "## Key Findings", "", f"- {summary(overall)}",
        f"- {len(season_positive)} of {len(by_season)} season-level subsets have a 95% ROI interval fully above zero.",
        f"- {len(league_positive)} league-level subsets have a positive 95% interval; all are nested La Liga Home thresholds, so they are one concentrated signal rather than independent confirmations.",
        f"- League-level Top 5% subsets contain as few as {int(by_league.bets.min())} bets and should be treated as exploratory.",
        "- The percentile subsets are nested, so results across Top 5% through Top 25% are not independent tests.",
        "", "## Discussion", "",
        "Calibration edge is not automatically betting edge: normalized market probabilities remove overround for forecasting, while realized returns are paid at the original closing odds. The requested `1 / average odds` break-even rate is a useful summary approximation; because odds vary across bets, realized per-bet ROI is the definitive return measure. Positive point estimates are only credible when their confidence intervals and direction remain stable across leagues and seasons.",
        "", "## Next Research Question", "", f"What have we learned? {learned}", "",
        "What is the most valuable next experiment?", "",
        "**Do any apparent favorite returns persist in non-overlapping probability bands and out-of-sample season splits, rather than only in nested cumulative thresholds?**", "",
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
