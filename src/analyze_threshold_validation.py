"""Validate season-trained favorite thresholds out of sample."""

import numpy as np
import pandas as pd

try:
    from .analyze_calibration import LEAGUES, ROOT, load_matches, markdown
except ImportError:
    from analyze_calibration import LEAGUES, ROOT, load_matches, markdown


REPORT = ROOT / "reports/03_favorite_threshold_validation"
OUTCOMES = {"Home": ("home_prob", "home_odds", "H")}
SEASONS = ("2024-2025", "2025-2026")
THRESHOLDS = np.round(np.arange(0.50, 0.91, 0.01), 2)
BOOTSTRAPS, MIN_BETS, TOP_SHARE = 10_000, 30, .15


def evaluate(matches, outcome, threshold, rng):
    probability, odds, result = OUTCOMES[outcome]
    bets = matches[matches[probability] >= threshold]
    if bets.empty:
        return {"bets": 0, **{name: np.nan for name in ("avg_prob", "avg_odds", "win_rate", "cal_edge", "roi", "ci_low", "ci_high")}}
    wins = bets.result.eq(result)
    profits = np.where(wins, bets[odds] - 1, -1).astype(float)
    roi_samples = rng.choice(profits, (BOOTSTRAPS, len(profits))).mean(axis=1)
    avg_prob, win_rate = bets[probability].mean(), wins.mean()
    return {
        "bets": len(bets), "avg_prob": avg_prob, "avg_odds": bets[odds].mean(),
        "win_rate": win_rate, "cal_edge": win_rate - avg_prob, "roi": profits.mean(),
        "ci_low": np.quantile(roi_samples, .025), "ci_high": np.quantile(roi_samples, .975),
    }


def analyze(matches):
    rng, searches, results = np.random.default_rng(42), [], []
    for code, league in LEAGUES.items():
        for outcome in OUTCOMES:
            for train_season, validation_season in (SEASONS, SEASONS[::-1]):
                train = matches[(matches.league == code) & (matches.season == train_season)]
                search_floor = train.home_prob.quantile(1 - TOP_SHARE)
                rows = []
                for threshold in THRESHOLDS[THRESHOLDS >= search_floor]:
                    row = {"league": league, "outcome": outcome, "train_season": train_season,
                           "validation_season": validation_season, "search_floor": search_floor,
                           "threshold": threshold}
                    row.update(evaluate(train, outcome, threshold, rng))
                    row["eligible"] = row["bets"] >= MIN_BETS
                    rows.append(row)
                table = pd.DataFrame(rows)
                eligible = table[table.eligible].sort_values(["roi", "bets", "threshold"], ascending=[False, False, True])
                table["selected"] = False
                if not eligible.empty:
                    selected = eligible.iloc[0]
                    table.loc[selected.name, "selected"] = True
                    validation = evaluate(
                        matches[(matches.league == code) & (matches.season == validation_season)],
                        outcome, selected.threshold, rng,
                    )
                    result = {key: selected[key] for key in ("league", "outcome", "train_season", "validation_season")}
                    result["selected_threshold"] = selected.threshold
                    result.update({f"train_{key}": selected[key] for key in ("bets", "avg_prob", "avg_odds", "win_rate", "cal_edge", "roi", "ci_low", "ci_high")})
                    result.update({f"validation_{key}": value for key, value in validation.items()})
                    results.append(result)
                searches.append(table)
    return pd.concat(searches, ignore_index=True), pd.DataFrame(results)


def result_table(results):
    table = results[["league", "outcome", "train_season", "validation_season", "selected_threshold",
                     "train_bets", "train_roi", "validation_bets", "validation_cal_edge", "validation_roi"]].copy()
    table["validation_roi_95%_ci"] = results.apply(lambda x: f"[{x.validation_ci_low:+.1%}, {x.validation_ci_high:+.1%}]", axis=1)
    table["selected_threshold"] = table.selected_threshold.map(lambda x: f"{x:.0%}")
    for column in ("train_roi", "validation_cal_edge", "validation_roi"):
        table[column] = table[column].map(lambda x: f"{x:+.1%}")
    return markdown(table.rename(columns={"train_season": "train", "validation_season": "validation", "selected_threshold": "threshold"}))


def stability_table(results):
    pivot = results.pivot(index=["league", "outcome"], columns="train_season", values="validation_roi").reset_index()
    pivot["both_positive"] = (pivot[SEASONS[0]] > 0) & (pivot[SEASONS[1]] > 0)
    pivot["interpretation"] = np.where(pivot.both_positive, "Stable positive", np.where((pivot[SEASONS[0]] < 0) & (pivot[SEASONS[1]] < 0), "Stable negative", "Unstable"))
    for season in SEASONS:
        pivot[season] = pivot[season].map(lambda x: f"{x:+.1%}")
    pivot["both_positive"] = pivot.both_positive.map({True: "Yes", False: "No"})
    return markdown(pivot.rename(columns={SEASONS[0]: "2024-25 → 2025-26 ROI", SEASONS[1]: "2025-26 → 2024-25 ROI", "both_positive": "both_positive?"}))


