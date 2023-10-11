import os
import cfbd
import math
import sqlite3
import datetime
import pandas as pd
import yaml

from cfbd.rest import ApiException
from functions import *

try:
    API_KEY = os.environ['API_KEY']
except KeyError:
    print('Token not available!')
print(API_KEY)

current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
CURRENT_SEASON = current_year if current_month > 7 else current_year - 1
DIVISION = 'fbs'

# Configure API key authorization: ApiKeyAuth
configuration = cfbd.Configuration()
configuration.api_key['Authorization'] = API_KEY
configuration.api_key_prefix['Authorization'] = 'Bearer'

sql_connection = sqlite3.connect('_data/puntersloveit.db')
sql_cursor = sql_connection.cursor()

GAMES_COLUMNS = [
# general
 'id',
 'season',
 'week',
 'start_date',
 'season_type',
 'completed',
 'conference_game',
 'excitement_index',
 'notes',
# home team
 'home_id',
 'home_team',
 'home_conference',
 'home_division',
 'home_points',
 'home_line_scores',
# away team
 'away_id',
 'away_team',
 'away_conference',
 'away_division',
 'away_points',
 'away_line_scores',
 ]

GAME_RATING_COLUMNS = [
 'game_id',
 'season',
 'week',
 'season_type',
 'excitement_index',
 'notes',
 'home_id',
 'home_team',
 'home_mascot',
 'home_abbreviation',
 'home_color',
 'home_rank',
 'home_conference',
 'home_division',
 'away_id',
 'away_team',
 'away_mascot',
 'away_abbreviation',
 'away_color',
 'away_rank',
 'away_conference',
 'away_division',
 'tds_rating',
 'sacks_rating',
 'interceptions_rating',
 'yards_rating',
 'stat_rating',
 'efficiency_rating',
 'overtimes_rating',
 'excitement_rating',
 'score_diff_rating',
 'leader_changes_rating',
 'game_rating',
 ]

SCORES_SUM_DIVIDER = math.sqrt(144) / 10
EXCIT_IND_DIVIDER = math.log(10, 4) / 10
SCORE_DIFF_DIVIDER = 29 / 10
YARDS_DIVIDER = math.sqrt(700) / 10

SATURATION_AMOUNT = 0.5
LIGHTENING_AMOUNT = 0.3

### Games Data
game_ids_from_db = set(
    pd.read_sql_query(f'SELECT id FROM ncaa_games WHERE season == {CURRENT_SEASON}', sql_connection).values.flatten()
)

api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

for season_type in ['regular', 'postseason']:
    try:
        # Get games and results for %division% and %year%
        response_result = api_instance.get_games(CURRENT_SEASON, division=DIVISION, season_type=season_type)
        if len(response_result) == 0:
            continue
        df_tmp = pd.DataFrame([i for i in map(cfbd.Game.to_dict, response_result)])
        df_tmp = df_tmp[GAMES_COLUMNS].query('completed == True')
        # Compare ids from db and response data
        game_ids_from_response = set(
            df_tmp.id.values.flatten()
        )
        new_games = game_ids_from_response - game_ids_from_db
        if len(new_games) == 0:
            print('0 new games')
            continue
        else:
            df_tmp.query(f'id in {list(new_games)}', inplace=True)
            df_tmp['scores_sum'] = df_tmp['home_points'] + df_tmp['away_points']
            df_tmp = df_tmp.query('scores_sum > 0')
            df_tmp['scores_diff'] = abs(df_tmp['home_points'] - df_tmp['away_points'])
            df_tmp['score_changes'] = df_tmp[['home_line_scores', 'away_line_scores']].apply(compare_scores, axis=1).apply(count_score_changes)
            df_tmp['number_of_quarters'] = df_tmp['home_line_scores'].apply(count_number_of_quarters)
            df_tmp.loc[:, 'home_line_scores'] = df_tmp.loc[:, 'home_line_scores'].apply(list).apply(str)
            df_tmp.loc[:, 'away_line_scores'] = df_tmp.loc[:, 'away_line_scores'].apply(list).apply(str)
            print(df_tmp.shape)
            df_tmp.to_sql('ncaa_games', sql_connection, if_exists='append', index=False)
    except ApiException as e:
        print("Exception when calling GamesApi->get_team_game_stats: %s\n" % e)

