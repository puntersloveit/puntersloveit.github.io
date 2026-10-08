import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ncaa_pbp_ratings import refresh_pbp_ratings, ratings_with_sources
from ncaa_sdv_wp_experiment import inspect_game_pbp


class PbpLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(':memory:')
        pd.DataFrame([dict(game_id=1, season=2026, game_rating=5.17,
                          efficiency_rating=8, overtimes_rating=0,
                          score_diff_rating=6, stat_rating=7,
                          leader_changes_rating=2, tds_rating=8)]).to_sql(
                              'ncaa_game_ratings', self.connection, index=False)
        pd.DataFrame([dict(id=1, home_points=31, away_points=24, completed=1)]).to_sql(
            'ncaa_games', self.connection, index=False)
        self.pbp = pd.DataFrame(dict(
            game_id=[1]*80, sequenceNumber=range(1,81),
            period=[1]*20+[2]*20+[3]*20+[4]*20,
            homeScore=[31]*80, awayScore=[24]*80,
            **{'end.homeScore':[31]*80, 'end.awayScore':[24]*80},
            home_wp_before=[0.05+i/100 for i in range(80)],
            gameSpread=[7.5]*80, gameSpreadAvailable=[True]*80,
            status_type_completed=[True]*80))

    def tearDown(self):
        self.connection.close()

    def refresh(self, frame):
        with patch('ncaa_pbp_ratings.pd.read_parquet', return_value=frame):
            refresh_pbp_ratings(self.connection, [2026], {2026:Path('fixture.parquet')})

    def rating(self):
        return self.connection.execute('SELECT game_rating FROM ncaa_game_ratings').fetchone()[0]

    def test_export_source_without_enrollment(self):
        self.assertEqual(ratings_with_sources(self.connection).rating_source.tolist(), ['legacy'])

    def test_export_accepted_source_survives_fetch_failure(self):
        self.refresh(self.pbp)
        partial = self.pbp.copy()
        partial['status_type_completed'] = False
        self.refresh(partial)
        self.assertEqual(ratings_with_sources(self.connection).rating_source.tolist(), ['pbp'])
        self.connection.execute('DELETE FROM ncaa_rating_sources')
        self.assertEqual(ratings_with_sources(self.connection).rating_source.tolist(), ['legacy'])

    def test_partial_then_complete_then_partial_then_offline(self):
        partial = self.pbp.copy()
        partial['status_type_completed'] = False
        self.refresh(partial)
        self.assertEqual(self.rating(), 5.17)
        self.refresh(self.pbp)
        accepted = self.rating()
        self.assertNotEqual(accepted, 5.17)
        self.refresh(self.pbp)
        self.assertEqual(self.rating(), accepted)
        self.refresh(partial)
        self.assertEqual(self.rating(), accepted)
        # A CFBD full rebuild writes its legacy rating back into the main table.
        self.connection.execute('UPDATE ncaa_game_ratings SET game_rating=5.17')
        self.connection.commit()
        with patch('ncaa_pbp_ratings.download_pbp', side_effect=OSError('offline')):
            refresh_pbp_ratings(self.connection, [2026])
        self.assertEqual(self.rating(), accepted)
        state = self.connection.execute(
            'SELECT legacy_game_rating,rating_source,pbp_status FROM ncaa_rating_sources').fetchone()
        self.assertEqual(state, (5.17,'pbp','source_unavailable'))

    def test_last_score_used_after_overtime_correction(self):
        self.pbp.loc[60, 'end.homeScore'] = 34
        result = inspect_game_pbp(self.pbp, pd.Series({'home_points':31,'away_points':24}))
        self.assertEqual(result['pbp_status'],'complete')

    def test_historical_float_completion_flags(self):
        self.pbp['status_type_completed'] = 1.0
        self.pbp['gameSpreadAvailable'] = 1.0
        self.refresh(self.pbp)
        self.assertEqual(ratings_with_sources(self.connection).rating_source.tolist(), ['pbp'])
        self.pbp.loc[20, 'status_type_completed'] = None
        result = inspect_game_pbp(self.pbp, pd.Series({'home_points':31,'away_points':24}))
        self.assertEqual(result['pbp_status'], 'source_not_completed')

    def test_incomplete_wp_or_wrong_final_score_preserves_legacy(self):
        self.pbp.loc[0,'home_wp_before'] = None
        self.refresh(self.pbp)
        self.assertEqual(self.rating(),5.17)
        self.pbp.loc[0,'home_wp_before'] = 0.05
        self.pbp.loc[79,'end.homeScore'] = 32
        self.refresh(self.pbp)
        self.assertEqual(self.rating(),5.17)