def write_report(results):
    experiments = len(results)
    pairs_total = results.groupby(["league", "outcome"]).ngroups
    positive_roi = int((results.validation_roi > 0).sum())
    positive_cal = int((results.validation_cal_edge > 0).sum())
    positive_ci = int((results.validation_ci_low > 0).sum())
    pairs = results.groupby(["league", "outcome"]).validation_roi.apply(lambda x: (x > 0).all())
    same_sign = results.groupby(["league", "outcome"]).validation_roi.apply(lambda x: (x > 0).all() or (x < 0).all()).sum()
    best, worst = results.loc[results.validation_roi.idxmax()], results.loc[results.validation_roi.idxmin()]
    evidence = "Partial" if pairs.any() else "No"
    lines = [
        "# Report 03 — Favorite Threshold Validation", "", "## Research Question", "",
        "Can a Home-favorite probability threshold selected in one season generalize to another season?", "",
        "## Executive Summary", "",
        f"- {positive_roi}/{experiments} validation experiments produced positive ROI; {positive_cal}/{experiments} had positive calibration edge, and {positive_ci}/{experiments} had a 95% ROI interval fully above zero.",
        f"- {int(same_sign)}/{pairs_total} leagues kept the same ROI sign across both directions; {int(pairs.sum())}/{pairs_total} were positive in both.",
        f"- Strongest validation: {best.league} {best.outcome}, {best.validation_roi:+.1%} ROI [{best.validation_ci_low:+.1%}, {best.validation_ci_high:+.1%}]. Weakest: {worst.league} {worst.outcome}, {worst.validation_roi:+.1%} [{worst.validation_ci_low:+.1%}, {worst.validation_ci_high:+.1%}].",
        f"- Evidence of a persistent favorite edge is {evidence.lower()}; validation, rather than optimized training ROI, does not support a broad strategy.", "",
        "## Research Scorecard", "", "| Metric | Value |", "| --- | ---: |",
        f"| Validation Experiments | {experiments} |", f"| Positive Validation ROI | {positive_roi} / {experiments} |",
        f"| Positive Validation Calibration Edge | {positive_cal} / {experiments} |", f"| Positive ROI 95% CI | {positive_ci} / {experiments} |",
        f"| Same-Sign ROI Across Both Directions | {int(same_sign)} / {pairs_total} |", f"| Evidence of Persistent Edge | {evidence} |", "",
        "## Method", "",
        "For each league, the training season's 85th percentile of normalized Home probability defines the search floor. Absolute 1-point thresholds from the first grid value at or above that floor through 90% are searched. The highest-ROI threshold with at least 30 bets is locked and applied unchanged to the other season; then the direction is reversed. ROI intervals use 10,000 deterministic bootstrap resamples.", "",
        "## Validation Results", "", result_table(results), "",
        "## Stability Summary", "", stability_table(results), "",
        "## Key Findings", "",
        f"- Optimized training thresholds generalized to positive ROI in {positive_roi}/{experiments} experiments, but only {positive_ci}/{experiments} cleared zero at the 95% level.",
        f"- Profitable in both directions: {int(pairs.sum())}/{pairs_total} leagues. Shared matches and related thresholds mean these are not fully independent confirmations.",
        "- Calibration edge and ROI can diverge because normalized probabilities remove overround while bets settle at unnormalized closing odds.",
        "- Selected thresholds vary by training season, indicating sensitivity to the sample and threshold search.", "",
        "## Discussion", "",
        "High training ROI is expected after in-sample optimization; validation ROI is the decisive result. A positive result in only one direction is weak evidence, and a point estimate remains inconclusive when its interval crosses zero. This is still exploratory because multiple strong-favorite thresholds are searched per training sample.", "",
        "## Next Experiment", "", "**Question**", "",
        "Do any league-level Home-favorite thresholds remain profitable when selected using multiple historical seasons and evaluated on a completely untouched future season?", "",
        "**Experiment**", "",
        "- Add historical seasons to form a multi-season training window.",
        "- Lock one Home-favorite threshold per league before viewing the next season.",
        "- Evaluate calibration edge, ROI, and confidence intervals on that untouched season.", "",
    ]
    (REPORT / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    search, results = analyze(load_matches())
    search.to_csv(REPORT / "threshold_search.csv", index=False)
    results.to_csv(REPORT / "validation_results.csv", index=False)
    write_report(results)
    print(f"Wrote Report 03 to {REPORT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
