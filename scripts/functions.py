import cfbd
import itertools
import requests
import pandas as pd
import colorsys

def saturate_hex_color(hex_color, saturation_amount, lightening_amount):
    """
    Convert a hexadecimal color to a saturated version of the color.

    Args:
        hex_color (str): The hexadecimal color code, with or without the '#' symbol.
        saturation_amount (float): The amount by which to decrease the saturation of the color.
        lightening_amount (float): The amount by which to increase the lightness of the color.

    Returns:
        str: The saturated hexadecimal color code.
    """
    # Remove the '#' symbol if present
    if hex_color is None:
        return '#FFFFFF'
    else:
        hex_color = hex_color.lstrip('#')

    # Convert hexadecimal color to RGB
    rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Convert RGB to HSL
    hls_color = colorsys.rgb_to_hls(rgb_color[0] / 255, rgb_color[1] / 255, rgb_color[2] / 255)

    # Increase the saturation of the HSL color
    saturated_hls_color = (hls_color[0], max(0.0, hls_color[1] + lightening_amount), max(0.0, hls_color[2] - saturation_amount))

    # Convert HSL back to RGB
    saturated_rgb_color = tuple(round(c * 255) for c in colorsys.hls_to_rgb(*saturated_hls_color))

    # Convert RGB to hexadecimal
    saturated_hex_color = '#{:02x}{:02x}{:02x}'.format(*saturated_rgb_color)

    return saturated_hex_color

def count_number_of_quarters(line_scores: list) -> int:
    return len(line_scores)

def count_score_changes(compared_scores: list) -> int:
    """
    Count the number of score changes in a list of compared scores.

    Args:
        compared_scores (list): List of scores to compare, where -1 means its a tie, 1 - home team leads, 0 - away team leads

    Returns:
        int: Number of score changes.
    """
    count = 0
    prev = None

    for num in compared_scores:
        # If it's the first score and it's -1, skip it
        if prev is None and num == -1:
            pass
        # If it's the first score and it's not -1, count it as a change
        elif prev is None and num != -1:
            count += 1
        # If it's not the first score and it's different from the previous score, count it as a change
        elif prev is not None and num != prev:
            count += 1
        prev = num

    return count

def compare_scores(scores: pd.core.series.Series) -> list:

    '''
    Compare home and away scores

    Parameters
    ----------
    scores : pd.core.series.Series, its a row of a DataFrame[['home_line_scores', 'away_line_scores']]

    Returns
    -------
    list of {-1, 0, 1}, where -1 means scores are equal, 0 means away team leading, 1 means home team leading
    
    '''

    home_line_scores = scores['home_line_scores']
    away_line_scores = scores['away_line_scores']

    # calculate accumulative scores
    home_line_scores_accumulative = list(itertools.accumulate(home_line_scores))
    away_line_scores_accumulative = list(itertools.accumulate(away_line_scores))

    compared_scores = [1 if h > a else 0 if h < a else -1 for h, a in zip(home_line_scores_accumulative, away_line_scores_accumulative)]

    return compared_scores
  
def parse_teamgamestats_into_pddf(game: cfbd.models.team_game.TeamGame) -> pd.DataFrame:
    """
    Parses a cfbd.models.team_game.TeamGame object into a pandas DataFrame.

    Args:
        game (cfbd.models.team_game.TeamGame): The team game object to parse.

    Returns:
        pd.DataFrame: The parsed game statistics as a DataFrame.
    """

    # Initialize variables
    id = game.id
    rushingTDs = 0
    puntReturnTDs = 0
    passingTDs = 0
    kickReturnTDs = 0
    interceptionTDs = 0
    totalFumbles = 0
    defensiveTDs = 0
    sacks = 0
    interceptions = 0
    rushingYards = 0
    netPassingYards = 0
    totalYards = 0

    # Create an empty DataFrame with the required columns
    game_stats_df = pd.DataFrame(columns=['id', 
                                          'rushingTDs', 
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
                                          'totalYards']
                                )

    # Iterate over each team in the game
    for team in game.teams:
        # Iterate over each stat in the team's stats
        for stat in team.stats:
            # Update the corresponding variable based on the stat's category
            if stat.category == 'rushingTDs':
                rushingTDs += float(stat.stat)
            elif stat.category == 'puntReturnTDs':
                puntReturnTDs += float(stat.stat)
            elif stat.category == 'passingTDs':
                passingTDs += float(stat.stat)
            elif stat.category == 'kickReturnTDs':
                kickReturnTDs += float(stat.stat)
            elif stat.category == 'interceptionTDs':
                interceptionTDs += float(stat.stat)
            elif stat.category == 'totalFumbles':
                totalFumbles += float(stat.stat)
            elif stat.category == 'defensiveTDs':
                defensiveTDs += float(stat.stat)
            elif stat.category == 'sacks':
                sacks += float(stat.stat)
            elif stat.category == 'interceptions':
                interceptions += float(stat.stat)
            elif stat.category == 'rushingYards':
                rushingYards += float(stat.stat)
            elif stat.category == 'netPassingYards':
                netPassingYards += float(stat.stat)
            elif stat.category == 'totalYards':
                totalYards += float(stat.stat)

    # Add the final row of data to the DataFrame
    game_stats_df.loc[0] = [id, rushingTDs, puntReturnTDs, passingTDs, kickReturnTDs, interceptionTDs, totalFumbles, defensiveTDs, sacks, interceptions, rushingYards, netPassingYards, totalYards]

    # Convert the 'id' column to integer type
    game_stats_df['id'] = game_stats_df.loc[:, 'id'].astype(int)

    # Return the parsed game statistics DataFrame
    return game_stats_df

def parse_week_ap25_rank_into_pddf(week_rankings: cfbd.models.ranking_week.RankingWeek) -> pd.DataFrame:
    """
    Parses the AP Top 25 rankings from a given RankingWeek object and returns a pandas DataFrame.

    Args:
        week_rankings: The week_rankings object containing the rankings.

    Returns:
        df_ranks: A pandas DataFrame containing the parsed rankings.
    """
    for poll in week_rankings.polls:
        if poll.poll == 'AP Top 25':
            # Create a DataFrame from the ranks and schools in the poll
            df_ranks = pd.DataFrame([i for i in map(cfbd.Game.to_dict, poll.ranks)])[['rank', 'school']]
            
            # Add additional columns to the DataFrame
            df_ranks['season'] = week_rankings.season
            df_ranks['week'] = week_rankings.week
            df_ranks['season_type'] = week_rankings.season_type
        else:
            pass
    return df_ranks

def download_file(url, file_path):
    """
    Downloads a file from the given URL and saves it to the specified file path.

    Args:
        url (str): The URL from which to download the file.
        file_path (str): The path where the downloaded file should be saved.
    """
    with requests.get(url, stream=True) as r:
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
