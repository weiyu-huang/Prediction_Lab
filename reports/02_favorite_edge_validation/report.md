# Report 02 — Favorite Edge Validation

## Research Question

Does the calibration bias of strong Home and Away favorites translate into positive betting returns after bookmaker margin?

## Executive Summary

- Best overall result: Home Top 10%, ROI +2.0% with 95% CI [-3.2%, +7.0%].
- No overall or season-level result is statistically significant at the 95% level.
- The signal is not stable across seasons; the best overall rule is positive in one season and negative in the other.
- La Liga Home favorites merit one focused out-of-sample test, but the broad favorite-edge hypothesis is not supported.

## Research Scorecard

| Metric | Value |
| --- | ---: |
| Best ROI | +2.0% |
| Statistically Significant | No |
| Stable Across Seasons | No |
| Stable Across Leagues | Partial — La Liga only |
| Worth Pursuing | Yes — one focused test |

## Method

For Home and Away separately, each scope selects its highest 5%, 10%, 15%, 20%, and 25% normalized implied probabilities. Each bet risks one unit at closing odds. ROI intervals use 10,000 deterministic bootstrap resamples. Percentile subsets are nested and ties at the cutoff are included.

## Results

### Overall

| outcome | top_% | bets | avg_prob | avg_odds | win_rate | break_even | cal_edge | bet_edge | roi | 95% CI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| home | 5 | 176 | 80.2% | 1.19 | 84.7% | 84.1% | +4.5% | +0.6% | +0.4% | [-6.1%, +6.5%] |
| home | 10 | 351 | 76.0% | 1.26 | 81.5% | 79.6% | +5.4% | +1.8% | +2.0% | [-3.2%, +7.0%] |
| home | 15 | 526 | 73.0% | 1.31 | 77.2% | 76.3% | +4.2% | +0.9% | +0.5% | [-4.4%, +5.1%] |
| home | 20 | 701 | 70.3% | 1.36 | 72.6% | 73.3% | +2.3% | -0.7% | -2.2% | [-6.8%, +2.3%] |
| home | 25 | 876 | 67.8% | 1.42 | 69.9% | 70.4% | +2.0% | -0.6% | -2.4% | [-6.7%, +1.9%] |
| away | 5 | 176 | 69.0% | 1.38 | 70.5% | 72.2% | +1.4% | -1.8% | -3.3% | [-12.7%, +5.6%] |
| away | 10 | 351 | 63.7% | 1.51 | 66.4% | 66.4% | +2.7% | +0.0% | -1.0% | [-8.5%, +6.4%] |
| away | 15 | 526 | 59.9% | 1.61 | 62.4% | 62.1% | +2.5% | +0.3% | -1.1% | [-7.9%, +5.6%] |
| away | 20 | 701 | 56.7% | 1.71 | 59.5% | 58.4% | +2.8% | +1.1% | -0.2% | [-6.4%, +5.9%] |
| away | 25 | 876 | 53.9% | 1.81 | 56.8% | 55.2% | +2.9% | +1.7% | +0.3% | [-5.8%, +6.2%] |

### By Season

The best overall rule (Home Top 10%) is not stable:

| season | outcome | top_% | bets | avg_prob | avg_odds | win_rate | break_even | cal_edge | bet_edge | roi | 95% CI |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-2025 | home | 10 | 176 | 77.3% | 1.24 | 83.5% | 80.5% | +6.2% | +3.0% | +3.6% | [-3.4%, +10.4%] |
| 2025-2026 | home | 10 | 176 | 74.5% | 1.27 | 78.4% | 78.6% | +3.9% | -0.2% | -0.8% | [-8.8%, +6.6%] |

### By League

Best point estimate within each league:

| league | outcome | top_% | bets | avg_prob | avg_odds | win_rate | break_even | cal_edge | bet_edge | roi | 95% CI |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Bundesliga | away | 25 | 153 | 53.3% | 1.85 | 57.5% | 54.1% | +4.2% | +3.4% | +3.4% | [-11.4%, +17.9%] |
| La Liga | home | 5 | 38 | 80.7% | 1.18 | 94.7% | 84.9% | +14.0% | +9.9% | +11.9% | [+2.2%, +18.7%] |
| Ligue 1 | home | 15 | 92 | 72.8% | 1.31 | 78.3% | 76.4% | +5.5% | +1.9% | +2.3% | [-9.2%, +13.3%] |
| Premier League | away | 5 | 38 | 69.2% | 1.39 | 76.3% | 72.1% | +7.2% | +4.3% | +5.9% | [-13.8%, +23.9%] |
| Serie A | away | 25 | 190 | 55.4% | 1.75 | 64.2% | 57.2% | +8.8% | +7.0% | +10.0% | [-1.9%, +21.9%] |

All 4 positive league-level confidence intervals are nested La Liga Home thresholds. Full league and season tables are exported under `tables/`.

## Discussion

- Calibration edge does not automatically translate into betting edge after margin.
- Positive point estimates are insufficient when the 95% interval includes zero.
- Season stability is more persuasive than one league's nested in-sample thresholds.
- Because odds vary, per-bet ROI is definitive; `1 / average odds` is only a summary break-even approximation.

## Next Experiment

**Question**

Does the La Liga Home favorite signal persist out-of-sample, or is it explained by threshold selection and sampling variance?

**Experiment**

- Select non-overlapping probability bands using 2024-2025 only.
- Evaluate the locked bands on 2025-2026.
- Reverse the train/test seasons and compare direction, ROI, and confidence intervals.
