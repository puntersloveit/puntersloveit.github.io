import cfbd
import math
import sqlite3
import datetime
import os
import pandas as pd
import yaml

from cfbd.rest import ApiException
from functions import *

try:
    API_KEY = os.environ['API_KEY']
except KeyError:
    API_KEY = 'Token not available!'

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

TEAM_INFO_COLUMNS = [
 'id',
 'school',
 'mascot',
 'abbreviation',
 'classification',
 'color',
 'alt_color',
 'logos',
 ]
LOGOS_DIRECTORY = 'team_logos/ncaa/'

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

### Games Data
api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

for year in range(2015, CURRENT_SEASON + 1):
    for season_type in ['regular', 'postseason']:
        try:
            # Get games and results for %division% and %year%
            response_result = api_instance.get_games(year, division=DIVISION, season_type=season_type)
            if len(response_result) == 0:
                continue            
            df_tmp = pd.DataFrame([i for i in map(cfbd.Game.to_dict, response_result)])
            df_tmp['scores_sum'] = df_tmp['home_points'] + df_tmp['away_points']

            df_tmp = df_tmp[GAMES_COLUMNS + ['scores_sum']].query('completed == True and scores_sum > 0')
            # Compute additional values
            df_tmp['scores_diff'] = abs(df_tmp['home_points'] - df_tmp['away_points'])
            df_tmp['score_changes'] = df_tmp[['home_line_scores', 'away_line_scores']].apply(compare_scores, axis=1).apply(count_score_changes)
            df_tmp['number_of_quarters'] = df_tmp['home_line_scores'].apply(count_number_of_quarters)
            df_tmp.loc[:, 'home_line_scores'] = df_tmp.loc[:, 'home_line_scores'].apply(list).apply(str)
            df_tmp.loc[:, 'away_line_scores'] = df_tmp.loc[:, 'away_line_scores'].apply(list).apply(str)

            df_tmp.to_sql('ncaa_games', sql_connection, if_exists='append', index=False)
        except ApiException as e:
            print("Exception when calling GamesApi->get_team_game_stats: %s\n" % e)

### Game Stats Summary Data

api_instance = cfbd.GamesApi(cfbd.ApiClient(configuration))

for year in range(2015, CURRENT_SEASON + 1):
    for season_type in ['regular', 'postseason']:
        if season_type == 'postseason':
            try:
                api_response = api_instance.get_team_game_stats(year, week=1, season_type=season_type, classification=DIVISION)
                game_stats_df = pd.DataFrame()
                for game in api_response:
                    game_stats_df = pd.concat([game_stats_df, parse_teamgamestats_into_pddf(game)], ignore_index=True) 
                game_stats_df.to_sql('ncaa_game_stats_summary', sql_connection, if_exists='append', index=False)                
            except ApiException as e:
                print("Exception when calling GamesApi->get_team_game_stats: %s\n" % e)
        else:
            for week in range(1, 16):
                try:
                    api_response = api_instance.get_team_game_stats(year, week=week, season_type=season_type, classification=DIVISION)
                    game_stats_df = pd.DataFrame()
                    for game in api_response:
                        game_stats_df = pd.concat([game_stats_df, parse_teamgamestats_into_pddf(game)], ignore_index=True)
                    game_stats_df.to_sql('ncaa_game_stats_summary', sql_connection, if_exists='append', index=False)
                except ApiException as e:
                    print("Exception when calling GamesApi->get_team_game_stats: %s\n" % e)


### AP TOP 25 Data
api_instance = cfbd.RankingsApi(cfbd.ApiClient(configuration))

for year in range(2015, CURRENT_SEASON + 1):
    for season_type in ['regular', 'postseason']:
        try:
            # Historical polls and rankings
            rankings = api_instance.get_rankings(year, season_type=season_type)
            for rank in rankings:
                df_tmp = parse_week_ap25_rank_into_pddf(rank)
                df_tmp.to_sql('ncaa_rankings', sql_connection, if_exists='append', index=False)
        except ApiException as e:
            print("Exception when calling RankingsApi->get_rankings: %s\n" % e)


### Teams Info
api_instance = cfbd.TeamsApi(cfbd.ApiClient(configuration))

