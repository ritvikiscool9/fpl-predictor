"""
Test API interactions and error handling
"""
import pytest
import sys
import os
from unittest.mock import patch, Mock
import requests

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpl_predictor import process_match_data, get_cached_fpl_data
from populate_db import populate_fresh_fpl_data


class TestAPIIntegration:
    """Test API calls and responses"""

    @patch('requests.get')
    def test_fpl_api_timeout_handling(self, mock_get):
        """Test handling of API timeouts"""
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        # Should handle timeout gracefully
        with pytest.raises((requests.Timeout, Exception)):
            populate_fresh_fpl_data()

    @patch('requests.get')
    def test_fpl_api_invalid_json(self, mock_get):
        """Test handling of invalid JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        with pytest.raises((ValueError, Exception)):
            populate_fresh_fpl_data()

    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors"""
        mock_get.side_effect = requests.ConnectionError("Network error")
        
        with pytest.raises((requests.ConnectionError, Exception)):
            populate_fresh_fpl_data()

    @patch('fpl_predictor.supabase')
    def test_cached_data_fallback(self, mock_supabase):
        """Test fallback to cached data when API fails"""
        # Mock database returning cached data
        mock_supabase.table().select().execute.return_value.data = [
            {"team_id": 1, "name": "Arsenal", "strength": 5}
        ]
        
        # Should not raise exceptions
        result = get_cached_fpl_data()
        assert result is not None


class TestErrorScenarios:
    """Test various error scenarios"""

    def test_malformed_player_data(self):
        """Test handling of malformed player data"""
        from fpl_predictor import calculate_player_form_score
        
        # Missing required fields
        malformed_player = {"id": 1}  # Missing total_points, minutes, element_type
        
        # Should handle gracefully (return 0 or default)
        score = calculate_player_form_score(malformed_player)
        assert score == 0

    def test_negative_values_handling(self):
        """Test handling of negative values in data"""
        from fpl_predictor import calculate_player_form_score
        
        negative_player = {
            "total_points": -10,  # Negative points
            "minutes": -100,      # Negative minutes
            "element_type": 3
        }
        
        score = calculate_player_form_score(negative_player)
        assert score >= 0  # Should not return negative scores

    def test_extreme_values(self):
        """Test handling of extreme values"""
        from fpl_predictor import calculate_player_form_score
        
        extreme_player = {
            "total_points": 999999,  # Extremely high points
            "minutes": 999999,       # Extremely high minutes
            "element_type": 3
        }
        
        score = calculate_player_form_score(extreme_player)
        assert 0 <= score <= 10  # Should be within expected range


class TestDataValidation:
    """Test data validation and constraints"""

    def test_position_validation(self):
        """Test that positions are within valid range"""
        from fpl_predictor import calculate_player_form_score
        
        for position in [1, 2, 3, 4]:  # Valid positions
            player = {
                "total_points": 50,
                "minutes": 900,
                "element_type": position
            }
            score = calculate_player_form_score(player)
            assert isinstance(score, (int, float))

    def test_invalid_position(self):
        """Test handling of invalid positions"""
        from fpl_predictor import calculate_player_form_score
        
        invalid_player = {
            "total_points": 50,
            "minutes": 900,
            "element_type": 99  # Invalid position
        }
        
        # Should handle gracefully
        score = calculate_player_form_score(invalid_player)
        assert score >= 0

    def test_budget_constraints(self):
        """Test that team building respects budget constraints"""
        from fpl_predictor import build_optimal_team
        
        # Mock data with expensive players
        expensive_match_data = {
            "fpl_data": {
                "elements": [
                    {"id": 1, "element_type": 1, "team": 1, "now_cost": 200, "total_points": 60, "selected_by_percent": "10.0"},
                ],
                "teams": [{"id": 1, "name": "Arsenal"}]
            },
            "fixture_difficulty": {1: {"avg_difficulty": 3.0, "home_games": 2, "away_games": 3}},
            "team_form": {1: {"goals_for": 15, "goals_against": 12, "wins": 5, "draws": 3, "losses": 2}}
        }
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            mock_predict.return_value = {
                "player_id": 1,
                "name": "Expensive Player",
                "position": 1,
                "team_id": 1,
                "predicted_points": 6.0,
                "price": 20.0,  # £20m player
                "ownership": 10.0,
                "team_name": "Arsenal"
            }
            
            result = build_optimal_team(expensive_match_data, budget=100)  # £10m budget
            
            # Should respect budget even if no players fit
            assert result["total_cost"] <= 10.0


class TestPerformance:
    """Test performance-related aspects"""

    def test_prediction_speed(self):
        """Test that predictions complete in reasonable time"""
        import time
        from fpl_predictor import predict_player_points
        
        player = {
            "id": 1,
            "team": 1,
            "element_type": 3,
            "total_points": 60,
            "minutes": 1350,
            "now_cost": 80,
            "selected_by_percent": "15.5",
            "chance_of_playing_this_round": 100,
            "chance_of_playing_next_round": 100,
        }
        
        match_data = {
            "fixture_difficulty": {1: {"avg_difficulty": 3.0, "home_games": 2, "away_games": 3}},
            "team_form": {1: {"goals_for": 15, "goals_against": 12, "wins": 5, "draws": 3, "losses": 2}}
        }
        
        start_time = time.time()
        prediction = predict_player_points(player, match_data)
        end_time = time.time()
        
        # Should complete quickly (less than 1 second)
        assert end_time - start_time < 1.0
        assert prediction is not None

    def test_large_dataset_handling(self):
        """Test handling of large player datasets"""
        from fpl_predictor import build_optimal_team
        
        # Create dataset with many players
        large_elements = []
        for i in range(100):  # 100 players
            large_elements.append({
                "id": i,
                "element_type": (i % 4) + 1,  # Distribute across positions
                "team": (i % 20) + 1,         # Distribute across 20 teams
                "now_cost": 50 + (i % 100),   # Vary prices
                "total_points": 30 + (i % 120),
                "selected_by_percent": str(5.0 + (i % 40))
            })
        
        large_match_data = {
            "fpl_data": {
                "elements": large_elements,
                "teams": [{"id": i, "name": f"Team {i}"} for i in range(1, 21)]
            },
            "fixture_difficulty": {i: {"avg_difficulty": 3.0, "home_games": 2, "away_games": 3} for i in range(1, 21)},
            "team_form": {i: {"goals_for": 15, "goals_against": 12, "wins": 5, "draws": 3, "losses": 2} for i in range(1, 21)}
        }
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            mock_predict.side_effect = lambda player, *args: {
                "player_id": player["id"],
                "name": f"Player {player['id']}",
                "position": player["element_type"],
                "team_id": player["team"],
                "predicted_points": 5.0,
                "price": player["now_cost"] / 10,
                "ownership": float(player["selected_by_percent"]),
                "team_name": f"Team {player['team']}"
            }
            
            # Should handle large dataset without errors
            result = build_optimal_team(large_match_data, budget=1000)
            assert "squad" in result


if __name__ == "__main__":
    pytest.main([__file__])