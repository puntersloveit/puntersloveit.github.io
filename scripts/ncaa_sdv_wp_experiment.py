"""Build a side-by-side NCAA rating experiment from SportsDataverse PBP.

CFBD remains the source of truth for games, scores, team metadata, rankings and
box-score statistics.  This script downloads one public ESPN-derived parquet
file per requested season and replaces only the two win-probability components
with the same aggregation used by the NFL pipeline.

The main database and production NCAA exports are read-only.  Re-running the
script downloads the current release again, so a game first published with an
incomplete live feed is automatically reconsidered and rated once its complete
PBP is available.
"""

from __future__ import annotations

import argparse
import math
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests


PBP_URL = (
    "https://github.com/sportsdataverse/sportsdataverse-data/releases/"
    "download/espn_cfb_pbp/play_by_play_{season}.parquet"
)
WIN_PROB_SHIFTS_DIVIDER = math.sqrt(40) / 10
MIN_COMPLETE_PLAYS = 40

PBP_COLUMNS = [
    "game_id",
    "sequenceNumber",
    "period",
    "homeScore",
    "awayScore",
    "end.homeScore",
    "end.awayScore",
    "home_wp_before",
    "gameSpread",
    "gameSpreadAvailable",
    "status_type_completed",
]


def nfl_wp_metrics(probabilities: pd.Series) -> tuple[float, float]:
    """Return the two WP aggregates exactly as the NFL loaders calculate them."""
    wp = pd.to_numeric(probabilities, errors="coerce").dropna().astype(float)
    if wp.empty:
        raise ValueError("win-probability series is empty")
    if not wp.between(0, 1).all():
        raise ValueError("win probabilities must be between 0 and 1")

    max_diff = float(wp.max() - wp.min())
    shifts = float(sum((wp - wp.shift(-offset)).abs().sum() for offset in (1, 2, 3)))
    return max_diff, shifts


def rating_with_wp(row: pd.Series, max_diff: float, shifts: float) -> float:
    """Recalculate only the WP-dependent parts of the existing NCAA rating."""
    shifts_rating = min(10, math.sqrt(shifts) / WIN_PROB_SHIFTS_DIVIDER)
    max_diff_rating = max_diff * 10
    rating = (
        min(float(row["efficiency_rating"]) + float(row["overtimes_rating"]), 10) * 0.25
        + shifts_rating * 0.25
        + float(row["score_diff_rating"]) * 0.20
        + max_diff_rating * 0.10
        + float(row["stat_rating"]) * 0.10
        + float(row["leader_changes_rating"]) * 0.10
    )
    if float(row["tds_rating"]) == 0:
        rating = max(0, rating - 2)
    return round(rating, 2)


def _bool_series(values: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False)
    return values.astype(str).str.lower().isin({"true", "1", "yes"})


def _final_score(game_pbp: pd.DataFrame, preferred: str, fallback: str) -> int | None:
    values = pd.Series(dtype="float64")
    if preferred in game_pbp.columns:
        values = pd.to_numeric(game_pbp[preferred], errors="coerce").dropna()
    if values.empty:
        values = pd.to_numeric(game_pbp[fallback], errors="coerce").dropna()
    return int(values.max()) if not values.empty else None


