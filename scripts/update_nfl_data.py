import math
import sqlite3
import datetime
import yaml
import nfl_data_py as nfl
import pandas as pd
import numpy as np

from functions import saturate_hex_color

current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
CURRENT_SEASON = current_year if current_month > 7 else current_year - 1

sql_connection = sqlite3.connect('_data/puntersloveit.db')
sql_cursor = sql_connection.cursor()

PBP_COLUMNS = [
 'game_id',
 'season',
 'season_type',
 'week',
 'away_team',
 'home_team',
 'total_home_score',
 'total_away_score',
 'qtr',
 'touchdown',
 'fumble_lost',
 'sack',
 'interception',
 'yards_gained',
 'vegas_home_wp',
 'score_differential',
 'score_differential_post'
 ]

YARDS_DIVIDER = math.sqrt(650) / 10
SCORES_SUM_DIVIDER = math.sqrt(100) / 10
SCORE_DIFF_DIVIDER = 19 / 10
WIN_PROB_SHIFTS_DIVIDER = math.sqrt(40) / 10

SATURATION_AMOUNT = 0.5
LIGHTENING_AMOUNT = 0.3

# Play-by-Play Data
game_ids_from_db = set(
    pd.read_sql_query(f'SELECT game_id FROM nfl_game_ratings WHERE season == {CURRENT_SEASON}', sql_connection).values.flatten()
)

pbp_data = nfl.import_pbp_data([CURRENT_SEASON], PBP_COLUMNS).query('game_id not in @game_ids_from_db')
pbp_data.query('~(score_differential.isna() | score_differential_post.isna())', inplace=True)
pbp_data['leader_changes'] = np.sign(pbp_data.score_differential_post) != np.sign(pbp_data.score_differential)

game_stats_summary_df = pbp_data.groupby(['game_id', 'season', 'season_type', 'week',  'away_team', 'home_team']).agg(
    total_home_score=pd.NamedAgg(column='total_home_score', aggfunc='max'),
    total_away_score=pd.NamedAgg(column='total_away_score', aggfunc='max'),
    qtr=pd.NamedAgg(column='qtr', aggfunc='max'),
    touchdown=pd.NamedAgg(column='touchdown', aggfunc='sum'),
    fumble_lost=pd.NamedAgg(column='fumble_lost', aggfunc='sum'),
    sack=pd.NamedAgg(column='sack', aggfunc='sum'),
    interception=pd.NamedAgg(column='interception', aggfunc='sum'),
    yards=pd.NamedAgg(column='yards_gained', aggfunc='sum'),
    leader_changes=pd.NamedAgg(column='leader_changes', aggfunc='sum'),
    win_chances_max_diff=pd.NamedAgg(column='vegas_home_wp', aggfunc=lambda x: x.max() - x.min()),
    win_prob_shifts=pd.NamedAgg(column='vegas_home_wp', aggfunc=lambda x: (x - x.shift(-1)).abs().sum() + (x - x.shift(-2)).abs().sum() + (x - x.shift(-3)).abs().sum())
).reset_index()
game_stats_summary_df['scores_sum'] = game_stats_summary_df['total_home_score'] + game_stats_summary_df['total_away_score']
game_stats_summary_df['scores_diff'] = (game_stats_summary_df['total_home_score'] - game_stats_summary_df['total_away_score']).abs()
game_stats_summary_df['overtime'] = game_stats_summary_df['qtr'].apply(lambda x: 1 if x == 5 else 0)
game_stats_summary_df.to_sql('nfl_game_stats_summary', sql_connection, if_exists='append', index=False)

# Table With Ratings
current_ratings_ids = tuple(pd.read_sql_query(f'select game_id from nfl_game_ratings', sql_connection).values.flatten())
new_ids_from_games_table = set(pd.read_sql_query(
                                    f'select game_id from nfl_game_stats_summary where game_id not in {current_ratings_ids}', 
                                    sql_connection
                                                ).values.flatten()
                              )
new_ids_from_games_table_tuple = str(tuple(new_ids_from_games_table))\
    .replace(",", "") if len(new_ids_from_games_table) == 1 else tuple(new_ids_from_games_table)

