import argparse
import datetime
import math
import os
import sqlite3

import pandas as pd
import yaml

from functions import (
    get_pregame_win_probabilities_safe,
    is_cfbd_quota_exhausted,
    pregame_wp_to_metrics,
    saturate_hex_color,
    write_teams_yaml,
)

SCORES_SUM_DIVIDER = math.sqrt(100) / 10
EXCIT_IND_DIVIDER = math.log(10, 4) / 10
SCORE_DIFF_DIVIDER = 19 / 10
YARDS_DIVIDER = math.sqrt(650) / 10
WIN_PROB_SHIFTS_DIVIDER = math.sqrt(40) / 10

SATURATION_AMOUNT = 0.5
LIGHTENING_AMOUNT = 0.3

GAME_RATING_COLUMNS = [
    "game_id",
    "season",
    "week",
    "season_type",
    "excitement_index",
    "notes",
    "home_id",
    "home_team",
    "home_mascot",
    "home_abbreviation",
    "home_color",
    "home_rank",
    "home_conference",
    "home_division",
    "away_id",
    "away_team",
    "away_mascot",
    "away_abbreviation",
    "away_color",
    "away_rank",
    "away_conference",
    "away_division",
    "tds_rating",
    "sacks_rating",
    "interceptions_rating",
    "yards_rating",
    "stat_rating",
    "efficiency_rating",
    "overtimes_rating",
    "excitement_rating",
    "score_diff_rating",
    "leader_changes_rating",
    "game_rating",
]


def ensure_wp_table(sql_connection: sqlite3.Connection) -> None:
    sql_connection.execute(
        """
        CREATE TABLE IF NOT EXISTS ncaa_win_probability_metrics (
            id INTEGER,
            win_chances_max_diff REAL,
            win_prob_shifts REAL
        )
        """
    )
    sql_connection.commit()


def get_missing_wp_games(sql_connection: sqlite3.Connection, min_season: int) -> pd.DataFrame:
    query = """
    SELECT g.id, g.season, g.season_type, g.week
    FROM ncaa_games g
    LEFT JOIN ncaa_win_probability_metrics w
        ON g.id = w.id
    WHERE w.id IS NULL
      AND g.season >= ?
    """
    missing_games = pd.read_sql_query(query, sql_connection, params=[min_season])
    if missing_games.empty:
        return missing_games
    return missing_games.astype({"id": "int64", "season": "int64", "week": "int64"})


def backfill_wp(sql_connection: sqlite3.Connection, api_key: str, min_season: int) -> None:
    ensure_wp_table(sql_connection)
    missing_games = get_missing_wp_games(sql_connection, min_season)
    if missing_games.empty:
        print(f"No missing win probability metrics for season >= {min_season}.")
        return

    periods = (
        missing_games[["season", "season_type", "week"]]
        .drop_duplicates()
        .sort_values(["season", "season_type", "week"], ascending=[False, True, False])
        .reset_index(drop=True)
    )
    period_to_ids = (
        missing_games.groupby(["season", "season_type", "week"])["id"]
        .apply(lambda x: set(x.astype(int).tolist()))
        .to_dict()
    )

    collected_rows: list[dict[str, float | int]] = []
    quota_exhausted = False
    processed_periods = 0
    for _, period in periods.iterrows():
        season = int(period["season"])
        season_type = str(period["season_type"])
        week = int(period["week"])
        ids_in_period = period_to_ids[(season, season_type, week)]

        try:
            pregame_data = get_pregame_win_probabilities_safe(
                api_key=api_key,
                year=season,
                week=week,
                season_type=season_type,
            )
            processed_periods += 1
        except Exception as error:
            print(
                f"WP fetch failed for season={season}, season_type={season_type}, "
                f"week={week}: {error}"
            )
            if is_cfbd_quota_exhausted(error):
                quota_exhausted = True
                print("CFBD monthly quota exhausted, stopping WP backfill.")
                break
            continue

        for game in pregame_data:
            game_id = int(game["game_id"])
            if game_id not in ids_in_period:
                continue
            wp_metrics = pregame_wp_to_metrics(game["home_win_probability"])
            if wp_metrics is None:
                continue

            win_chances_max_diff, win_prob_shifts = wp_metrics
            collected_rows.append(
                {
                    "id": game_id,
                    "win_chances_max_diff": float(win_chances_max_diff),
                    "win_prob_shifts": float(win_prob_shifts),
                }
            )

    if collected_rows:
        (
            pd.DataFrame(collected_rows)
            .drop_duplicates(subset=["id"])
            .to_sql("ncaa_win_probability_metrics", sql_connection, if_exists="append", index=False)
        )
        sql_connection.execute(
            """
            DELETE FROM ncaa_win_probability_metrics
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM ncaa_win_probability_metrics
                GROUP BY id
            )
            """
        )
        sql_connection.commit()

    remaining_missing = get_missing_wp_games(sql_connection, min_season).shape[0]
    print(f"Processed periods: {processed_periods}")
    print(f"Inserted/updated WP rows: {len(collected_rows)}")
    print(f"Remaining missing WP rows for season >= {min_season}: {remaining_missing}")
    if quota_exhausted:
        print("Backfill was partial because of quota exhaustion.")