def inspect_game_pbp(game_pbp: pd.DataFrame, cfbd_game: pd.Series) -> dict[str, object]:
    """Validate a PBP snapshot and calculate metrics when it is production-safe."""
    result: dict[str, object] = {
        "pbp_status": "complete",
        "pbp_raw_rows": int(len(game_pbp)),
        "pbp_plays": int(len(game_pbp)),
        "pbp_discarded_rows": 0,
        "pbp_periods": None,
        "pbp_home_score": None,
        "pbp_away_score": None,
        "pregame_home_wp": None,
        "game_spread": None,
        "new_win_chances_max_diff": None,
        "new_win_prob_shifts": None,
    }
    if game_pbp.empty:
        result["pbp_status"] = "missing_pbp"
        return result

    game_pbp = game_pbp.copy()
    # The published frame is already chronological. ESPN occasionally appends
    # replay/scoring rows to the end with an old sequence number and a broken
    # start-score state. Sorting would move those rows into the game and create
    # artificial WP jumps. Keep only the strictly increasing canonical stream.
    sequence = pd.to_numeric(game_pbp["sequenceNumber"], errors="coerce")
    previous_max = sequence.cummax().shift(1).fillna(-math.inf)
    canonical_rows = sequence.notna() & sequence.gt(previous_max)
    game_pbp = game_pbp.loc[canonical_rows].assign(_sequence=sequence[canonical_rows])
    result["pbp_plays"] = int(len(game_pbp))
    result["pbp_discarded_rows"] = int(result["pbp_raw_rows"] - len(game_pbp))

    periods = pd.to_numeric(game_pbp["period"], errors="coerce").dropna()
    result["pbp_periods"] = int(periods.max()) if not periods.empty else None
    result["pbp_home_score"] = _final_score(game_pbp, "end.homeScore", "homeScore")
    result["pbp_away_score"] = _final_score(game_pbp, "end.awayScore", "awayScore")

    source_completed = _bool_series(game_pbp["status_type_completed"])
    if source_completed.empty or not source_completed.all():
        result["pbp_status"] = "source_not_completed"
        return result
    if len(game_pbp) < MIN_COMPLETE_PLAYS or not result["pbp_periods"] or result["pbp_periods"] < 4:
        result["pbp_status"] = "implausibly_short"
        return result
    if (
        result["pbp_home_score"] != int(cfbd_game["home_points"])
        or result["pbp_away_score"] != int(cfbd_game["away_points"])
    ):
        result["pbp_status"] = "score_mismatch"
        return result

    spread_available = _bool_series(game_pbp["gameSpreadAvailable"])
    if spread_available.empty or not spread_available.any():
        result["pbp_status"] = "missing_spread"
        return result

    spreads = pd.to_numeric(game_pbp["gameSpread"], errors="coerce").dropna()
    result["game_spread"] = float(spreads.iloc[0]) if not spreads.empty else None
    wp = pd.to_numeric(game_pbp["home_wp_before"], errors="coerce").dropna()
    if wp.empty:
        result["pbp_status"] = "missing_win_probability"
        return result

    result["pregame_home_wp"] = float(wp.iloc[0])
    try:
        max_diff, shifts = nfl_wp_metrics(wp)
    except ValueError:
        result["pbp_status"] = "invalid_win_probability"
        return result
    result["new_win_chances_max_diff"] = max_diff
    result["new_win_prob_shifts"] = shifts
    return result


