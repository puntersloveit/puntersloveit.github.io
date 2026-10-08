# What is this site about?
This site contains game ratings for the two most popular American football competitions: the NFL and NCAA Football. We present no game results, stats, or game tapes - only ratings.

# Why do we need these ratings, I watch all the games live
These ratings are intended for those who, for various reasons (for example, time zones), cannot watch games live, but wish to view the most exciting game tapes after the end of the game week or during the offseason.

# How to read game rating (```GR```) values?
- ```GR < 5```, A below-average game for a neutral viewer.
- ```GR >= 5```, A typical game that may still be worth watching, especially if you care about either team.
- ```GR >= 6```, A good game.
- ```GR >= 7```, A very good game.
- ```GR >= 8```, An exceptional game and one of the highlights of the season.
- ```GR >= 9```, An extraordinarily rare, all-time game.
- ```GR = 10```, An unreachable ideal. These games do not exist.

# What factors does the rating take into account?
- Score efficiency
- Proximity of the result, including overtime
- Game stats (yards, touchdowns, sacks, interceptions)
- Surprising outcomes, twists, and turns during the game
- Number of leadership changes

# What factors does the rating NOT take into account?
- Team's power or popularity
- Players' power or popularity, including spectacular stunts from the players
- Personal bias or preference for a particular team
- Having Taylor Swift in the bleachers

Everyone must consider these factors individually. For instance, if teams you favor are playing and the rating is around ```GR 5-6``` (a typical to above-average game), you will likely enjoy watching it.

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

CFBD provides games, final scores, box-score statistics, rankings and team metadata.
When validated SportsDataverse play-by-play (PBP) is available, the two
win-probability components use its spread-aware `home_wp_before` series.
Their aggregation and weights match NFL; the probability models and the other
NCAA inputs are not identical to NFL.

### PBP and Simplified ratings

For a PBP rating, probabilities are kept in canonical chronological order:

```text
win_chances_max_diff = max(wp) - min(wp)
win_prob_shifts = sum(abs(wp[i] - wp[i+k]) for k in (1, 2, 3) for valid i)
```

The first available PBP probability is included. A separate CFBD pregame
probability is not prepended to this series. PBP must pass completion checks:
completed source flags, at least 40 canonical plays, period 4 or later, final
scores matching CFBD, an available spread and valid probabilities on every
canonical play. Missing or rejected PBP does not hide the game.

Games without accepted PBP retain the **Simplified** (`legacy`) rating. Its
WP components are proxies derived from CFBD's home pregame probability `p`,
not measured changes during the game:

```text
balance = max(0, 1 - 2 * abs(p - 0.5))
win_chances_max_diff = balance
win_prob_shifts = 40 * balance
```

A balanced pregame matchup therefore receives larger proxy contributions;
these proxies cannot capture an actual comeback or upset. If the proxy metrics
are missing, the legacy calculation fills missing WP inputs with medians from
the batch being scored. The remaining components and final weights below are
unchanged between PBP and Simplified ratings.

Each scheduled update rechecks PBP for the current season and enrolled historical
seasons with Simplified ratings, even when no new CFBD games arrive. Once valid
PBP appears, the rating and team averages are updated and the Simplified badge
is removed. Previously accepted PBP metrics survive temporary source failures.

Only per-game WP aggregates, validation state and the original legacy score are
persisted in SQLite (`ncaa_rating_sources`); raw PBP is not stored in the DB or
committed. Like the NFL updater, the NCAA updater still needs to read the remote
season Parquet to discover new or corrected data. Its local `.cache/` download
is ignored by Git and does not consume CFBD API quota.

### stat_rating
1. **Touchdowns rating:**

   ```tds_rating = min(10, totalTDs)```

2. **Sacks rating:**

   ```sacks_rating = min(12, sacks) / 1.2```

3. **Interceptions rating:**

   ```interceptions_rating = min(7, interceptions) / 0.7```

4. **Yards rating:**

   ```yards_rating = sqrt(min(650, max(0, totalYards - 350))) / YARDS_DIVIDER```
   - Where ```YARDS_DIVIDER = sqrt(650) / 10```

5. **Overall statistical rating, calculated from all previous ratings:**

   ```stat_rating = 0.3 * tds_rating + 0.1 * sacks_rating + 0.1 * interceptions_rating + 0.5 * yards_rating```