query = '''
SELECT
    game_id,
    season,
    season_type,
    week,
    home_team_info.team_name as home_team, 
    home_team_info.team_color as home_color,
    away_team_info.team_name as away_team,
    away_team_info.team_color as away_color,
    total_home_score,
    total_away_score,
    qtr,
    touchdown,
    fumble_lost,
    sack,
    interception,
    yards,
    leader_changes,
    win_chances_max_diff,
    win_prob_shifts,
    scores_sum,
    scores_diff,
    overtime
FROM nfl_game_stats_summary AS games
LEFT JOIN nfl_teams_info AS home_team_info
    ON games.home_team = home_team_info.team_abbr
LEFT JOIN nfl_teams_info AS away_team_info
    ON games.away_team = away_team_info.team_abbr

WHERE game_id in {new_ids_from_games_table_tuple}

'''
rating_df = pd.read_sql_query(query, sql_connection)

rating_df['tds_rating'] = rating_df['touchdown'].apply(lambda x: min(10, x))
rating_df['sacks_rating'] = rating_df['sack'].apply(lambda x: min(12, x) / 1.2)
rating_df['interceptions_rating'] = rating_df['interception'].apply(lambda x: min(7, x) / 0.7)
rating_df['yards_rating'] = rating_df['yards'].apply(lambda x: math.sqrt(min(650, max(0, x - 350))) / YARDS_DIVIDER)

rating_df['stat_rating'] = rating_df['tds_rating'] * 0.3\
                  + rating_df['sacks_rating'] * 0.1\
                  + rating_df['interceptions_rating'] * 0.1\
                  + rating_df['yards_rating'] * 0.5

rating_df.loc[:, 'efficiency_rating'] = rating_df.loc[:, 'scores_sum']\
    .apply(lambda x: math.sqrt(x) / SCORES_SUM_DIVIDER)
rating_df.loc[:, 'score_diff_rating'] = rating_df.loc[:, 'scores_diff']\
    .apply(lambda x: 7.5 if x == 0 else max(-10, (20 - x) / SCORE_DIFF_DIVIDER))
rating_df.loc[:, 'win_prob_shifts_rating'] = rating_df.loc[:, 'win_prob_shifts']\
    .apply(lambda x: min(10, math.sqrt(x) / WIN_PROB_SHIFTS_DIVIDER))
rating_df.loc[:, 'win_chances_max_diff_rating'] = rating_df.loc[:, 'win_chances_max_diff']\
    .apply(lambda x: x * 10)
rating_df.loc[:, 'leader_changes_rating'] = rating_df.loc[:, 'leader_changes']\
    .apply(lambda x: min(10, x))

rating_df.loc[:, 'game_rating'] = (rating_df.loc[:, 'efficiency_rating'] + rating_df.loc[:, 'overtime']).apply(lambda x: min(x, 10)) * 0.25\
                         + rating_df.loc[:, 'win_prob_shifts_rating'] * 0.25\
                         + rating_df.loc[:, 'score_diff_rating'] * 0.20\
                         + rating_df.loc[:, 'win_chances_max_diff_rating'] * 0.10\
                         + rating_df.loc[:, 'stat_rating'] * 0.10\
                         + rating_df.loc[:, 'leader_changes_rating'] * 0.10
rating_df.loc[:, 'game_rating'] = rating_df.loc[:, ['game_rating', 'tds_rating']]\
    .apply(lambda x: max(0, x['game_rating'] - 2) if x['tds_rating'] == 0 else x['game_rating'], axis=1).round(2)

rating_df['week'] = rating_df['week'].astype(str)
rating_df.loc[rating_df.season_type == 'POST', 'week'] = 'Playoff'
rating_df['away_color'] = rating_df['away_color'].apply(lambda x: saturate_hex_color(x, SATURATION_AMOUNT, LIGHTENING_AMOUNT))
rating_df['home_color'] = rating_df['home_color'].apply(lambda x: saturate_hex_color(x, SATURATION_AMOUNT, LIGHTENING_AMOUNT))

rating_df.to_sql('nfl_game_ratings', sql_connection, if_exists='append', index=False)

# Data for site
rating_df = pd.read_sql_query('select * from nfl_game_ratings', sql_connection)

rating_df[['away_color', 
           'home_color', 
           'season', 
           'week', 
           'away_team',
           'home_team', 
           'game_rating']]\
    .sort_values('game_rating', ascending=False)\
        .to_csv('_data/nfl_game_ratings.csv', index=False)

unique_seasons = []
for y in range(rating_df.season.max(), rating_df.season.min()-1, -1):
    weeks = rating_df.query(f'season == {y}').week.unique().tolist()
    if y == CURRENT_SEASON:
        weeks = weeks[::-1]
    unique_seasons.append(
    {
        'season': y,
        'weeks': weeks + ['All']
    }       
    )
with open('_data/nfl_unique_seasons.yml', 'w') as file:
    yaml.dump(unique_seasons, file)
