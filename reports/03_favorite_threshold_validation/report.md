# Report 03 — Favorite Threshold Validation

## Research Question

Can a favorite probability threshold selected in one season generalize to another season?

## Executive Summary

- 10/20 validation experiments produced positive ROI; 14/20 had positive calibration edge, and 0/20 had a 95% ROI interval fully above zero.
- 4/10 league-outcome pairs kept the same ROI sign across both directions; 2/10 were positive in both.
- Strongest validation: La Liga Home, +11.8% ROI [-0.1%, +22.1%]. Weakest: Serie A Home, -14.1% [-34.9%, +6.3%].
- Evidence of a persistent favorite edge is partial; validation, rather than optimized training ROI, does not support a broad strategy.

## Research Scorecard

| Metric | Value |
| --- | ---: |
| Validation Experiments | 20 |
| Positive Validation ROI | 10 / 20 |
| Positive Validation Calibration Edge | 14 / 20 |
| Positive ROI 95% CI | 0 / 20 |
| Same-Sign ROI Across Both Directions | 4 / 10 |
| Evidence of Persistent Edge | Partial |

## Method

For each league and Home/Away outcome, thresholds from 50% to 90% are searched on one training season. The highest-ROI threshold with at least 30 bets is locked and applied unchanged to the other season; then the direction is reversed. ROI intervals use 10,000 deterministic bootstrap resamples.

## Validation Results

| league | outcome | train | validation | threshold | train_bets | train_roi | validation_bets | validation_cal_edge | validation_roi | validation_roi_95%_ci |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Premier League | Home | 2024-2025 | 2025-2026 | 71% | 42 | -3.3% | 19 | +7.8% | +4.5% | [-16.8%, +23.5%] |
| Premier League | Home | 2025-2026 | 2024-2025 | 68% | 32 | +4.8% | 59 | -4.2% | -10.1% | [-25.2%, +4.3%] |
| Premier League | Away | 2024-2025 | 2025-2026 | 60% | 30 | +22.6% | 18 | +0.5% | -2.9% | [-35.9%, +28.7%] |
| Premier League | Away | 2025-2026 | 2024-2025 | 57% | 31 | -2.1% | 41 | +5.1% | +1.8% | [-19.0%, +21.5%] |
| Bundesliga | Home | 2024-2025 | 2025-2026 | 72% | 31 | +4.0% | 20 | +0.1% | -5.3% | [-28.3%, +13.4%] |
| Bundesliga | Home | 2025-2026 | 2024-2025 | 50% | 98 | +14.0% | 115 | -4.8% | -12.4% | [-25.9%, +0.9%] |
| Bundesliga | Away | 2024-2025 | 2025-2026 | 51% | 38 | +0.4% | 33 | +4.5% | +0.5% | [-24.4%, +24.9%] |
| Bundesliga | Away | 2025-2026 | 2024-2025 | 52% | 31 | +1.1% | 34 | -3.2% | -9.6% | [-35.0%, +14.5%] |
| La Liga | Home | 2024-2025 | 2025-2026 | 61% | 70 | +13.0% | 56 | +13.5% | +11.7% | [-1.4%, +23.1%] |
| La Liga | Home | 2025-2026 | 2024-2025 | 65% | 46 | +16.4% | 60 | +12.1% | +11.8% | [-0.1%, +22.1%] |
| La Liga | Away | 2024-2025 | 2025-2026 | 50% | 46 | +1.7% | 40 | -0.2% | -4.1% | [-29.1%, +20.4%] |
| La Liga | Away | 2025-2026 | 2024-2025 | 50% | 40 | -4.1% | 46 | +2.8% | +1.7% | [-21.5%, +24.7%] |
| Serie A | Home | 2024-2025 | 2025-2026 | 70% | 32 | +11.8% | 31 | -6.5% | -14.1% | [-34.9%, +6.3%] |
| Serie A | Home | 2025-2026 | 2024-2025 | 65% | 54 | -6.7% | 53 | +7.4% | +5.0% | [-10.5%, +18.8%] |
| Serie A | Away | 2024-2025 | 2025-2026 | 51% | 62 | +18.4% | 62 | +6.7% | +3.7% | [-14.7%, +21.4%] |
| Serie A | Away | 2025-2026 | 2024-2025 | 58% | 40 | +9.4% | 29 | +4.5% | +1.4% | [-24.2%, +25.7%] |
| Ligue 1 | Home | 2024-2025 | 2025-2026 | 67% | 44 | +10.3% | 34 | -1.1% | -7.9% | [-27.2%, +9.8%] |
| Ligue 1 | Home | 2025-2026 | 2024-2025 | 62% | 52 | +4.9% | 64 | +2.9% | -0.9% | [-16.2%, +13.6%] |
| Ligue 1 | Away | 2024-2025 | 2025-2026 | 55% | 34 | +2.7% | 34 | +1.6% | -3.1% | [-28.1%, +20.7%] |
| Ligue 1 | Away | 2025-2026 | 2024-2025 | 55% | 34 | -3.1% | 34 | +4.5% | +2.7% | [-22.0%, +26.1%] |

## Stability Summary

| league | outcome | 2024-25 → 2025-26 ROI | 2025-26 → 2024-25 ROI | both_positive? | interpretation |
| ---: | --- | ---: | ---: | ---: | ---: |
| Bundesliga | Away | +0.5% | -9.6% | No | Unstable |
| Bundesliga | Home | -5.3% | -12.4% | No | Stable negative |
| La Liga | Away | -4.1% | +1.7% | No | Unstable |
| La Liga | Home | +11.7% | +11.8% | Yes | Stable positive |
| Ligue 1 | Away | -3.1% | +2.7% | No | Unstable |
| Ligue 1 | Home | -7.9% | -0.9% | No | Stable negative |
| Premier League | Away | -2.9% | +1.8% | No | Unstable |
| Premier League | Home | +4.5% | -10.1% | No | Unstable |
| Serie A | Away | +3.7% | +1.4% | Yes | Stable positive |
| Serie A | Home | -14.1% | +5.0% | No | Unstable |

## Key Findings

- Optimized training thresholds generalized to positive ROI in 10/20 experiments, but only 0/20 cleared zero at the 95% level.
- 2 league-outcome pairs were profitable in both directions; shared matches and related thresholds mean these are not fully independent confirmations.
- Calibration edge and ROI can diverge because normalized probabilities remove overround while bets settle at unnormalized closing odds.
- Selected thresholds vary by training season, indicating sensitivity to the sample and threshold search.

## Discussion

High training ROI is expected after in-sample optimization; validation ROI is the decisive result. A positive result in only one direction is weak evidence, and a point estimate remains inconclusive when its interval crosses zero. This is still exploratory because 41 thresholds are searched per training sample.

## Next Experiment

**Question**

Do any league-outcome thresholds remain profitable when selected using multiple historical seasons and evaluated on a completely untouched future season?

**Experiment**

- Add historical seasons to form a multi-season training window.
- Lock one threshold per league and outcome before viewing the next season.
- Evaluate calibration edge, ROI, and confidence intervals on that untouched season.