### Additional game excitement ratings
1. **Efficiency rating:**

   ```efficiency_rating = sqrt(scores_sum) / SCORES_SUM_DIVIDER```
   - Where ```SCORES_SUM_DIVIDER = sqrt(100) / 10```

2. **Overtimes rating:**

   ```
   If number_of_quarters > 4:  
     overtimes_rating = 1  
   Else:  
     overtimes_rating = 0
   ```

3. **Score difference rating:**

   ```
   If scores_diff == 0:  
     score_diff_rating = 7.5  
   Else:  
     score_diff_rating = max(-10, (20 - scores_diff) / SCORE_DIFF_DIVIDER)
   ```

   - Where ```SCORE_DIFF_DIVIDER = 19 / 10```

4. **Win probability shifts rating:**

   ```win_prob_shifts_rating = min(10, sqrt(win_prob_shifts) / WIN_PROB_SHIFTS_DIVIDER)```
   - Where ```WIN_PROB_SHIFTS_DIVIDER = sqrt(40) / 10```

5. **Maximum win chances difference rating:**

   ```win_chances_max_diff_rating = 10 * win_chances_max_diff```

6. **Leader changes rating:**

   ```leader_changes_rating = min(10, score_changes)```

> The WP formulas above apply to either accepted PBP aggregates or the Simplified
> proxies described above; equal formulas do not mean equal input quality.

### Overall game rating:
1. **First, calculate:**

   ```
   game_rating = 0.25 * min(efficiency_rating + overtimes_rating, 10)  
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

# When do game ratings update?
- NFL ratings update daily at ~6:30 and ~8:30 UTC, with an additional update at ~4:30 UTC on Monday mornings.
- NCAA ratings update daily at ~7:30 UTC, with an additional update at ~4:30 UTC on Sunday mornings.

## NCAA play-by-play pipeline and comparison

The standalone `scripts/ncaa_sdv_wp_experiment.py` comparison is quota-free and
does not modify the main database. The load/update/rebuild scripts separately
apply accepted PBP aggregates before exporting site ratings. See
[`docs/ncaa_sdv_wp_experiment.md`](docs/ncaa_sdv_wp_experiment.md) for the data
contract, completion checks, rerun behaviour and local preview instructions.

NCAA exports include `rating_source` (`pbp` or `legacy`). Game-rating pages
mark legacy ratings as “Simplified”, with a spoiler-free explanation. The badge
reflects the accepted rating source, not the latest download status. Previously
accepted PBP ratings remain unmarked during temporary source outages. Historical
seasons not enrolled in the PBP pipeline keep their legacy ratings and the badge.

The NCAA conference filter offers only FBS conferences from each season's exported game metadata,
not today's team affiliations. A conference matches either team, including
cross-conference games. Switching seasons preserves the selection only when
that conference exists in the new season; “All Years” offers the historical union.

UTC time its: -8 USA&Canada Pacific, -6 Mexico City, Guatemala City, Tegucigalpa, San José, San Salvador, -5 USA&Canada Eastern, -4 Santiago, Santo Domingo, Caracas, La Paz, -3 São Paulo, Buenos Aires, Montevideo, +1 Berlin, Madrid, Paris, Rome, +2 Kiyv, Cairo, Jerusalem, +3 Moscow, Istanbul, +4 Dubai, Tbilisi, +5 Tashkent, Karachi, Dushanbe, Yekaterinburg +6 Almaty, Dhaka, +7 Jakarta, Bangkok, Novosibirsk, +8 Shanghai, Taipei, Singapore, +9 Tokyo, Seoul, +10 Sidney, Vladivostok, +12 Auckland, Petropavlovsk-Kamchatsky

# Where do I watch game tapes?
Every man for himself.

# Special Thanks
Inspired by [wikihoops](https://wikihoops.com/about/)   
Stats from [CollegeFootballData](https://collegefootballdata.com/) (NCAA games and box scores), [SportsDataverse](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_cfb_pbp) (NCAA ESPN-derived PBP and win probabilities), and [nfl_data_py](https://github.com/cooperdff/nfl_data_py) (NFL).

# Database documentation
Database tables and relationships are documented in [DATABASE.md](DATABASE.md).
