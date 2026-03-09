# Repository Agent Guide

## 1) Project purpose
PuntersLoveIt is a static, spoiler-free ratings site for American football games (NFL + NCAA).
The product goal is simple: rank games by watchability/entertainment value without showing classic spoiler-heavy game context.

Core constraints:
- No backend runtime for users (GitHub Pages + pre-generated data files).
- Data pipelines run in GitHub Actions and commit generated artifacts back to the repo.
- Ratings formulas and interpretation are documented in `README.md`.

---

## 2) High-level architecture
The system has 3 layers:

1. Data ingestion + scoring (`scripts/*.py`)
- Pull source data from `nfl_data_py` (NFL) and CFBD API (NCAA).
- Normalize and aggregate into SQLite tables in `_data/puntersloveit.db`.
- Compute game and team ratings.
- Export final artifacts for the static site.

2. Data artifacts (`_data/*`)
Main published artifacts consumed by Jekyll layouts:
- `_data/nfl_game_ratings.csv`
- `_data/nfl_game_ratings_extended.csv`
- `_data/nfl_team_ratings.json`
- `_data/nfl_unique_seasons.yml`
- `_data/nfl_teams.yml`
- `_data/ncaa_game_ratings.csv`
- `_data/ncaa_game_ratings_extended.csv`
- `_data/ncaa_team_ratings.json`
- `_data/ncaa_unique_seasons.yml`
- `_data/ncaa_teams.yml`

3. Static rendering (Jekyll)
- Layouts in `_layouts/` + shared JS in `assets/js/ratings.js`.
- Pages are generated from `_data` files at build time.
- No runtime API calls from the frontend.

---

## 3) Pipeline responsibilities

### NFL scripts
- `scripts/load_nfl_data.py`
  - Full historical rebuild (from 1999 through current season).
  - Replaces core NFL tables and exports all NFL artifacts.
- `scripts/update_nfl_data.py`
  - Incremental update for current season only.
  - Appends only new games to ratings tables.
  - Must remain safe when there are zero new games.

### NCAA scripts
- `scripts/load_ncaa_data.py`
  - Full historical NCAA rebuild.
  - Loads games/stats/rankings/team metadata.
  - Builds ratings and exports all NCAA artifacts.
- `scripts/update_ncaa_data.py`
  - Incremental NCAA update for current season.
  - Pulls only what is needed for new games.
  - Must remain safe when there are zero new games.
- `scripts/backfill_ncaa_wp_and_rebuild.py`
  - Backfills NCAA win-probability proxy metrics and rebuilds NCAA exports.

### Shared helpers
- `scripts/functions.py`
  - Color normalization helpers.
  - Score-change helpers.
  - CFBD-related helper utilities.
  - Shared exporter helpers (including teams YAML export).

---

## 4) Critical external constraint: CFBD quota
CFBD token quota is limited (currently treated as 1000 requests/month).

Mandatory rule:
- Do **not** increase NCAA API request volume without explicit approval from the repo owner.

Practical implications:
- Keep request pattern in `update_ncaa_data.py` at current behavior unless approved.
- Prefer period-based batching already implemented.
- Avoid adding per-game API loops against CFBD endpoints.
- Reuse existing tables and already-fetched data whenever possible.

If a change may affect request count:
- Document expected request delta.
- Gate behavior behind an explicit flag or separate script.
- Get approval before merging.

---

## 5) Frontend/data contracts that must not break
The layouts rely on stable artifact names and core fields.

Examples:
- `ncaa_ratings.html` uses `site.data.ncaa_game_ratings`, `site.data.ncaa_unique_seasons`, `site.data.ncaa_teams`.
- `nfl_ratings.html` uses `site.data.nfl_game_ratings`, `site.data.nfl_unique_seasons`, `site.data.nfl_teams`.
- Extended layouts rely on `*_game_ratings_extended` payloads.
- Team pages rely on `*_team_ratings.json`.

Rules:
- Keep exported file names stable.
- Keep required columns/keys stable unless frontend is updated in the same change.
- Keep color values valid hex (`#RRGGBB`).

---

## 6) GitHub Actions operations
Workflows in `.github/workflows/` run loads/updates and commit outputs.

Operational rules:
- Workflows should not fail when there are no content changes.
- Commit steps should be no-op safe if `git diff --cached --quiet`.
- Python dependency set is defined by `requirements.txt`.

---

## 7) Data and DB conventions
- Main DB: `_data/puntersloveit.db`.
- Local backup folder: `_data/local_backups/`.
- Prefer deterministic exports (stable field names/order where possible).
- Prefer idempotent update behavior where feasible.

For NCAA team filters:
- `_data/ncaa_teams.yml` must be auto-generated from computed `ncaa_team_ratings` to correctly include newly transitioned FBS teams.

---

## 8) Change rules for contributors/agents
When editing this repo:
- Keep architecture static-site-first (no backend requirement).
- Preserve rating semantics unless change is intentional and documented.
- Do not silently alter NCAA request volume.
- Keep incremental scripts robust on "no new games" days.
- Validate build and basic smoke behavior before finalizing.

Minimum validation checklist:
1. `bundle exec jekyll build`
2. `python -m compileall scripts tests` (or equivalent interpreter path)
3. Unit tests (if modified): `python -m unittest -v ...`
4. Optional smoke test via `jekyll serve` + page checks

---

## 9) Notes for future refactors
Preferred direction (without changing product meaning):
- Reduce duplicated scoring logic across load/update scripts.
- Keep shared computation code in reusable helpers/modules.
- Introduce more unit coverage for pure functions and export contracts.
- Keep CI checks lightweight and quota-safe.

