# Report 03 — Favorite Threshold Validation

## Research Question

Can a Home-favorite probability threshold selected in one season generalize to another season?

## Executive Summary

- 4/10 validation experiments produced positive ROI; 6/10 had positive calibration edge, and 0/10 had a 95% ROI interval fully above zero.
- 3/5 leagues kept the same ROI sign across both directions; 1/5 were positive in both.
- Strongest validation: La Liga Home, +11.8% ROI [-0.1%, +22.2%]. Weakest: Serie A Home, -14.1% [-35.0%, +6.5%].
- Evidence of a persistent favorite edge is partial; validation, rather than optimized training ROI, does not support a broad strategy.

## Research Scorecard

| Metric | Value |
| --- | ---: |
| Validation Experiments | 10 |
| Positive Validation ROI | 4 / 10 |
| Positive Validation Calibration Edge | 6 / 10 |
| Positive ROI 95% CI | 0 / 10 |
| Same-Sign ROI Across Both Directions | 3 / 5 |
| Evidence of Persistent Edge | Partial |

## Method

For each league, Home-favorite thresholds from 50% to 90% are searched on one training season. The highest-ROI threshold with at least 30 bets is locked and applied unchanged to the other season; then the direction is reversed. ROI intervals use 10,000 deterministic bootstrap resamples.

## Validation Results

| league | outcome | train | validation | threshold | train_bets | train_roi | validation_bets | validation_cal_edge | validation_roi | validation_roi_95%_ci |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Premier League | Home | 2024-2025 | 2025-2026 | 71% | 42 | -3.3% | 19 | +7.8% | +4.5% | [-16.8%, +23.5%] |
| Premier League | Home | 2025-2026 | 2024-2025 | 68% | 32 | +4.8% | 59 | -4.2% | -10.1% | [-25.2%, +4.3%] |
| Bundesliga | Home | 2024-2025 | 2025-2026 | 72% | 31 | +4.0% | 20 | +0.1% | -5.3% | [-28.1%, +13.8%] |
| Bundesliga | Home | 2025-2026 | 2024-2025 | 50% | 98 | +14.0% | 115 | -4.8% | -12.4% | [-26.0%, +0.9%] |
| La Liga | Home | 2024-2025 | 2025-2026 | 61% | 70 | +13.0% | 56 | +13.5% | +11.7% | [-1.2%, +23.1%] |
| La Liga | Home | 2025-2026 | 2024-2025 | 65% | 46 | +16.4% | 60 | +12.1% | +11.8% | [-0.1%, +22.2%] |
| Serie A | Home | 2024-2025 | 2025-2026 | 70% | 32 | +11.8% | 31 | -6.5% | -14.1% | [-35.0%, +6.5%] |
| Serie A | Home | 2025-2026 | 2024-2025 | 65% | 54 | -6.7% | 53 | +7.4% | +5.0% | [-9.9%, +18.8%] |
| Ligue 1 | Home | 2024-2025 | 2025-2026 | 67% | 44 | +10.3% | 34 | -1.1% | -7.9% | [-27.1%, +10.4%] |
| Ligue 1 | Home | 2025-2026 | 2024-2025 | 62% | 52 | +4.9% | 64 | +2.9% | -0.9% | [-16.0%, +13.5%] |

## Stability Summary

| league | outcome | 2024-25 → 2025-26 ROI | 2025-26 → 2024-25 ROI | both_positive? | interpretation |
| ---: | --- | ---: | ---: | ---: | ---: |
| Bundesliga | Home | -5.3% | -12.4% | No | Stable negative |
| La Liga | Home | +11.7% | +11.8% | Yes | Stable positive |
| Ligue 1 | Home | -7.9% | -0.9% | No | Stable negative |
| Premier League | Home | +4.5% | -10.1% | No | Unstable |
| Serie A | Home | -14.1% | +5.0% | No | Unstable |

## Key Findings

- Optimized training thresholds generalized to positive ROI in 4/10 experiments, but only 0/10 cleared zero at the 95% level.
- Profitable in both directions: 1/5 leagues. Shared matches and related thresholds mean these are not fully independent confirmations.
- Calibration edge and ROI can diverge because normalized probabilities remove overround while bets settle at unnormalized closing odds.
- Selected thresholds vary by training season, indicating sensitivity to the sample and threshold search.

## Discussion

High training ROI is expected after in-sample optimization; validation ROI is the decisive result. A positive result in only one direction is weak evidence, and a point estimate remains inconclusive when its interval crosses zero. This is still exploratory because 41 thresholds are searched per training sample.

## Next Experiment

**Question**

Do any league-level Home-favorite thresholds remain profitable when selected using multiple historical seasons and evaluated on a completely untouched future season?

**Experiment**

- Add historical seasons to form a multi-season training window.
- Lock one Home-favorite threshold per league before viewing the next season.
- Evaluate calibration edge, ROI, and confidence intervals on that untouched season.