def rebuild_ratings(sql_connection: sqlite3.Connection) -> None:
    query = """
    SELECT
        games.id as game_id,
        games.season,
        games.week,
        games.season_type,
        excitement_index,
        notes,
        home_id,
        home_team,
        home_team_info.mascot as home_mascot,
        home_team_info.abbreviation as home_abbreviation,
        home_team_info.color as home_color,
        home_ranks.rank as home_rank,
        home_conference,
        home_division,
        away_id,
        away_team,
        away_team_info.mascot as away_mascot,
        away_team_info.abbreviation as away_abbreviation,
        away_team_info.color as away_color,
        away_ranks.rank as away_rank,
        away_conference,
        away_division,
        scores_sum,
        scores_diff,
        score_changes,
        number_of_quarters,
        win_chances_max_diff,
        win_prob_shifts,
        rushingTDs,
        puntReturnTDs,
        passingTDs,
        kickReturnTDs,
        interceptionTDs,
        totalFumbles,
        defensiveTDs,
        sacks,
        interceptions,
        rushingYards,
        netPassingYards,
        totalYards
    FROM ncaa_games AS games
    LEFT JOIN ncaa_game_stats_summary AS stats
        ON games.id = stats.id
    LEFT JOIN ncaa_win_probability_metrics AS win_prob_metrics
        ON games.id = win_prob_metrics.id
    LEFT JOIN ncaa_rankings AS home_ranks
        ON games.home_team = home_ranks.school
           AND games.season = home_ranks.season
           AND games.week = home_ranks.week
           AND games.season_type = home_ranks.season_type
    LEFT JOIN ncaa_rankings AS away_ranks
        ON games.away_team = away_ranks.school
           AND games.season = away_ranks.season
           AND games.week = away_ranks.week
           AND games.season_type = away_ranks.season_type
    LEFT JOIN ncaa_teams_info AS home_team_info
        ON games.home_id = home_team_info.id
    LEFT JOIN ncaa_teams_info AS away_team_info
        ON games.away_id = away_team_info.id
    """
    game_ratings = pd.read_sql_query(query, sql_connection)

    numeric_columns = [
        "rushingTDs",
        "puntReturnTDs",
        "passingTDs",
        "kickReturnTDs",
        "interceptionTDs",
        "totalFumbles",
        "defensiveTDs",
        "sacks",
        "interceptions",
        "rushingYards",
        "netPassingYards",
        "totalYards",
        "win_chances_max_diff",
        "win_prob_shifts",
        "excitement_index",
    ]
    for col in numeric_columns:
        game_ratings[col] = pd.to_numeric(game_ratings[col], errors="coerce")

    for col in numeric_columns:
        median_value = game_ratings[col].median()
        game_ratings[col].fillna(0 if pd.isna(median_value) else median_value, inplace=True)

    game_ratings["totalTDs"] = (
        game_ratings["rushingTDs"]
        + game_ratings["puntReturnTDs"]
        + game_ratings["passingTDs"]
        + game_ratings["kickReturnTDs"]
        + game_ratings["interceptionTDs"]
    )
    game_ratings = game_ratings.drop(
        [
            "rushingTDs",
            "puntReturnTDs",
            "passingTDs",
            "kickReturnTDs",
            "interceptionTDs",
            "defensiveTDs",
            "rushingYards",
            "netPassingYards",
        ],
        axis=1,
    )

    game_ratings["tds_rating"] = game_ratings["totalTDs"].apply(lambda x: min(10, x))
    game_ratings["sacks_rating"] = game_ratings["sacks"].apply(lambda x: min(12, x) / 1.2)
    game_ratings["interceptions_rating"] = game_ratings["interceptions"].apply(
        lambda x: min(7, x) / 0.7
    )
    game_ratings["yards_rating"] = game_ratings["totalYards"].apply(
        lambda x: math.sqrt(min(650, max(0, x - 350))) / YARDS_DIVIDER
    )
    game_ratings["stat_rating"] = (
        game_ratings["tds_rating"] * 0.3
        + game_ratings["sacks_rating"] * 0.1
        + game_ratings["interceptions_rating"] * 0.1
        + game_ratings["yards_rating"] * 0.5
    )

    game_ratings["efficiency_rating"] = game_ratings["scores_sum"].apply(
        lambda x: math.sqrt(x) / SCORES_SUM_DIVIDER
    )
    game_ratings["overtimes_rating"] = game_ratings["number_of_quarters"].apply(
        lambda x: 1 if x > 4 else 0
    )
    game_ratings["excitement_rating"] = game_ratings["excitement_index"].apply(
        lambda x: math.log(max(x, 1), 4) / EXCIT_IND_DIVIDER if x < 10 else 10
    )
    game_ratings["score_diff_rating"] = game_ratings["scores_diff"].apply(
        lambda x: 7.5 if x == 0 else max(-10, (20 - x) / SCORE_DIFF_DIVIDER)
    )
    game_ratings["leader_changes_rating"] = game_ratings["score_changes"].apply(lambda x: min(10, x))
    game_ratings["win_prob_shifts_rating"] = game_ratings["win_prob_shifts"].apply(
        lambda x: min(10, math.sqrt(x) / WIN_PROB_SHIFTS_DIVIDER)
    )
    game_ratings["win_chances_max_diff_rating"] = game_ratings["win_chances_max_diff"].apply(
        lambda x: x * 10
    )

    game_ratings["game_rating"] = (
        (game_ratings["efficiency_rating"] + game_ratings["overtimes_rating"]).apply(lambda x: min(x, 10))
        * 0.25
        + game_ratings["win_prob_shifts_rating"] * 0.25
        + game_ratings["score_diff_rating"] * 0.20
        + game_ratings["win_chances_max_diff_rating"] * 0.10
        + game_ratings["stat_rating"] * 0.10
        + game_ratings["leader_changes_rating"] * 0.10
    )
    game_ratings["game_rating"] = game_ratings[["game_rating", "tds_rating"]].apply(
        lambda x: max(0, x["game_rating"] - 2) if x["tds_rating"] == 0 else x["game_rating"],
        axis=1,
    ).round(2)

    delete_irrelevant_notes = (
        lambda x: ""
        if x is None
        else x
        if "bowl" in x or "kickoff" in x or "championship" in x or "classic" in x
        else ""
    )
    game_ratings["notes"] = (
        game_ratings.notes.apply(lambda x: x.lower().replace('"', "") if x is not None else None)
        .apply(delete_irrelevant_notes)
    )

    game_ratings[GAME_RATING_COLUMNS].to_sql(
        "ncaa_game_ratings", sql_connection, if_exists="replace", index=False
    )

    ratings_for_export = pd.read_sql_query("select * from ncaa_game_ratings", sql_connection)
    ratings_for_export["away_color"] = ratings_for_export["away_color"].apply(
        lambda x: saturate_hex_color(x, SATURATION_AMOUNT, LIGHTENING_AMOUNT)
    )
    ratings_for_export["home_color"] = ratings_for_export["home_color"].apply(
        lambda x: saturate_hex_color(x, SATURATION_AMOUNT, LIGHTENING_AMOUNT)
    )

    home_ratings = (
        ratings_for_export.query('home_division == "fbs"')
        .groupby(["season", "home_team"])
        .agg({"game_rating": "mean", "home_color": "first", "home_conference": "first"})
        .reset_index()
    )
    home_ratings.columns = ["season", "team", "avg_game_rating", "team_color", "conference"]

    away_ratings = (
        ratings_for_export.query('away_division == "fbs"')
        .groupby(["season", "away_team"])
        .agg({"game_rating": "mean", "away_color": "first", "away_conference": "first"})
        .reset_index()
    )
    away_ratings.columns = ["season", "team", "avg_game_rating", "team_color", "conference"]

    team_ratings = pd.concat([home_ratings, away_ratings])
    team_ratings = (
        team_ratings.groupby(["season", "team"])
        .agg({"avg_game_rating": "mean", "team_color": "first", "conference": "first"})
        .reset_index()
    )
    team_ratings.to_sql("ncaa_team_ratings", sql_connection, if_exists="replace", index=False)

    team_ratings = pd.read_sql_query("select * from ncaa_team_ratings", sql_connection)
    team_ratings.to_json("_data/ncaa_team_ratings.json", orient="records")
    write_teams_yaml(team_ratings["team"].tolist(), "_data/ncaa_teams.yml")

    add_rank_to_team_name = lambda x: f"{x[0]}({int(x[1])})" if x[1] != -1 else x[0]
    ratings_for_export["away_rank"] = ratings_for_export["away_rank"].fillna(-1).astype(int)
    ratings_for_export["home_rank"] = ratings_for_export["home_rank"].fillna(-1).astype(int)
    ratings_for_export["week"] = ratings_for_export["week"].astype(str)
    ratings_for_export.loc[ratings_for_export.season_type == "postseason", "week"] = "Bowls"
    ratings_for_export["away_team"] = ratings_for_export[["away_team", "away_rank"]].apply(
        add_rank_to_team_name, axis=1
    )
    ratings_for_export["home_team"] = ratings_for_export[["home_team", "home_rank"]].apply(
        add_rank_to_team_name, axis=1
    )
    ratings_for_export["game_rating"] = ratings_for_export["game_rating"].round(2)

    ratings_for_export[
        [
            "away_color",
            "home_color",
            "season",
            "week",
            "notes",
            "away_id",
            "home_id",
            "away_team",
            "home_team",
            "game_rating",
        ]
    ].sort_values("game_rating", ascending=False).to_csv("_data/ncaa_game_ratings.csv", index=False)
    ratings_for_export.to_csv("_data/ncaa_game_ratings_extended.csv", index=False)

    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month
    current_season = current_year if current_month > 7 else current_year - 1

    unique_seasons = []
    for season in range(ratings_for_export.season.max(), ratings_for_export.season.min() - 1, -1):
        weeks = ratings_for_export.query(f"season == {season}").week.unique().tolist()
        if season == current_season:
            weeks = weeks[::-1]
        unique_seasons.append({"season": season, "weeks": weeks + ["All"]})
    unique_seasons.append({"season": -1, "weeks": ["All"]})

    with open("_data/ncaa_unique_seasons.yml", "w") as file:
        yaml.dump(unique_seasons, file)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-season", type=int, default=2022)
    args = parser.parse_args()

    api_key = os.environ.get("API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("API_KEY env var is required.")

    sql_connection = sqlite3.connect("_data/puntersloveit.db")
    try:
        backfill_wp(sql_connection, api_key=api_key, min_season=args.min_season)
        rebuild_ratings(sql_connection)
        missing_after = get_missing_wp_games(sql_connection, args.min_season).shape[0]
        print(f"Final missing WP rows for season >= {args.min_season}: {missing_after}")
        print(
            "Current counts: "
            + str(
                pd.read_sql_query(
                    """
                    SELECT 'ncaa_games' as table_name, COUNT(*) as cnt FROM ncaa_games
                    UNION ALL SELECT 'ncaa_win_probability_metrics', COUNT(*) FROM ncaa_win_probability_metrics
                    UNION ALL SELECT 'ncaa_game_ratings', COUNT(*) FROM ncaa_game_ratings
                    UNION ALL SELECT 'ncaa_team_ratings', COUNT(*) FROM ncaa_team_ratings
                    """,
                    sql_connection,
                ).to_dict(orient="records")
            )
        )
    finally:
        sql_connection.close()


if __name__ == "__main__":
    main()