def download_pbp(season: int, cache_dir: Path, timeout: int = 120) -> tuple[Path, str | None]:
    """Download the latest season asset atomically; never reuse a stale snapshot."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / f"play_by_play_{season}.parquet"
    url = PBP_URL.format(season=season)
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()
    last_modified = response.headers.get("Last-Modified")

    fd, temporary_name = tempfile.mkstemp(prefix=f"pbp_{season}_", suffix=".parquet", dir=cache_dir)
    try:
        with os.fdopen(fd, "wb") as temporary_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    temporary_file.write(chunk)
        os.replace(temporary_name, destination)
    except Exception:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise
    finally:
        response.close()
    return destination, last_modified


def load_cfbd_baseline(database: Path, seasons: Iterable[int]) -> pd.DataFrame:
    placeholders = ",".join("?" for _ in seasons)
    query = f"""
        SELECT ratings.*, games.home_points, games.away_points,
               old_wp.win_chances_max_diff AS old_win_chances_max_diff,
               old_wp.win_prob_shifts AS old_win_prob_shifts
        FROM ncaa_game_ratings AS ratings
        JOIN ncaa_games AS games ON games.id = ratings.game_id
        LEFT JOIN ncaa_win_probability_metrics AS old_wp ON old_wp.id = ratings.game_id
        WHERE ratings.season IN ({placeholders})
        ORDER BY ratings.season DESC, ratings.week DESC, ratings.game_id
    """
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(query, connection, params=list(seasons))
    finally:
        connection.close()


def build_comparison(baseline: pd.DataFrame, pbp_frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    pbp = pd.concat(list(pbp_frames), ignore_index=True) if pbp_frames else pd.DataFrame()
    if not pbp.empty:
        missing = sorted(set(PBP_COLUMNS) - set(pbp.columns))
        if missing:
            raise ValueError(f"SportsDataverse PBP is missing required columns: {', '.join(missing)}")
        pbp["game_id"] = pd.to_numeric(pbp["game_id"], errors="coerce").astype("Int64")
        grouped = {int(game_id): group for game_id, group in pbp.groupby("game_id")}
    else:
        grouped = {}

    rows: list[dict[str, object]] = []
    for _, game in baseline.iterrows():
        game_id = int(game["game_id"])
        metrics = inspect_game_pbp(grouped.get(game_id, pd.DataFrame()), game)
        row = {
            "game_id": game_id,
            "season": int(game["season"]),
            "week": int(game["week"]),
            "season_type": game["season_type"],
            "away_team": game["away_team"],
            "home_team": game["home_team"],
            "old_game_rating": float(game["game_rating"]),
            "new_game_rating": None,
            "rating_delta": None,
            "old_win_chances_max_diff": game["old_win_chances_max_diff"],
            "old_win_prob_shifts": game["old_win_prob_shifts"],
            **metrics,
        }
        if metrics["pbp_status"] == "complete":
            new_rating = rating_with_wp(
                game,
                float(metrics["new_win_chances_max_diff"]),
                float(metrics["new_win_prob_shifts"]),
            )
            row["new_game_rating"] = new_rating
            row["rating_delta"] = round(new_rating - float(game["game_rating"]), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def parse_local_files(values: list[str]) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for value in values:
        season_text, separator, path_text = value.partition("=")
        if not separator:
            raise ValueError("--pbp-file values must use SEASON=PATH")
        result[int(season_text)] = Path(path_text)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("_data/puntersloveit.db"))
    parser.add_argument("--seasons", type=int, nargs="+", help="Seasons to compare; default is latest DB season")
    parser.add_argument("--pbp-file", action="append", default=[], metavar="SEASON=PATH")
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/ncaa_sdv"))
    parser.add_argument(
        "--csv-output", type=Path, default=Path("_data/ncaa_game_ratings_comparison.csv")
    )
    parser.add_argument(
        "--json-output", type=Path, default=Path("assets/data/ncaa_game_ratings_comparison.json")
    )
    args = parser.parse_args()

    local_files = parse_local_files(args.pbp_file)
    if args.seasons:
        seasons = sorted(set(args.seasons))
    else:
        connection = sqlite3.connect(f"file:{args.database.resolve()}?mode=ro", uri=True)
        try:
            latest = connection.execute("SELECT MAX(season) FROM ncaa_game_ratings").fetchone()[0]
        finally:
            connection.close()
        seasons = [int(latest)]

    pbp_frames: list[pd.DataFrame] = []
    for season in seasons:
        if season in local_files:
            path = local_files[season]
            print(f"Season {season}: using {path}")
        else:
            path, modified = download_pbp(season, args.cache_dir)
            suffix = f" (Last-Modified: {modified})" if modified else ""
            print(f"Season {season}: downloaded {path}{suffix}")
        pbp_frames.append(pd.read_parquet(path, columns=PBP_COLUMNS))

    baseline = load_cfbd_baseline(args.database, seasons)
    comparison = build_comparison(baseline, pbp_frames)
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.csv_output, index=False)
    comparison.to_json(args.json_output, orient="records")

    counts = comparison["pbp_status"].value_counts().to_dict()
    print(f"Compared {len(comparison)} CFBD games: {counts}")
    print(f"CSV: {args.csv_output}")
    print(f"JSON: {args.json_output}")


if __name__ == "__main__":
    main()
