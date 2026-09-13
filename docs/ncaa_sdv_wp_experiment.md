# NCAA SportsDataverse WP experiment

This experiment leaves the production NCAA pipeline unchanged. CFBD remains the
source of truth for games, final scores, team metadata, rankings and game stats.
SportsDataverse supplies only spread-aware play-by-play win probabilities.

## Run locally

```bash
python scripts/ncaa_sdv_wp_experiment.py --seasons 2025 2026
bundle exec jekyll serve
```

Open `http://localhost:4000/ncaa_wp_experiment`.

One public parquet file is downloaded per season. These downloads do not use a
CFBD token or consume the CFBD monthly quota. The current release is downloaded
on every run so previously incomplete games are reconsidered automatically.

For an offline run, provide already downloaded files:

```bash
python scripts/ncaa_sdv_wp_experiment.py \
  --seasons 2025 2026 \
  --pbp-file 2025=/path/to/play_by_play_2025.parquet \
  --pbp-file 2026=/path/to/play_by_play_2026.parquet
```

## Completion gate

A game receives an experimental rating only when all of these are true:

1. CFBD already marks and stores the game as completed.
2. SportsDataverse marks every PBP row as completed.
3. The feed contains at least 40 unique sequenced plays and reaches period 4.
4. Its final home and away scores exactly match CFBD.
5. A pregame spread and valid spread-aware `home_wp_before` values are present.

The release sometimes appends replay/scoring rows at the end of a game with an
old `sequenceNumber` and inconsistent start-score state. The published row order
is preserved and only this non-increasing tail is discarded. The comparison
exposes both `pbp_raw_rows` and `pbp_discarded_rows` so the cleanup is visible.

The comparison contains every CFBD-rated game in the requested seasons. Games
that fail the gate retain their old score and expose a `pbp_status` explaining
why the experimental score is blank. A later run recalculates all games from the
newest file rather than considering only previously unseen game ids.

## Formula parity

The PBP rows are ordered by `sequenceNumber`. The first `home_wp_before` value,
which represents the pregame state before the opening play, is included. The two
aggregates deliberately match `scripts/load_nfl_data.py`:

```python
win_chances_max_diff = wp.max() - wp.min()
win_prob_shifts = sum(
    (wp - wp.shift(-offset)).abs().sum()
    for offset in (1, 2, 3)
)
```

Only the 25% WP-movement component and 10% WP-range component are replaced. All
other NCAA rating components remain exactly as stored in the production DB.

## Outputs

- `_data/ncaa_game_ratings_comparison.csv`
- `assets/data/ncaa_game_ratings_comparison.json`

The main SQLite tables and the production NCAA CSV/JSON exports are never
modified by this script.