### Game Stats Summary Data
ids_from_games_table = set(pd.read_sql_query(f'select id from ncaa_games', sql_connection).values.flatten())
ids_from_stats_table = set(pd.read_sql_query(f'select id from ncaa_game_stats_summary', sql_connection).values.flatten())
new_game_ids = ids_from_games_table - ids_from_stats_table

api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

for game_id in new_game_ids:
    game_id = int(game_id)
    try:
        api_response = api_instance.get_team_game_stats(CURRENT_SEASON, game_id=game_id)
        if len(api_response) == 0:
            continue
        game_stats_df = parse_teamgamestats_into_pddf(api_response[0])
        game_stats_df.to_sql('ncaa_game_stats_summary', sql_connection, if_exists='append', index=False)                
    except ApiException as e:
        print(f"Exception when calling GamesApi->get_team_game_stats with game id {game_id}: {e}\n")

### AP TOP 25 Data
max_week_current_season = int(
    pd.read_sql_query(f'select max(week) from ncaa_rankings where season == {CURRENT_SEASON}', sql_connection)\
        .loc[0, 'max(week)']
    )

api_instance = cfbd.RankingsApi(cfbd.ApiClient(configuration))

for season_type in ['regular', 'postseason']:
    try:
        if season_type == 'regular' and max_week_current_season+1 > 16:
            continue
        elif season_type == 'postseason':
            rankings = api_instance.get_rankings(CURRENT_SEASON, season_type=season_type)
            if len(rankings) == 0:
                continue
        else:
            rankings = api_instance.get_rankings(CURRENT_SEASON, season_type=season_type, week=max_week_current_season+1)
            if len(rankings) == 0:
                continue

            for rank in rankings:
                df_tmp = parse_week_ap25_rank_into_pddf(rank)
                df_tmp.to_sql('ncaa_rankings', sql_connection, if_exists='append', index=False)

    except ApiException as e:
        print("Exception when calling RankingsApi->get_rankings: %s\n" % e)

### Table With Ratings
current_ratings_ids = tuple(pd.read_sql_query(f'select game_id from ncaa_game_ratings', sql_connection).values.flatten())
new_ids_from_games_table = set(pd.read_sql_query(f'select id from ncaa_games where id not in {current_ratings_ids}', sql_connection).values.flatten())
new_ids_from_stats_table = set(pd.read_sql_query(f'select id from ncaa_game_stats_summary where id not in {current_ratings_ids}', sql_connection).values.flatten())
new_ids_from_both = new_ids_from_games_table.intersection(new_ids_from_stats_table)

new_ids_from_both_tuple = str(tuple(new_ids_from_both)).replace(",", "") if len(new_ids_from_both) == 1 else tuple(new_ids_from_both)

query = f'''
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

WHERE games.id in {new_ids_from_both_tuple}

'''
game_ratings_update = pd.read_sql_query(query, sql_connection)

for col in ['rushingTDs',
            'puntReturnTDs',
            'passingTDs',
            'kickReturnTDs',
            'interceptionTDs',
            'totalFumbles',
            'defensiveTDs',
            'sacks',
            'interceptions',
            'rushingYards',
            'netPassingYards',
            'totalYards',
            'excitement_index',
            ]:
    game_ratings_update[col].fillna(game_ratings_update[col].median(), inplace=True)

game_ratings_update['totalTDs'] = game_ratings_update['rushingTDs'] + game_ratings_update['puntReturnTDs'] + game_ratings_update['passingTDs'] + game_ratings_update['kickReturnTDs'] + game_ratings_update['interceptionTDs']
game_ratings_update = game_ratings_update.drop(['rushingTDs', 'puntReturnTDs', 'passingTDs', 'kickReturnTDs', 'interceptionTDs', 'defensiveTDs', 'rushingYards', 'netPassingYards',], axis=1)

game_ratings_update['tds_rating'] = game_ratings_update['totalTDs'].apply(lambda x: min(10, max(0, x - 4)))
game_ratings_update['sacks_rating'] = game_ratings_update['sacks'].apply(lambda x: min(12, x) / 1.2)
game_ratings_update['interceptions_rating'] = game_ratings_update['interceptions'].apply(lambda x: min(5, x) / 0.5)
game_ratings_update['yards_rating'] = game_ratings_update['totalYards'].apply(lambda x: math.sqrt(min(700, max(0, x - 500))) / YARDS_DIVIDER)

game_ratings_update['stat_rating'] = game_ratings_update['tds_rating'] * 0.1\
                  + game_ratings_update['sacks_rating'] * 0.1\
                  + game_ratings_update['interceptions_rating'] * 0.1\
                  + game_ratings_update['yards_rating'] * 0.7

