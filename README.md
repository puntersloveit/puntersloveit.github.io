# What is this site about?
This site contains game ratings for the two most popular American football competitions: the NFL and NCAA Football. We present no game results, stats, or game tapes - only ratings.

# Why do we need these ratings, I watch all the games live
These ratings are intended for those who, for various reasons (for example, time zones), cannot watch games live, but wish to view the most exciting game tapes after the end of the game week or during the offseason.

# How to read game rating (```GR```) values?
- ```GR > 5.5```, The game is slightly above average.
- ```GR > 6.5```, 30% of the best games.
- ```GR > 7.5```, 10% of the best games. These games are in the top 100 in NCAAF and top 30 in the NFL for the season.
- ```GR > 7.8```, 5% of the best games. These games are in the top 50 in NCAAF and top 10 in the NFL for the season.
- ```GR > 8.4```, 1% of the best games. These games are in the top 10 in NCAAF and top 3 in the NFL for the season.
- ```GR > 9```, Represents an incredible game. These games come around once every few years.
- ```GR = 10```, An unreachable ideal. These games do not exist.

# What factors does the rating take into account?
- Score efficiency
- Proximity of the result, including overtime
- Game stats (yards, touchdowns, fumbles, sacks, interceptions)
- Surprising outcomes, twists, and turns during the game
- Number of leadership changes

# What factors does the rating NOT take into account?
- Team's power or popularity
- Players' power or popularity, including spectacular stunts from the players
- Personal bias or preference for a particular team
- Having Taylor Swift in the bleachers

Everyone must consider these factors individually. For instance, if teams you favor are playing and the rating shows a ```GR > 5``` (indicating the game is above average), you will likely enjoy watching this game.

# Game Rating Formulas
## NFL
### stat_rating
1. **Touchdowns rating:**

   ```tds_rating = min(10, touchdown)```

2. **Sacks rating:**

   ```sacks_rating = min(12, sack) / 1.2```

3. **Interceptions rating:**

   ```interceptions_rating = min(7, interception) / 0.7```

4. **Yards rating:**

   ```yards_rating = sqrt(min(650, max(0, yards - 350))) / YARDS_DIVIDER```
   - Where ```YARDS_DIVIDER = sqrt(650) / 10```

5. **Overall statistical rating, calculated from all previous ratings:**

   ```stat_rating = 0.3 * tds_rating + 0.1 * sacks_rating + 0.1 * interceptions_rating + 0.5 * yards_rating```

### Additional game excitement ratings
1. **Efficiency rating:**

   ```efficiency_rating = sqrt(scores_sum) / SCORES_SUM_DIVIDER```
   - Where ```SCORES_SUM_DIVIDER = sqrt(100) / 10```

2. **Score difference rating:**

   ```
   If scores_diff == 0:  
     score_diff_rating = 7.5  
   Else:  
     score_diff_rating = max(-10, (20 - scores_diff) / SCORE_DIFF_DIVIDER)
   ```
   - Where ```SCORE_DIFF_DIVIDER = 19 / 10```

3. **Win probability shifts rating:**

   ```win_prob_shifts_rating = min(10, sqrt(win_prob_shifts) / WIN_PROB_SHIFTS_DIVIDER)```
   - Where ```WIN_PROB_SHIFTS_DIVIDER = sqrt(40) / 10```

4. **Maximum win chances difference rating:**

   ```win_chances_max_diff_rating = 10 * win_chances_max_diff```

5. **Leader changes rating:**

   ```leader_changes_rating = min(10, leader_changes)```

### Overall game rating:
1. **First, calculate:**

   ```
   game_rating = 0.25 * min(efficiency_rating + overtime, 10)  
               + 0.25 * win_prob_shifts_rating  
               + 0.20 * score_diff_rating  
               + 0.10 * win_chances_max_diff_rating  
               + 0.10 * stat_rating  
               + 0.10 * leader_changes_rating
   ```
2. **Adjustment of the overall game rating:**

   ```
   If tds_rating == 0:  
     game_rating = max(0, game_rating - 2)
   ```


