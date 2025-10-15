"""
Test utility functions and player prediction logic
"""
import pytest
import sys
import os
from unittest.mock import patch

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Supabase before importing modules that use it
with patch('supabase.create_client'):
    with patch.dict(os.environ, {'SUPABASE_URL': 'test', 'SUPABASE_KEY': 'test'}):
        from fpl_predictor import (
            calculate_player_form_score,
            calculate_fixture_favorability,
            calculate_team_strength_score,
            predict_player_points,
        )


class TestPlayerFormScore:
    """Test player form calculation"""

    def test_form_score_zero_games(self):
        """Test form score for player with no games"""
        player = {"total_points": 0, "minutes": 0, "element_type": 3}
        score = calculate_player_form_score(player)
        assert score == 0

    def test_form_score_good_midfielder(self):
        """Test form score for good midfielder"""
        player = {
            "total_points": 90,  # Good points
            "minutes": 1800,     # 20 games worth
            "element_type": 3    # Midfielder
        }
        score = calculate_player_form_score(player)
        assert 3 <= score <= 10

    def test_form_score_excellent_forward(self):
        """Test form score for excellent forward"""
        player = {
            "total_points": 150,  # Excellent points
            "minutes": 1800,      # 20 games
            "element_type": 4     # Forward
        }
        score = calculate_player_form_score(player)
        assert score >= 5

    def test_form_score_different_positions(self):
        """Test that different positions have appropriate benchmarks"""
        base_player = {"total_points": 50, "minutes": 900}  # 10 games, 5 pts/game
        
        gk_score = calculate_player_form_score({**base_player, "element_type": 1})
        def_score = calculate_player_form_score({**base_player, "element_type": 2})
        mid_score = calculate_player_form_score({**base_player, "element_type": 3})
        fwd_score = calculate_player_form_score({**base_player, "element_type": 4})
        
        # All should be valid scores
        assert all(0 <= score <= 10 for score in [gk_score, def_score, mid_score, fwd_score])


class TestFixtureFavorability:
    """Test fixture difficulty calculations"""

    def test_fixture_favorability_easy_fixtures(self):
        """Test favorability with easy fixtures"""
        fixture_data = {
            1: {"avg_difficulty": 2.0, "home_games": 3, "away_games": 2}
        }
        favorability = calculate_fixture_favorability(1, fixture_data)
        assert favorability > 5  # Easy fixtures should be favorable

    def test_fixture_favorability_hard_fixtures(self):
        """Test favorability with difficult fixtures"""
        fixture_data = {
            1: {"avg_difficulty": 4.5, "home_games": 1, "away_games": 4}
        }
        favorability = calculate_fixture_favorability(1, fixture_data)
        assert favorability < 5  # Hard fixtures should be less favorable

    def test_fixture_favorability_missing_team(self):
        """Test favorability for team not in fixture data"""
        fixture_data = {2: {"avg_difficulty": 3.0, "home_games": 2, "away_games": 3}}
        favorability = calculate_fixture_favorability(999, fixture_data)
        assert favorability == 5.0  # Should return neutral score


class TestTeamStrengthScore:
    """Test team strength calculations"""

    def test_team_strength_strong_team(self):
        """Test strength for a strong team"""
        team_form_data = {
            1: {"goals_for": 25, "goals_against": 8, "wins": 8, "draws": 2, "losses": 0}
        }
        strength = calculate_team_strength_score(1, team_form_data)
        assert strength > 6  # Strong team should have high score

    def test_team_strength_weak_team(self):
        """Test strength for a weak team"""
        team_form_data = {
            1: {"goals_for": 5, "goals_against": 25, "wins": 1, "draws": 2, "losses": 7}
        }
        strength = calculate_team_strength_score(1, team_form_data)
        assert strength < 4  # Weak team should have low score

    def test_team_strength_missing_team(self):
        """Test strength for missing team data"""
        team_form_data = {2: {"goals_for": 15, "goals_against": 15, "wins": 3, "draws": 4, "losses": 3}}
        strength = calculate_team_strength_score(999, team_form_data)
        assert strength == 5.0  # Should return neutral score


class TestPlayerPointsPrediction:
    """Test the main prediction function"""

    def test_predict_player_points_basic(self):
        """Test basic prediction functionality"""
        player = {
            "id": 1,
            "team": 1,
            "element_type": 3,  # Midfielder
            "total_points": 60,
            "minutes": 1350,    # 15 games
            "now_cost": 80,     # £8.0m
            "selected_by_percent": "15.5",
            "chance_of_playing_this_round": 100,
            "chance_of_playing_next_round": 100,
        }
        
        match_data = {
            "fixture_difficulty": {
                1: {"avg_difficulty": 2.5, "home_games": 3, "away_games": 2}
            },
            "team_form": {
                1: {"goals_for": 20, "goals_against": 12, "wins": 6, "draws": 3, "losses": 1}
            }
        }
        
        prediction = predict_player_points(player, match_data)
        
        # Check prediction structure
        required_keys = [
            "player_id", "name", "position", "team_id", "predicted_points",
            "confidence", "form_score", "fixture_favorability", "team_strength",
            "price", "ownership", "value_rating"
        ]
        
        for key in required_keys:
            assert key in prediction
        
        # Check reasonable ranges
        assert 0 <= prediction["predicted_points"] <= 20
        assert 0 <= prediction["confidence"] <= 10
        assert 0 <= prediction["form_score"] <= 10
        assert 0 <= prediction["fixture_favorability"] <= 10
        assert 0 <= prediction["team_strength"] <= 10

    def test_predict_injured_player(self):
        """Test prediction for injured player"""
        player = {
            "id": 2,
            "team": 1,
            "element_type": 4,  # Forward
            "total_points": 80,
            "minutes": 1200,
            "now_cost": 100,
            "selected_by_percent": "25.0",
            "chance_of_playing_this_round": 25,  # Injured
            "chance_of_playing_next_round": 75,
        }
        
        match_data = {
            "fixture_difficulty": {1: {"avg_difficulty": 3.0, "home_games": 2, "away_games": 3}},
            "team_form": {1: {"goals_for": 15, "goals_against": 15, "wins": 4, "draws": 4, "losses": 2}}
        }
        
        prediction = predict_player_points(player, match_data)
        
        # Injured player should have lower prediction
        assert prediction["predicted_points"] < 5
        assert "injury_risk" in prediction["risk_factors"] or "doubtful" in prediction["risk_factors"]


if __name__ == "__main__":
    pytest.main([__file__])