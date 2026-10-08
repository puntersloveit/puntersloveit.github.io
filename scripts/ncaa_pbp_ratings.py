"""Persist the legacy baseline and upgrade NCAA ratings when full PBP arrives."""

from pathlib import Path
import sqlite3

import pandas as pd

from ncaa_sdv_wp_experiment import (
    PBP_COLUMNS, download_pbp, inspect_game_pbp, rating_with_wp,
)


def refresh_pbp_ratings(connection: sqlite3.Connection, seasons, local_files=None):
    """Retry all rated games in selected seasons, including already known games.

    Download failures preserve published ratings. Accepted metrics persist across
    missing/invalid snapshots and full CFBD rebuilds. No CFBD calls are made.
    """
    local_files = local_files or {}
    connection.execute("""
        CREATE TABLE IF NOT EXISTS ncaa_rating_sources (
            game_id INTEGER PRIMARY KEY,
            legacy_game_rating REAL NOT NULL,
            rating_source TEXT NOT NULL DEFAULT 'legacy',
            pbp_status TEXT NOT NULL DEFAULT 'pending',
            win_chances_max_diff REAL,
            win_prob_shifts REAL,
            pbp_plays INTEGER,
            home_points INTEGER,
            away_points INTEGER
        )
    """)
    for season in sorted(set(int(s) for s in seasons)):
        games = pd.read_sql_query("""
            SELECT r.*, g.home_points, g.away_points
            FROM ncaa_game_ratings r JOIN ncaa_games g ON g.id=r.game_id
            WHERE r.season=? AND g.completed=1
        """, connection, params=[season])
        if games.empty:
            continue
        with connection:
            connection.executemany("""
                INSERT OR IGNORE INTO ncaa_rating_sources(game_id,legacy_game_rating)
                VALUES (?,?)
            """, [(int(g.game_id), float(g.game_rating)) for g in games.itertuples()])

        grouped = None
        failure = None
        try:
            path = local_files.get(season)
            if path is None:
                path, _ = download_pbp(season, Path('.cache/ncaa_sdv'))
            pbp = pd.read_parquet(path, columns=PBP_COLUMNS)
            pbp['game_id'] = pd.to_numeric(pbp.game_id, errors='raise').astype(int)
            grouped = dict(tuple(pbp.groupby('game_id')))
        except Exception as error:
            failure = 'source_unavailable'
            print(f'NCAA PBP season {season}: unavailable ({error}); preserving ratings')

        accepted = 0
        with connection:
            for _, game in games.iterrows():
                gid = int(game.game_id)
                state = connection.execute("""
                    SELECT win_chances_max_diff, win_prob_shifts, home_points, away_points
                    FROM ncaa_rating_sources WHERE game_id=?
                """, [gid]).fetchone()
                metrics = None
                if grouped is not None:
                    metrics = inspect_game_pbp(grouped.get(gid, pd.DataFrame()), game)
                status = failure if metrics is None else metrics['pbp_status']
                if metrics is not None and status == 'complete':
                    state = (metrics['new_win_chances_max_diff'], metrics['new_win_prob_shifts'],
                             int(game.home_points), int(game.away_points))
                    connection.execute("""
                        UPDATE ncaa_rating_sources SET win_chances_max_diff=?,
                            win_prob_shifts=?, home_points=?, away_points=?, pbp_plays=?
                        WHERE game_id=?
                    """, [*state, metrics['pbp_plays'], gid])
                # Reapply accepted metrics after a full CFBD rebuild; a failed
                # download or temporary partial snapshot must not downgrade it.
                valid_cached = (state[0] is not None and state[1] is not None
                                and state[2] == int(game.home_points)
                                and state[3] == int(game.away_points))
                source = 'pbp' if valid_cached else 'legacy'
                if valid_cached:
                    score = rating_with_wp(game, float(state[0]), float(state[1]))
                    connection.execute('UPDATE ncaa_game_ratings SET game_rating=? WHERE game_id=?',
                                       [score, gid])
                    accepted += 1
                else:
                    connection.execute('''
                        UPDATE ncaa_game_ratings SET game_rating=(
                            SELECT legacy_game_rating FROM ncaa_rating_sources WHERE game_id=?
                        ) WHERE game_id=?
                    ''', [gid, gid])
                connection.execute("""
                    UPDATE ncaa_rating_sources SET rating_source=?, pbp_status=? WHERE game_id=?
                """, [source, status, gid])
        print(f'NCAA PBP season {season}: {accepted}/{len(games)} ratings use PBP')


def refresh_current_season(connection, season):
    # Continue retrying enrolled fallback games even after a season rollover.
    # Unenrolled historical seasons are left alone.
    pending_seasons = []
    if connection.execute("SELECT 1 FROM sqlite_master WHERE name='ncaa_rating_sources'").fetchone():
        pending_seasons = [row[0] for row in connection.execute('''
            SELECT DISTINCT r.season FROM ncaa_game_ratings r
            JOIN ncaa_rating_sources s ON s.game_id=r.game_id
            WHERE s.rating_source='legacy'
        ''')]
    refresh_pbp_ratings(connection, [season, *pending_seasons])
