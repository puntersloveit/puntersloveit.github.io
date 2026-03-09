import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / 'scripts'))

import functions as fn  # noqa: E402


class FakeRank:
    def __init__(self, rank: int, school: str):
        self.rank = rank
        self.school = school

    def to_dict(self):
        return {'rank': self.rank, 'school': self.school}


class FakePoll:
    def __init__(self, poll: str, ranks: list[FakeRank]):
        self.poll = poll
        self.ranks = ranks


class FakeWeekRanking:
    def __init__(self, polls: list[FakePoll], season: int, week: int, season_type: str):
        self.polls = polls
        self.season = season
        self.week = week
        self.season_type = season_type


class FunctionsTests(unittest.TestCase):
    def test_saturate_hex_color_rejects_invalid_hex(self):
        self.assertEqual(fn.saturate_hex_color('#121121121', 0.5, 0.3), '#FFFFFF')
        self.assertEqual(fn.saturate_hex_color('zzzzzz', 0.5, 0.3), '#FFFFFF')

    def test_saturate_hex_color_keeps_valid_hex_shape(self):
        color = fn.saturate_hex_color('#336699', -10.0, 10.0)
        self.assertRegex(color, r'^#[0-9a-f]{6}$')

    def test_parse_week_ap25_rank_returns_empty_when_poll_missing(self):
        week = FakeWeekRanking(
            polls=[FakePoll('Coaches Poll', [FakeRank(1, 'Team A')])],
            season=2025,
            week=3,
            season_type='regular',
        )
        result = fn.parse_week_ap25_rank_into_pddf(week)
        self.assertTrue(result.empty)
        self.assertEqual(
            list(result.columns),
            ['rank', 'school', 'season', 'week', 'season_type'],
        )

    def test_parse_week_ap25_rank_extracts_ap_poll(self):
        week = FakeWeekRanking(
            polls=[
                FakePoll('Coaches Poll', [FakeRank(1, 'Team A')]),
                FakePoll('AP Top 25', [FakeRank(1, 'Team B'), FakeRank(2, 'Team C')]),
            ],
            season=2025,
            week=4,
            season_type='regular',
        )
        result = fn.parse_week_ap25_rank_into_pddf(week)
        self.assertEqual(result.shape[0], 2)
        self.assertListEqual(result['school'].tolist(), ['Team B', 'Team C'])
        self.assertTrue((result['season'] == 2025).all())
        self.assertTrue((result['week'] == 4).all())

    def test_write_teams_yaml_deduplicates_and_sorts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'teams.yml'
            fn.write_teams_yaml(
                ['Rice', '  UConn  ', '', 'Rice', None, 'Sam Houston'],
                str(output_path),
            )
            text = output_path.read_text(encoding='utf-8')

        teams = [line.strip()[2:] for line in text.splitlines() if line.strip().startswith('- ')]
        self.assertEqual(teams, ['Rice', 'Sam Houston', 'UConn'])


if __name__ == '__main__':
    unittest.main()
