# Report 01 — Market Calibration

## Research Question

How well calibrated are normalized closing 1X2 probabilities, and are the patterns stable across leagues and seasons?

## Executive Summary

- The largest overall bin deviation is Away bin 15 at +7.8%.
- Closing probabilities are broadly informative, but individual calibration bins remain noisy.
- Deviations are not clearly stable after splitting by league and season.
- Strong-favorite bias is worth one direct betting-return test before deeper modeling.

## Research Scorecard

| Metric | Value |
| --- | ---: |
| Largest Overall Bin Error | +7.8% |
| Statistically Significant | Not tested |
| Stable Across Seasons | No clear evidence |
| Stable Across Leagues | No clear evidence |
| Worth Pursuing | Yes — favorite validation |

## Method

All 3,504 matches are converted from closing odds to normalized Home / Draw / Away probabilities. Each outcome uses 20 equal-frequency bins. Error is observed rate minus average inferred probability.

## Results

### Overall

| outcome | bias | MAE | max_error | matches |
| --- | ---: | ---: | ---: | ---: |
| home | -0.6% | 3.1% | 7.0% | 3504 |
| draw | +0.1% | 1.7% | 5.4% | 3504 |
| away | +0.6% | 2.4% | 7.8% | 3504 |

![Overall calibration](figures/overall.png)

### By Season

| season | outcome | bias | MAE | max_error | matches |
| ---: | --- | ---: | ---: | ---: | ---: |
| 2024-2025 | home | -2.1% | 4.7% | 8.6% | 1752 |
| 2024-2025 | draw | +0.1% | 3.8% | 12.8% | 1752 |
| 2024-2025 | away | +2.0% | 4.7% | 10.4% | 1752 |
| 2025-2026 | home | +0.8% | 3.9% | 13.5% | 1752 |
| 2025-2026 | draw | +0.1% | 2.7% | 10.1% | 1752 |
| 2025-2026 | away | -0.9% | 3.5% | 8.1% | 1752 |

### By League

| league | outcome | bias | MAE | max_error | matches |
| ---: | --- | ---: | ---: | ---: | ---: |
| Premier League | home | -2.2% | 6.6% | 19.0% | 760 |
| Premier League | draw | +1.8% | 5.2% | 16.6% | 760 |
| Premier League | away | +0.4% | 5.4% | 10.4% | 760 |
| Bundesliga | home | -3.7% | 7.1% | 19.9% | 612 |
| Bundesliga | draw | +1.2% | 5.9% | 16.3% | 612 |
| Bundesliga | away | +2.5% | 5.1% | 26.2% | 612 |
| La Liga | home | +2.4% | 7.5% | 14.4% | 760 |
| La Liga | draw | -1.3% | 5.3% | 12.4% | 760 |
| La Liga | away | -1.0% | 6.3% | 15.2% | 760 |
| Serie A | home | -2.4% | 5.0% | 12.9% | 760 |
| Serie A | draw | +0.6% | 4.0% | 13.7% | 760 |
| Serie A | away | +1.8% | 5.8% | 13.4% | 760 |
| Ligue 1 | home | +2.8% | 5.5% | 11.9% | 612 |
| Ligue 1 | draw | -2.1% | 7.1% | 19.9% | 612 |
| Ligue 1 | away | -0.7% | 4.4% | 10.0% | 612 |

Full bin-level tables and supporting figures are exported under `tables/` and `figures/`.

## Discussion

- Small calibration errors can be economically irrelevant after bookmaker margin.
- League-level bins contain only about 30–38 matches, so large deviations are unstable.
- Calibration should be translated into realized betting returns before treating it as an edge.

## Next Experiment

**Question**

Does the apparent calibration bias among strong Home and Away favorites survive bookmaker margin?

**Experiment**

- Select the highest 5%–25% normalized Home and Away probabilities.
- Calculate flat-bet ROI and bootstrap confidence intervals.
- Check stability overall, by season, and by league.
