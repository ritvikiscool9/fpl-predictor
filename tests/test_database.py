"""
Integration tests for database operations
"""
import sys
import os
from unittest.mock import patch, Mock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Supabase before importing modules that use it
with patch('supabase.create_client'):
    with patch.dict(os.environ, {'SUPABASE_URL': 'test', 'SUPABASE_KEY': 'test'}):
        from populate_db import populate_fresh_fpl_data


class TestDatabaseIntegration:
    """Test database integration without hitting real database"""

    @patch('populate_db.requests.get')
    @patch('populate_db.supabase')
    def test_populate_fresh_fpl_data_success(self, mock_supabase, mock_get):
        """Test successful FPL data population"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "events": [
                {
                    "id": 1,
                    "name": "Gameweek 1",
                    "deadline_time": "2024-08-16T17:30:00Z",
                    "finished": False,
                    "is_current": True,
                    "average_entry_score": 0,
                    "highest_score": 0
                }
            ],
            "teams": [
                {
                    "id": 1,
                    "name": "Arsenal",
                    "short_name": "ARS",
                    "code": 3
                }
            ],
            "elements": [
                {
                    "id": 1,
                    "first_name": "Mohamed",
                    "second_name": "Salah",
                    "element_type": 3,
                    "team": 2,
                    "total_points": 150,
                    "minutes": 1800,
                    "goals_scored": 15,
                    "assists": 10,
                    "clean_sheets": 0,
                    "goals_conceded": 0,
                    "own_goals": 0,
                    "penalties_saved": 0,
                    "penalties_missed": 0,
                    "yellow_cards": 2,
                    "red_cards": 0,
                    "saves": 0,
                    "bonus": 20,
                    "bps": 500,
                    "influence": "800.5",
                    "creativity": "600.2",
                    "threat": "900.8",
                    "ict_index": "230.5",
                    "now_cost": 120,
                    "selected_by_percent": "35.5",
                    "transfers_in": 1000,
                    "transfers_out": 200,
                    "form": "8.5",
                    "points_per_game": "6.2",
                    "status": "a",
                    "news": "",
                    "chance_of_playing_this_round": 100,
                    "chance_of_playing_next_round": 100
                }
            ]
        }
        mock_get.return_value = mock_response

        # Mock successful database operations
        mock_supabase.table().upsert().execute.return_value = Mock()
        mock_supabase.table().select().eq().execute.return_value = Mock(data=[{"id": 1}])

        # Should not raise exceptions
        populate_fresh_fpl_data()

        # Verify API was called
        mock_get.assert_called_once_with("https://fantasy.premierleague.com/api/bootstrap-static/")

        # Verify database operations were called
        assert mock_supabase.table.called

    @patch('populate_db.requests.get')
    def test_populate_fresh_fpl_data_api_failure(self, mock_get):
        """Test handling of API failure"""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Should raise exception for API failure
        try:
            populate_fresh_fpl_data()
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Failed to get FPL data: 500" in str(e)

    @patch('populate_db.requests.get')
    @patch('populate_db.supabase')
    def test_populate_fresh_fpl_data_missing_current_gameweek(self, mock_supabase, mock_get):
        """Test handling when no current gameweek is found"""
        # Mock API response without current gameweek
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "events": [
                {
                    "id": 1,
                    "name": "Gameweek 1",
                    "deadline_time": "2024-08-16T17:30:00Z",
                    "finished": True,
                    "is_current": False,  # No current gameweek
                    "average_entry_score": 50,
                    "highest_score": 120
                }
            ],
            "teams": [],
            "elements": []
        }
        mock_get.return_value = mock_response

        # Mock database queries - first return empty (no current GW), then return GW8
        mock_supabase.table().select().eq().execute.side_effect = [
            Mock(data=[]),  # No current gameweek found
            Mock(data=[{"id": 8}])  # Gameweek 8 found
        ]

        # Should handle gracefully and fall back to GW8
        populate_fresh_fpl_data()

        # Should have queried for current gameweek and then GW8
        assert mock_supabase.table().select().eq().execute.call_count >= 2


class TestDataConsistency:
    """Test data consistency and validation"""

    def test_player_data_required_fields(self):
        """Test that player data has all required fields"""
        sample_player = {
            "id": 1,
            "first_name": "Test",
            "second_name": "Player",
            "element_type": 3,
            "team": 1,
            "total_points": 100,
            "minutes": 1500,
            "now_cost": 80,
            "selected_by_percent": "20.5"
        }

        # Check required fields exist
        required_fields = ["id", "element_type", "team", "total_points", "now_cost"]
        for field in required_fields:
            assert field in sample_player, f"Missing required field: {field}"

    def test_gameweek_data_validation(self):
        """Test gameweek data validation"""
        sample_gameweek = {
            "id": 1,
            "name": "Gameweek 1",
            "finished": False,
            "is_current": True
        }

        # Basic validation
        assert isinstance(sample_gameweek["id"], int)
        assert isinstance(sample_gameweek["finished"], bool)
        assert isinstance(sample_gameweek["is_current"], bool)
        assert sample_gameweek["id"] > 0


if __name__ == "__main__":
    # Simple test runner since we don't have pytest installed
    import unittest
    
    # Convert classes to unittest format
    class TestPopulateDB(unittest.TestCase):
        def setUp(self):
            self.db_tests = TestDatabaseIntegration()
            self.consistency_tests = TestDataConsistency()

        def test_populate_success(self):
            self.db_tests.test_populate_fresh_fpl_data_success()

        def test_api_failure(self):
            self.db_tests.test_populate_fresh_fpl_data_api_failure()

        def test_missing_gameweek(self):
            self.db_tests.test_populate_fresh_fpl_data_missing_current_gameweek()

        def test_player_fields(self):
            self.consistency_tests.test_player_data_required_fields()

        def test_gameweek_validation(self):
            self.consistency_tests.test_gameweek_data_validation()

    unittest.main()