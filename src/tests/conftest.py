"""
Test fixtures and common test data
"""
import pytest
import sys
import os
from unittest.mock import patch

# Add the parent directories to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(src_dir)
sys.path.insert(0, src_dir)
sys.path.insert(0, root_dir)

# Setup test environment
from test_env import setup_test_environment
setup_test_environment()


@pytest.fixture
def sample_fpl_data():
    """Sample FPL data for testing"""
    return {
        "elements": [
            {
                "id": 1,
                "first_name": "Mohamed",
                "second_name": "Salah",
                "element_type": 3,  # Midfielder
                "team": 1,
                "total_points": 150,
                "minutes": 1800,
                "goals_scored": 15,
                "assists": 10,
                "now_cost": 120,
                "selected_by_percent": "35.5",
                "chance_of_playing_this_round": 100,
                "chance_of_playing_next_round": 100,
                "form": "8.5",
                "points_per_game": "6.2"
            },
            {
                "id": 2,
                "first_name": "Virgil",
                "second_name": "van Dijk",
                "element_type": 2,  # Defender
                "team": 1,
                "total_points": 80,
                "minutes": 1700,
                "goals_scored": 3,
                "assists": 2,
                "clean_sheets": 8,
                "now_cost": 65,
                "selected_by_percent": "22.1",
                "chance_of_playing_this_round": 100,
                "chance_of_playing_next_round": 100,
                "form": "6.2",
                "points_per_game": "4.5"
            }
        ],
        "teams": [
            {"id": 1, "name": "Liverpool", "short_name": "LIV"},
            {"id": 2, "name": "Arsenal", "short_name": "ARS"}
        ],
        "events": [
            {
                "id": 10,
                "name": "Gameweek 10",
                "is_current": True,
                "finished": False,
                "deadline_time": "2024-11-02T11:30:00Z"
            }
        ]
    }


@pytest.fixture
def sample_match_data():
    """Sample match data for testing predictions"""
    return {
        "fixture_difficulty": {
            1: {"avg_difficulty": 2.5, "home_games": 3, "away_games": 2},
            2: {"avg_difficulty": 3.8, "home_games": 1, "away_games": 4}
        },
        "team_form": {
            1: {
                "goals_for": 25,
                "goals_against": 8,
                "wins": 8,
                "draws": 2,
                "losses": 0,
                "points": 26
            },
            2: {
                "goals_for": 20,
                "goals_against": 12,
                "wins": 6,
                "draws": 3,
                "losses": 1,
                "points": 21
            }
        }
    }


@pytest.fixture
def sample_players():
    """Sample player data for different positions"""
    return {
        "goalkeeper": {
            "id": 10,
            "element_type": 1,
            "team": 1,
            "total_points": 60,
            "minutes": 1800,
            "goals_conceded": 8,
            "saves": 45,
            "clean_sheets": 8,
            "now_cost": 45,
            "selected_by_percent": "12.5"
        },
        "defender": {
            "id": 20,
            "element_type": 2,
            "team": 1,
            "total_points": 75,
            "minutes": 1650,
            "goals_scored": 2,
            "assists": 4,
            "clean_sheets": 6,
            "now_cost": 55,
            "selected_by_percent": "18.7"
        },
        "midfielder": {
            "id": 30,
            "element_type": 3,
            "team": 2,
            "total_points": 90,
            "minutes": 1500,
            "goals_scored": 8,
            "assists": 6,
            "now_cost": 80,
            "selected_by_percent": "25.3"
        },
        "forward": {
            "id": 40,
            "element_type": 4,
            "team": 2,
            "total_points": 120,
            "minutes": 1400,
            "goals_scored": 12,
            "assists": 3,
            "now_cost": 95,
            "selected_by_percent": "30.1"
        }
    }


@pytest.fixture
def budget_constrained_team():
    """Team data for testing budget constraints"""
    return {
        "cheap_players": [
            {"id": i, "element_type": 1 + (i % 4), "team": 1 + (i % 3), "now_cost": 40, "total_points": 30}
            for i in range(15)
        ],
        "expensive_players": [
            {"id": i + 50, "element_type": 1 + (i % 4), "team": 1 + (i % 3), "now_cost": 150, "total_points": 120}
            for i in range(5)
        ]
    }


@pytest.fixture
def mock_supabase_response():
    """Mock Supabase response structure"""
    return {
        "data": [
            {
                "id": 1,
                "player_name": "Test Player",
                "total_points": 50,
                "minutes": 900,
                "element_type": 3,
                "team_id": 1,
                "gameweek": 10,
                "season": "2024-25"
            }
        ],
        "count": 1
    }


class TestDataValidators:
    """Common validation functions for tests"""
    
    @staticmethod
    def validate_player_prediction(prediction):
        """Validate a player prediction has required fields and reasonable values"""
        required_fields = [
            "player_id", "name", "position", "team_id", "predicted_points",
            "confidence", "form_score", "fixture_favorability", "team_strength",
            "price", "ownership", "value_rating"
        ]
        
        for field in required_fields:
            assert field in prediction, f"Missing required field: {field}"
        
        # Value ranges
        assert 0 <= prediction["predicted_points"] <= 25
        assert 0 <= prediction["confidence"] <= 10
        assert 0 <= prediction["form_score"] <= 10
        assert 0 <= prediction["fixture_favorability"] <= 10
        assert 0 <= prediction["team_strength"] <= 10
        assert prediction["price"] > 0
        assert 0 <= prediction["ownership"] <= 100

    @staticmethod
    def validate_team_structure(team_result):
        """Validate optimal team structure"""
        required_keys = ["squad", "starting_xi", "bench", "formation", "total_cost", "predicted_points"]
        for key in required_keys:
            assert key in team_result, f"Missing required key: {key}"
        
        # Squad constraints
        assert len(team_result["squad"]) <= 15
        assert len(team_result["starting_xi"]) == 11
        assert len(team_result["bench"]) <= 4
        assert team_result["total_cost"] > 0
        assert team_result["predicted_points"] >= 0