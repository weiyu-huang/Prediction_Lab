# Big Five Dataset v0 — Validation Report

Generated on 2026-08-04 by `src/build_dataset.py`.

## Dataset summary

| Season | E0 | D1 | SP1 | I1 | F1 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-2025 | 380 | 306 | 380 | 380 | 306 | 1,752 |
| 2025-2026 | 380 | 306 | 380 | 380 | 306 | 1,752 |
| **Total** | **760** | **612** | **760** | **760** | **612** | **3,504** |

The processed dataset spans 2024-08-15 through 2026-05-24. It contains 1,507 home wins, 883 draws, and 1,114 away wins.

## Automated checks

- All 10 expected source files are present and contain the expected `Div` value.
- All required raw and processed columns are present.
- Required values contain no missing data.
- All 3,504 `match_id` values are unique.
- No exact duplicate processed rows remain.
- Every result is `H`, `D`, or `A`.
- Goals are non-negative and all closing odds are greater than 1.
- Every kickoff timestamp parses successfully.
- Every league-season row count is plausible and matches the expected full-season count.
- CSV and Parquet outputs have identical rows and values; their serialized data types differ as expected.

## Kickoff-time spot checks

The source `Time` field matches the published local wall-clock kickoff in the checked fixtures:

- Manchester United–Fulham on 2024-08-16: source `20:00`; Manchester United published `20:00 BST`.
- Athletic Club–Getafe on 2024-08-15: source `18:00`; Athletic Club published `19:00 CEST`.
- Bayern Munich–RB Leipzig on 2025-08-22: source `19:30`; DFB published `20:30 +02:00`.

These checks show that football-data normalizes at least some continental kickoff values to UK local time. The pipeline therefore localizes the source date and time with `Europe/London`, automatically applying GMT/BST daylight-saving rules, and then converts the timestamp to UTC. The original wall-clock value remains unchanged in `time`.

The resulting UTC spot checks are:

- Manchester United–Fulham: `20:00 BST` → `19:00 UTC`.
- Athletic Club–Getafe: source `18:00 BST` / published `19:00 CEST` → `17:00 UTC`.
- Bayern Munich–RB Leipzig: source `19:30 BST` / published `20:30 CEST` → `18:30 UTC`.

Sources: [Manchester United](https://www.manutd.com/en/news/detail/match-preview-for-man-utd-v-fulham-in-the-premier-league-13-august-2024), [Athletic Club](https://www.athletic-club.eus/en/news/2024/08/15/match-pack-athletic-club-vs-getafe-cf/), and [DFB Datencenter](https://datencenter.dfb.de/en/data-center/bundesliga/2025-2026/1-matchday/2398217).
