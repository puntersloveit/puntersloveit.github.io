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

The formulas below show normalization explicitly: divide by a reference value,
then multiply by `10` to express the result on the rating scale. For example,
`10 * sqrt(scores_sum) / sqrt(100)` gives 10 points for 100 combined points
and 5 points for 25 combined points. Here, `100` is the scoring benchmark;
`10` sets the rating scale. The square root gives diminishing returns as
scoring increases.

`min` caps a value, `max` sets a floor, and `sqrt` means square root.
Game statistics and scores are combined across both teams: `scores_sum` is
the total points scored, and `scores_diff` is the absolute final score margin.
These expressions are algebraically equivalent to the pipeline calculations.

## What do the win-probability metrics measure?

Win probability (WP) is a model's estimate of the home team's chance of winning
at a particular moment in the game. It uses a 0–1 scale: `0.2` means 20%.
NFL uses `vegas_home_wp`; NCAA games with accepted PBP use `home_wp_before`.
Both metrics below follow the same team's probability throughout the game.

### `win_chances_max_diff`: how wide was the swing?

This is the distance between the highest and lowest recorded win probability:

```text
win_chances_max_diff = max(wp) - min(wp)
```

If the home team's chances range from 20% to 80%, the metric is
`0.8 - 0.2 = 0.6` (60 percentage points), and its rating component is
`10 * 0.6 = 6`. It captures the size of the probability range, regardless of
how often the game moves between those extremes. A single sustained comeback
can create a large range; repeated reversals are not required. The range alone
does not tell us which team eventually won.

### `win_prob_shifts`: how much did the chances move throughout the game?

This adds up absolute probability changes over short stretches. Each recorded
probability is compared with the next one, the one two entries ahead and the
one three entries ahead, wherever those entries exist:

```text
win_prob_shifts = sum(abs(wp[i] - wp[i+k]) for k in (1, 2, 3) for valid i)
```

For a short example, take `20% → 70% → 40% → 80%`:

| Distance between entries | Absolute changes | Sum |
| --- | --- | --- |
| 1 entry | 0.50 + 0.30 + 0.40 | 1.20 |
| 2 entries | 0.20 + 0.10 | 0.30 |
| 3 entries | 0.60 | 0.60 |
| **Total `win_prob_shifts`** | | **2.10** |

Changes in either direction add to the total. The overlapping comparisons
capture movement across several nearby plays, rather than only between
adjacent entries. This is an accumulated movement measure, not a probability
or a count of lead changes, so it can exceed 1. The reference value `40` in
the rating formula is a total movement benchmark, not 40% or 40 reversals.
Longer games also offer more opportunities to accumulate movement.

Together, the two components describe the **size of the probability range**
and the **amount of short-term movement**. A steady, one-sided game usually
has less movement than a game with repeated swings in the estimated chances.

For NCAA **Simplified** ratings, actual in-game WP is unavailable: these same
field names hold pregame-balance proxies instead. The examples above describe
the PBP metrics; see the NCAA section below for the proxy calculation.

## NFL
### stat_rating
1. **Touchdowns rating:**

   ```tds_rating = min(10, touchdown)```

2. **Sacks rating:**

   ```sacks_rating = 10 * min(sack, 12) / 12```

   Twelve combined sacks reach the cap of 10.

3. **Interceptions rating:**

   ```interceptions_rating = 10 * min(interception, 7) / 7```

   Seven combined interceptions reach the cap of 10.

4. **Yards rating:**

   ```yards_rating = 10 * sqrt(min(650, max(0, yards - 350))) / sqrt(650)```

   Yards up to 350 contribute zero; 1,000 combined yards reach the cap of 10.
   The benchmark `650` is the additional yardage above the 350-yard floor.

5. **Overall statistical rating, calculated from all previous ratings:**

   ```stat_rating = 0.3 * tds_rating + 0.1 * sacks_rating + 0.1 * interceptions_rating + 0.5 * yards_rating```

### Additional game excitement ratings
1. **Efficiency rating:**

   ```efficiency_rating = 10 * sqrt(scores_sum) / sqrt(100)```

   The benchmark is 100 combined points for a component value of 10.
   The overall formula below caps this component, including the overtime bonus, at 10.

2. **Score difference rating:**

   ```
   If scores_diff == 0:  
     score_diff_rating = 7.5  
   Else:  
     score_diff_rating = max(-10, 10 * (20 - scores_diff) / 19)
   ```

   A one-point margin gives 10; a 20-point margin gives 0. Wider margins
   produce a penalty, capped at -10. A tie receives the special value 7.5.

3. **Win probability movement rating (`win_prob_shifts`):**

   ```win_prob_shifts_rating = 10 * min(1, sqrt(win_prob_shifts) / sqrt(40))```

   The benchmark is 40 units of accumulated probability movement for the cap of 10.
   Probabilities use the 0–1 scale, so a change from 0.2 to 0.7 contributes 0.5.

4. **Win probability range rating (`win_chances_max_diff`):**

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

   ```sacks_rating = 10 * min(sacks, 12) / 12```

   Twelve combined sacks reach the cap of 10.

3. **Interceptions rating:**

   ```interceptions_rating = 10 * min(interceptions, 7) / 7```

   Seven combined interceptions reach the cap of 10.

4. **Yards rating:**

   ```yards_rating = 10 * sqrt(min(650, max(0, totalYards - 350))) / sqrt(650)```

   Yards up to 350 contribute zero; 1,000 combined yards reach the cap of 10.
   The benchmark `650` is the additional yardage above the 350-yard floor.

5. **Overall statistical rating, calculated from all previous ratings:**

   ```stat_rating = 0.3 * tds_rating + 0.1 * sacks_rating + 0.1 * interceptions_rating + 0.5 * yards_rating```

### Additional game excitement ratings
1. **Efficiency rating:**

   ```efficiency_rating = 10 * sqrt(scores_sum) / sqrt(100)```

   The benchmark is 100 combined points for a component value of 10.
   The overall formula below caps this component, including the overtime bonus, at 10.

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
     score_diff_rating = max(-10, 10 * (20 - scores_diff) / 19)
   ```

   A one-point margin gives 10; a 20-point margin gives 0. Wider margins
   produce a penalty, capped at -10. A tie receives the special value 7.5.

4. **Win probability movement rating (`win_prob_shifts`):**

   ```win_prob_shifts_rating = 10 * min(1, sqrt(win_prob_shifts) / sqrt(40))```

   The benchmark is 40 units of accumulated probability movement for the cap of 10.
   Probabilities use the 0–1 scale, so a change from 0.2 to 0.7 contributes 0.5.

5. **Win probability range rating (`win_chances_max_diff`):**

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
