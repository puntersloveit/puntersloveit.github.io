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

   ![tds_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{tds_rating}=\min(10,\ \text{touchdown}))

2. **Sacks rating:**

   ![sacks_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{sacks_rating}=\dfrac{\min(12,\ \text{sack})}{1.2})

3. **Interceptions rating:**

   ![interceptions_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{interceptions_rating}=\dfrac{\min(7,\ \text{interception})}{0.7})

4. **Yards rating:**

   ![yards_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{yards_rating}=\dfrac{\sqrt{\min\left(650,\ \max\left(0,\ \text{yards} - 350\right)\right)}}{\text{YARDS\_DIVIDER}})

   Where  
   ![YARDS_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{YARDS\_DIVIDER}=\dfrac{\sqrt{650}}{10})

5. **Overall statistical rating, calculated from all previous ratings:**

   ![stat_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{stat_rating}=0.3\times\text{tds_rating}+0.1\times\text{sacks_rating}+0.1\times\text{interceptions_rating}+0.5\times\text{yards_rating})

### Separately, we calculate several ratings reflecting the game's excitement
1. **Efficiency rating:**

   ![efficiency_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{efficiency_rating}=\dfrac{\sqrt{\text{scores\_sum}}}{\text{SCORES\_SUM\_DIVIDER}})

   Where  
   ![SCORES_SUM_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{SCORES\_SUM\_DIVIDER}=\dfrac{\sqrt{100}}{10})

2. **Score difference rating:**

   ![score_diff_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{score_diff_rating}=\begin{cases}7.5,\text{if}\ \text{scores\_diff}=0\\\max\left(-10,\ \dfrac{20-\text{scores\_diff}}{\text{SCORE\_DIFF\_DIVIDER}}\right),\text{otherwise}\end{cases})

   Where  
   ![SCORE_DIFF_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{SCORE\_DIFF\_DIVIDER}=\dfrac{19}{10})

3. **Win probability shifts rating:**

   ![win_prob_shifts_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{win_prob_shifts_rating}=\min\left(10,\ \dfrac{\sqrt{\text{win\_prob\_shifts}}}{\text{WIN\_PROB\_SHIFTS\_DIVIDER}}\right))

   Where  
   ![WIN_PROB_SHIFTS_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{WIN\_PROB\_SHIFTS\_DIVIDER}=\dfrac{\sqrt{40}}{10})

4. **Maximum win chances difference rating:**

   ![win_chances_max_diff_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{win_chances_max_diff_rating}=10\times\text{win_chances_max_diff})

5. **Leader changes rating:**

   ![leader_changes_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{leader_changes_rating}=\min(10,\ \text{leader_changes}))

### Overall game rating
1. **First, calculate**

   ![game_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{game_rating}=0.25\times\min\left(\text{efficiency_rating}+\text{overtime},\ 10\right)+0.25\times\text{win_prob_shifts_rating}+0.2\times\text{score_diff_rating}+0.1\times\text{win_chances_max_diff_rating}+0.1\times\text{stat_rating}+0.1\times\text{leader_changes_rating})

