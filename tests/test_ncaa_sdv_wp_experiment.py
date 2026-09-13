import math
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ncaa_sdv_wp_experiment import inspect_game_pbp, nfl_wp_metrics, rating_with_wp


class NcaaSportsDataverseExperimentTests(unittest.TestCase):
    def test_wp_metrics_match_nfl_aggregation(self):
        wp = pd.Series([0.05, 0.10, 0.20, 0.40])
        max_diff, shifts = nfl_wp_metrics(wp)
        expected_shifts = sum(
            (wp - wp.shift(-offset)).abs().sum() for offset in (1, 2, 3)
        )
        self.assertAlmostEqual(max_diff, 0.35)
        self.assertAlmostEqual(shifts, expected_shifts)

    def test_partial_feed_is_not_rated(self):
        pbp = pd.DataFrame(
            {
                "sequenceNumber": range(1, 61),
                "period": [1] * 20 + [2] * 20 + [3] * 20,
                "homeScore": [27] * 60,
                "awayScore": [24] * 60,
                "end.homeScore": [27] * 60,
                "end.awayScore": [24] * 60,
                "home_wp_before": [0.05] * 60,
                "gameSpread": [24.5] * 60,
                "gameSpreadAvailable": [True] * 60,
                "status_type_completed": [False] * 60,
            }
        )
        result = inspect_game_pbp(pbp, pd.Series({"home_points": 39, "away_points": 31}))
        self.assertEqual(result["pbp_status"], "source_not_completed")
        self.assertIsNone(result["new_win_prob_shifts"])

    def test_complete_feed_is_accepted(self):
        probabilities = [0.05 + index / 200 for index in range(80)]
        pbp = pd.DataFrame(
            {
                "sequenceNumber": range(1, 81),
                "period": [1] * 20 + [2] * 20 + [3] * 20 + [4] * 20,
                "homeScore": [0] * 79 + [31],
                "awayScore": [0] * 79 + [24],
                "end.homeScore": [0] * 79 + [31],
                "end.awayScore": [0] * 79 + [24],
                "home_wp_before": probabilities,
                "gameSpread": [-7.5] * 80,
                "gameSpreadAvailable": [True] * 80,
                "status_type_completed": [True] * 80,
            }
        )
        result = inspect_game_pbp(pbp, pd.Series({"home_points": 31, "away_points": 24}))
        self.assertEqual(result["pbp_status"], "complete")
        self.assertAlmostEqual(result["pregame_home_wp"], 0.05)
        self.assertIsNotNone(result["new_win_prob_shifts"])

    def test_late_replay_row_does_not_distort_wp(self):
        rows = 80
        pbp = pd.DataFrame(
            {
                "sequenceNumber": list(range(2, rows + 2)) + [1],
                "period": [1] * 20 + [2] * 20 + [3] * 20 + [4] * 20 + [1],
                "homeScore": [0] * 79 + [31, 7],
                "awayScore": [0] * 79 + [24, 0],
                "end.homeScore": [0] * 79 + [31, 7],
                "end.awayScore": [0] * 79 + [24, 0],
                "home_wp_before": [0.5] * rows + [0.999],
                "gameSpread": [-3.5] * (rows + 1),
                "gameSpreadAvailable": [True] * (rows + 1),
                "status_type_completed": [True] * (rows + 1),
            }
        )
        result = inspect_game_pbp(pbp, pd.Series({"home_points": 31, "away_points": 24}))
        self.assertEqual(result["pbp_status"], "complete")
        self.assertEqual(result["pbp_discarded_rows"], 1)
        self.assertAlmostEqual(result["new_win_chances_max_diff"], 0)

    def test_rating_replaces_only_wp_components(self):
        row = pd.Series(
            {
                "efficiency_rating": 8,
                "overtimes_rating": 0,
                "score_diff_rating": 6,
                "stat_rating": 7,
                "leader_changes_rating": 4,
                "tds_rating": 5,
            }
        )
        shifts = 4
        expected = round(
            8 * 0.25
            + min(10, math.sqrt(shifts) / (math.sqrt(40) / 10)) * 0.25
            + 6 * 0.20
            + (0.5 * 10) * 0.10
            + 7 * 0.10
            + 4 * 0.10,
            2,
        )
        self.assertEqual(rating_with_wp(row, 0.5, shifts), expected)


if __name__ == "__main__":
    unittest.main()