try:
    # Team information
    api_response = api_instance.get_teams()
except ApiException as e:
    print("Exception when calling TeamsApi->get_teams: %s\n" % e)


df = pd.DataFrame([i for i in map(cfbd.models.team.Team.to_dict, api_response)])[TEAM_INFO_COLUMNS]
df['logo1'] = df.logos.apply(lambda x: x[0] if x is not None else None)
df['logo2'] = df.logos.apply(lambda x: x[1] if x is not None and len(x) > 1 else None)
df.drop(columns='logos', inplace=True)
df.to_sql('ncaa_teams_info', sql_connection, if_exists='replace', index=False)

# load logos to ncaa logos directory
os.makedirs(LOGOS_DIRECTORY, exist_ok=True)
for i in range(df.shape[0]):
    if df.loc[i, 'logo1'] is not None:
        download_file(df.loc[i, 'logo1'], f'{LOGOS_DIRECTORY}{df.loc[i, "id"]}.png')

### Table With Ratings
query = '''
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

'''
df = pd.read_sql_query(query, sql_connection)

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
            'totalYards']:
    df[col].fillna(df[col].median(), inplace=True)

df.loc[:, 'excitement_index'].fillna(df['excitement_index'].median(), inplace=True)

df['totalTDs'] = df['rushingTDs'] + df['puntReturnTDs'] + df['passingTDs'] + df['kickReturnTDs'] + df['interceptionTDs']
df = df.drop(['rushingTDs', 'puntReturnTDs', 'passingTDs', 'kickReturnTDs', 'interceptionTDs', 'defensiveTDs', 'rushingYards', 'netPassingYards',], axis=1)

df['tds_rating'] = df['totalTDs'].apply(lambda x: min(10, max(0, x - 4)))
df['sacks_rating'] = df['sacks'].apply(lambda x: min(12, x) / 1.2)
df['interceptions_rating'] = df['interceptions'].apply(lambda x: min(5, x) / 0.5)
df['yards_rating'] = df['totalYards'].apply(lambda x: math.sqrt(min(700, max(0, x - 500))) / YARDS_DIVIDER)

df['stat_rating'] = df['tds_rating'] * 0.1\
                  + df['sacks_rating'] * 0.1\
                  + df['interceptions_rating'] * 0.1\
                  + df['yards_rating'] * 0.7

df.loc[:, 'efficiency_rating'] = df.loc[:, 'scores_sum'].apply(lambda x: math.sqrt(x) / SCORES_SUM_DIVIDER)
df.loc[:, 'overtimes_rating'] = df.loc[:, 'number_of_quarters'].apply(lambda x: 2 if x > 9 else 1 if x > 4 else 0)
df.loc[:, 'excitement_rating'] = df.loc[:, 'excitement_index'].apply(lambda x: math.log(max(x, 1), 4) / EXCIT_IND_DIVIDER if x < 10 else 10)
df.loc[:, 'score_diff_rating'] = df.loc[:, 'scores_diff'].apply(lambda x: 0 if x > 29 else (30 - x) / SCORE_DIFF_DIVIDER)
df.loc[:, 'leader_changes_rating'] = df.loc[:, 'score_changes'].apply(lambda x: 10 if x > 4 else 9 if x == 4 else 6 if x == 3 else 3 if x == 2 else 0)

df.loc[:, 'game_rating'] = (df.loc[:, 'efficiency_rating'] + df.loc[:, 'overtimes_rating']).apply(lambda x: min(x, 10)) * 0.25\
                         + df.loc[:, 'score_diff_rating'] * 0.25\
                         + df.loc[:, 'stat_rating'] * 0.25\
                         + df.loc[:, 'excitement_rating'] * 0.2\
                         + df.loc[:, 'leader_changes_rating'] * 0.05

delete_irrelevant_notes = lambda x: '' if x is None else x if x.__contains__('bowl') or x.__contains__('kickoff') or x.__contains__('championship') or x.__contains__('classic') else ''
df['notes'] = df.notes.apply(lambda x: x.lower().replace('"', '') if x is not None else None).apply(delete_irrelevant_notes)

df[GAME_RATING_COLUMNS].to_sql('ncaa_game_ratings', sql_connection, if_exists='replace', index=False)