2. **Adjustment of the overall game rating:**

   If  
   ![tds_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{tds_rating}=0),  
   then:

   ![game_rating_adjusted](https://latex.codecogs.com/png.latex?\dpi{110}\text{game_rating}=\max(0,\ \text{game_rating}-2))

## NCAAF
### stat_rating
1. **Touchdowns rating:**

   ![tds_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{tds_rating}=\min(10,\ \max(0,\ \text{totalTDs}-4)))

2. **Sacks rating:**

   ![sacks_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{sacks_rating}=\dfrac{\min(12,\ \text{sacks})}{1.2})

3. **Interceptions rating:**

   ![interceptions_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{interceptions_rating}=\dfrac{\min(5,\ \text{interceptions})}{0.5})

4. **Yards rating:**

   ![yards_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{yards_rating}=\dfrac{\sqrt{\min(700,\ \max(0,\ \text{totalYards}-500))}}{\text{YARDS_DIVIDER}})

   Where  
   ![YARDS_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{YARDS_DIVIDER}=\dfrac{\sqrt{700}}{10})

5. **Overall statistical rating, calculated from all previous ratings:**

   ![stat_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{stat_rating}=0.1\times\text{tds_rating}+0.1\times\text{sacks_rating}+0.1\times\text{interceptions_rating}+0.7\times\text{yards_rating})

### Additional game excitement ratings
1. **Efficiency rating:**

   ![efficiency_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{efficiency_rating}=\dfrac{\sqrt{\text{scores_sum}}}{\text{SCORES_SUM_DIVIDER}})

   Where  
   ![SCORES_SUM_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{SCORES_SUM_DIVIDER}=\dfrac{\sqrt{144}}{10})

2. **Overtimes rating:**

   ![overtimes_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{overtimes_rating}=\begin{cases}2,&\text{if}\ \text{number_of_quarters}>9\\1,&\text{if}\ \text{number_of_quarters}>4\\0,&\text{otherwise}\end{cases})

3. **Excitement rating:**

   ![excitement_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{excitement_rating}=\begin{cases}\dfrac{\log(\max(\text{excitement_index},1),4)}{\text{EXCIT_IND_DIVIDER}},&\text{if}\ \text{excitement_index}<10\\10,&\text{otherwise}\end{cases})

   Where  
   ![EXCIT_IND_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{EXCIT_IND_DIVIDER}=\dfrac{\log(10,4)}{10})

4. **Score difference rating:**

   ![score_diff_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{score_diff_rating}=\begin{cases}0,&\text{if}\ \text{scores_diff}>29\\\dfrac{30-\text{scores_diff}}{\text{SCORE_DIFF_DIVIDER}},&\text{otherwise}\end{cases})

   Where  
   ![SCORE_DIFF_DIVIDER](https://latex.codecogs.com/png.latex?\dpi{110}\text{SCORE_DIFF_DIVIDER}=\dfrac{29}{10})

5. **Leader changes rating:**

   ![leader_changes_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{leader_changes_rating}=\begin{cases}10,&\text{if}\ \text{score_changes}>4\\9,&\text{if}\ \text{score_changes}=4\\6,&\text{if}\ \text{score_changes}=3\\3,&\text{if}\ \text{score_changes}=2\\0,&\text{otherwise}\end{cases})

### Overall game rating

   ![game_rating](https://latex.codecogs.com/png.latex?\dpi{110}\text{game_rating}=0.25\times\min\left(\text{efficiency_rating}+\text{overtimes_rating},10\right)+0.25\times\text{score_diff_rating}+0.25\times\text{stat_rating}+0.2\times\text{excitement_rating}+0.05\times\text{leader_changes_rating})

# When do game ratings update?
- NFL ratings update daily at ~6:30 and ~8:30 UTC, with an additional update at ~4:30 UTC on Monday mornings.
- NCAA ratings update daily at ~7:30 UTC, with an additional update at ~4:30 UTC on Sunday mornings.

UTC time its: -8 USA&Canada Pacific, -6 Mexico City, Guatemala City, Tegucigalpa, San José, San Salvador, -5 USA&Canada Eastern, -4 Santiago, Santo Domingo, Caracas, La Paz, -3 São Paulo, Buenos Aires, Montevideo, +1 Berlin, Madrid, Paris, Rome, +2 Kiyv, Cairo, Jerusalem, +3 Moscow, Istanbul, +4 Dubai, Tbilisi, +5 Tashkent, Karachi, Dushanbe, Yekaterinburg +6 Almaty, Dhaka, +7 Jakarta, Bangkok, Novosibirsk, +8 Shanghai, Taipei, Singapore, +9 Tokyo, Seoul, +10 Sidney, Vladivostok, +12 Auckland, Petropavlovsk-Kamchatsky

# Where do I watch game tapes?
Every man for himself.

# Special Thanks
Inspired by [wikihoops](https://wikihoops.com/about/)   
Stats from [CollegeFootballData](https://collegefootballdata.com/) and [nfl_data_py](https://github.com/cooperdff/nfl_data_py)   