## NCAAF
### stat_rating
1. **Touchdowns rating:**

   ```tds_rating = min(10, max(0, totalTDs - 4))```

2. **Sacks rating:**

   ```sacks_rating = min(12, sacks) / 1.2```

3. **Interceptions rating:**

   ```interceptions_rating = min(5, interceptions) / 0.5```

4. **Yards rating:**

   ```yards_rating = sqrt(min(700, max(0, totalYards - 500))) / YARDS_DIVIDER```
   - Where ```YARDS_DIVIDER = sqrt(700) / 10```

5. **Overall statistical rating, calculated from all previous ratings:**

   ```stat_rating = 0.1 * tds_rating + 0.1 * sacks_rating + 0.1 * interceptions_rating + 0.7 * yards_rating```

### Additional game excitement ratings
1. **Efficiency rating:**

   ```efficiency_rating = sqrt(scores_sum) / SCORES_SUM_DIVIDER```
   - Where ```SCORES_SUM_DIVIDER = sqrt(144) / 10```

2. **Overtimes rating:**

   ```
   If number_of_quarters > 9:  
     overtimes_rating = 2  
   Else if number_of_quarters > 4:  
     overtimes_rating = 1  
   Else:  
     overtimes_rating = 0
   ```

3. **Excitement rating:**

   ```
   If excitement_index < 10:  
     excitement_rating = log(max(excitement_index, 1), 4) / EXCIT_IND_DIVIDER  
   Else:  
     excitement_rating = 10
   ```

   - Where ```EXCIT_IND_DIVIDER = log(10, 4) / 10```

4. **Score difference rating:**

   ```
   If scores_diff > 29:  
     score_diff_rating = 0  
   Else:  
     score_diff_rating = (30 - scores_diff) / SCORE_DIFF_DIVIDER
   ```

   - Where ```SCORE_DIFF_DIVIDER = 29 / 10```

5. **Leader changes rating:**

   ```
   If score_changes > 4:  
     leader_changes_rating = 10  
   Else if score_changes == 4:  
     leader_changes_rating = 9  
   Else if score_changes == 3:  
     leader_changes_rating = 6  
   Else if score_changes == 2:  
     leader_changes_rating = 3  
   Else:  
     leader_changes_rating = 0
   ```

### Overall game rating:

   ```
   game_rating = 0.25 * min(efficiency_rating + overtimes_rating, 10)  
               + 0.25 * score_diff_rating  
               + 0.25 * stat_rating  
               + 0.20 * excitement_rating  
               + 0.05 * leader_changes_rating
   ```

# When do game ratings update?
- NFL ratings update daily at ~6:30 and ~8:30 UTC, with an additional update at ~4:30 UTC on Monday mornings.
- NCAA ratings update daily at ~7:30 UTC, with an additional update at ~4:30 UTC on Sunday mornings.

UTC time its: -8 USA&Canada Pacific, -6 Mexico City, Guatemala City, Tegucigalpa, San José, San Salvador, -5 USA&Canada Eastern, -4 Santiago, Santo Domingo, Caracas, La Paz, -3 São Paulo, Buenos Aires, Montevideo, +1 Berlin, Madrid, Paris, Rome, +2 Kiyv, Cairo, Jerusalem, +3 Moscow, Istanbul, +4 Dubai, Tbilisi, +5 Tashkent, Karachi, Dushanbe, Yekaterinburg +6 Almaty, Dhaka, +7 Jakarta, Bangkok, Novosibirsk, +8 Shanghai, Taipei, Singapore, +9 Tokyo, Seoul, +10 Sidney, Vladivostok, +12 Auckland, Petropavlovsk-Kamchatsky

# Where do I watch game tapes?
Every man for himself.

# Special Thanks
Inspired by [wikihoops](https://wikihoops.com/about/)   
Stats from [CollegeFootballData](https://collegefootballdata.com/) and [nfl_data_py](https://github.com/cooperdff/nfl_data_py)   