game_ratings_update.loc[:, 'efficiency_rating'] = game_ratings_update.loc[:, 'scores_sum']\
    .apply(lambda x: math.sqrt(x) / SCORES_SUM_DIVIDER)
game_ratings_update.loc[:, 'overtimes_rating'] = game_ratings_update.loc[:, 'number_of_quarters']\
    .apply(lambda x: 2 if x > 9 else 1 if x > 4 else 0)
game_ratings_update.loc[:, 'excitement_rating'] = game_ratings_update.loc[:, 'excitement_index']\
    .apply(lambda x: math.log(max(x, 1), 4) / EXCIT_IND_DIVIDER if x < 10 else 10)
game_ratings_update.loc[:, 'score_diff_rating'] = game_ratings_update.loc[:, 'scores_diff']\
    .apply(lambda x: 0 if x > 29 else (30 - x) / SCORE_DIFF_DIVIDER)
game_ratings_update.loc[:, 'leader_changes_rating'] = game_ratings_update.loc[:, 'score_changes']\
    .apply(lambda x: 10 if x > 4 else 9 if x == 4 else 6 if x == 3 else 3 if x == 2 else 0)

game_ratings_update.loc[:, 'game_rating'] = (game_ratings_update.loc[:, 'efficiency_rating'] + game_ratings_update.loc[:, 'overtimes_rating'])\
                         .apply(lambda x: min(x, 10)) * 0.25\
                         + game_ratings_update.loc[:, 'score_diff_rating'] * 0.25\
                         + game_ratings_update.loc[:, 'stat_rating'] * 0.25\
                         + game_ratings_update.loc[:, 'excitement_rating'] * 0.2\
                         + game_ratings_update.loc[:, 'leader_changes_rating'] * 0.05

delete_irrelevant_notes = lambda x: '' if x is None \
    else x if x.__contains__('bowl') or x.__contains__('kickoff') or x.__contains__('championship') or x.__contains__('classic') else ''
game_ratings_update['notes'] = game_ratings_update.notes\
    .apply(lambda x: x.lower().replace('"', '') if x is not None else None).apply(delete_irrelevant_notes)

game_ratings_update[GAME_RATING_COLUMNS].to_sql('ncaa_game_ratings', sql_connection, if_exists='append', index=False)

### Prepare Game Ratings to Site
game_ratings = pd.read_sql_query('select * from ncaa_game_ratings', sql_connection)

add_rank_to_team_name = lambda x: f'{x[0]}({int(x[1])})' if x[1] != -1 else x[0]
game_ratings['away_rank'] = game_ratings['away_rank'].fillna(-1).astype(int)
game_ratings['home_rank'] = game_ratings['home_rank'].fillna(-1).astype(int)
game_ratings['week'] = game_ratings['week'].astype(str)
game_ratings.loc[game_ratings.season_type == 'postseason', 'week'] = 'Bowls'
game_ratings['away_team'] = game_ratings[['away_team', 'away_rank']].apply(add_rank_to_team_name, axis=1)
game_ratings['home_team'] = game_ratings[['home_team', 'home_rank']].apply(add_rank_to_team_name, axis=1)
game_ratings['game_rating'] = game_ratings['game_rating'].round(2)

game_ratings['away_color'] = game_ratings['away_color'].apply(lambda x: saturate_hex_color(x, SATURATION_AMOUNT, LIGHTENING_AMOUNT))
game_ratings['home_color'] = game_ratings['home_color'].apply(lambda x: saturate_hex_color(x, SATURATION_AMOUNT, LIGHTENING_AMOUNT))

game_ratings[['away_color', 
              'home_color', 
              'season', 
              'week', 
              'notes', 
              'away_id', 
              'home_id', 
              'away_team',
              'home_team', 
              'game_rating']]\
    .sort_values('game_rating', ascending=False)\
        .to_csv('_data/ncaa_game_ratings.csv', index=False)

unique_seasons = []
for y in range(game_ratings.season.max(), game_ratings.season.min()-1, -1):
    weeks = game_ratings.query(f'season == {y}').week.unique().tolist()
    if y == CURRENT_SEASON:
        weeks = weeks[::-1]
    unique_seasons.append(
    {
        'season': y,
        'weeks': weeks + ['All']
    }       
    )

with open('_data/ncaa_unique_seasons.yml', 'w') as file:
    yaml.dump(unique_seasons, file)