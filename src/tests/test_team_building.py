"""
Test team building and recommendation logic
"""
import pytest
import sys
import os
from unittest.mock import patch, Mock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Supabase before importing modules that use it
with patch('supabase.create_client'):
    with patch.dict(os.environ, {'SUPABASE_URL': 'test', 'SUPABASE_KEY': 'test', 'API_KEY': 'test_api'}):
        from fpl_predictor import (
            build_optimal_team,
            generate_transfer_recommendations,
            get_best_players_by_position
        )


class TestTeamBuilding:
    """Test optimal team building functionality"""

    def create_mock_match_data(self):
        """Create mock match data for testing"""
        return {
            "fpl_data": {
                "elements": [
                    # Goalkeepers
                    {"id": 1, "element_type": 1, "team": 1, "now_cost": 45, "total_points": 60, "minutes": 1800, "selected_by_percent": "10.5"},
                    {"id": 2, "element_type": 1, "team": 2, "now_cost": 50, "total_points": 80, "selected_by_percent": "15.2"},
                    
                    # Defenders
                    {"id": 3, "element_type": 2, "team": 1, "now_cost": 55, "total_points": 70, "minutes": 1700, "selected_by_percent": "20.1"},
                    {"id": 4, "element_type": 2, "team": 2, "now_cost": 60, "total_points": 85, "minutes": 1800, "selected_by_percent": "25.3"},
                    {"id": 5, "element_type": 2, "team": 3, "now_cost": 45, "total_points": 55, "minutes": 1600, "selected_by_percent": "12.7"},
                    {"id": 6, "element_type": 2, "team": 4, "now_cost": 50, "total_points": 65, "minutes": 1650, "selected_by_percent": "18.9"},
                    {"id": 7, "element_type": 2, "team": 5, "now_cost": 40, "total_points": 45, "minutes": 1500, "selected_by_percent": "8.4"},
                    
                    # Midfielders
                    {"id": 8, "element_type": 3, "team": 1, "now_cost": 120, "total_points": 150, "minutes": 1800, "selected_by_percent": "45.6"},
                    {"id": 9, "element_type": 3, "team": 2, "now_cost": 80, "total_points": 90, "minutes": 1700, "selected_by_percent": "22.3"},
                    {"id": 10, "element_type": 3, "team": 3, "now_cost": 60, "total_points": 70, "minutes": 1600, "selected_by_percent": "15.8"},
                    {"id": 11, "element_type": 3, "team": 4, "now_cost": 70, "total_points": 80, "minutes": 1650, "selected_by_percent": "18.7"},
                    {"id": 12, "element_type": 3, "team": 5, "now_cost": 55, "total_points": 60, "minutes": 1550, "selected_by_percent": "12.1"},
                    
                    # Forwards
                    {"id": 13, "element_type": 4, "team": 1, "now_cost": 110, "total_points": 140, "minutes": 1750, "selected_by_percent": "35.4"},
                    {"id": 14, "element_type": 4, "team": 2, "now_cost": 90, "total_points": 100, "minutes": 1600, "selected_by_percent": "20.8"},
                    {"id": 15, "element_type": 4, "team": 3, "now_cost": 70, "total_points": 75, "minutes": 1500, "selected_by_percent": "15.2"},
                ],
                "teams": [
                    {"id": 1, "name": "Arsenal"},
                    {"id": 2, "name": "Liverpool"},
                    {"id": 3, "name": "Tottenham"},
                    {"id": 4, "name": "Newcastle"},
                    {"id": 5, "name": "Brighton"}
                ]
            },
            "fixture_difficulty": {
                i: {"avg_difficulty": 3.0, "home_games": 2, "away_games": 3} 
                for i in range(1, 6)
            },
            "team_form": {
                i: {"goals_for": 15, "goals_against": 12, "wins": 5, "draws": 3, "losses": 2} 
                for i in range(1, 6)
            }
        }

    def test_build_optimal_team_structure(self):
        """Test that optimal team has correct structure"""
        match_data = self.create_mock_match_data()
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            # Mock predictions for all players
            mock_predict.side_effect = lambda player, *args: {
                "player_id": player["id"],
                "name": f"Player {player['id']}",
                "position": player["element_type"],
                "team_id": player["team"],
                "predicted_points": 5.0 + (player["total_points"] / 20),  # Reasonable prediction
                "price": player["now_cost"] / 10,
                "ownership": float(player["selected_by_percent"]),
                "team_name": f"Team {player['team']}"
            }
            
            result = build_optimal_team(match_data, budget=1000)
            
            # Check structure
            required_keys = ["squad", "starting_xi", "bench", "formation", "total_cost", "predicted_points"]
            for key in required_keys:
                assert key in result
            
            # Check squad composition
            assert len(result["squad"]) <= 15  # Max 15 players
            assert len(result["starting_xi"]) == 11  # Exactly 11 starters
            assert len(result["bench"]) <= 4  # Max 4 bench players
            
            # Check budget constraint
            assert result["total_cost"] <= 100.0  # £100m budget

    def test_build_optimal_team_position_constraints(self):
        """Test that team respects FPL position constraints"""
        match_data = self.create_mock_match_data()
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            mock_predict.side_effect = lambda player, *args: {
                "player_id": player["id"],
                "name": f"Player {player['id']}",
                "position": player["element_type"],
                "team_id": player["team"],
                "predicted_points": 6.0,
                "price": player["now_cost"] / 10,
                "ownership": float(player["selected_by_percent"]),
                "team_name": f"Team {player['team']}"
            }
            
            result = build_optimal_team(match_data, budget=1000)
            
            # Count positions in squad
            squad_positions = {}
            for player in result["squad"]:
                pos = player["position"]
                squad_positions[pos] = squad_positions.get(pos, 0) + 1
            
            # Check FPL constraints: 2 GK, 5 DEF, 5 MID, 3 FWD
            expected_positions = {1: 2, 2: 5, 3: 5, 4: 3}
            for pos, expected_count in expected_positions.items():
                actual_count = squad_positions.get(pos, 0)
                assert actual_count <= expected_count, f"Too many players in position {pos}: {actual_count} > {expected_count}"

    def test_generate_transfer_recommendations_structure(self):
        """Test transfer recommendations structure"""
        match_data = self.create_mock_match_data()
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            mock_predict.side_effect = lambda player, *args: {
                "player_id": player["id"],
                "name": f"Player {player['id']}",
                "position": player["element_type"],
                "team_id": player["team"],
                "predicted_points": 5.0 + (player["total_points"] / 30),
                "price": player["now_cost"] / 10,
                "ownership": float(player["selected_by_percent"]),
                "value_rating": 2.5,
                "team_name": f"Team {player['team']}"
            }
            
            recommendations = generate_transfer_recommendations(match_data, budget=100, top_n=3)
            
            # Check structure
            expected_keys = ["best_value", "highest_predicted", "differential_picks"]
            for key in expected_keys:
                assert key in recommendations
                assert isinstance(recommendations[key], list)

    def test_get_best_players_by_position(self):
        """Test getting best players by position"""
        match_data = self.create_mock_match_data()
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            mock_predict.side_effect = lambda player, *args: {
                "player_id": player["id"],
                "name": f"Player {player['id']}",
                "position": player["element_type"],
                "predicted_points": 4.0 + (player["total_points"] / 25),
                "price": player["now_cost"] / 10,
                "ownership": float(player["selected_by_percent"]),
                "team_name": f"Team {player['team']}"
            }
            
            best_players = get_best_players_by_position(match_data, top_n=2)
            
            # Should have all 4 positions
            expected_positions = ["Goalkeepers", "Defenders", "Midfielders", "Forwards"]
            for position in expected_positions:
                assert position in best_players
                assert len(best_players[position]) <= 2  # top_n = 2


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_player_data(self):
        """Test handling of empty player data"""
        match_data = {
            "fpl_data": {"elements": [], "teams": []},
            "fixture_difficulty": {},
            "team_form": {}
        }
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            result = build_optimal_team(match_data, budget=1000)
            
            # Should handle empty data gracefully
            assert "squad" in result
            assert len(result["squad"]) == 0

    def test_insufficient_budget(self):
        """Test team building with very low budget"""
        match_data = {
            "fpl_data": {
                "elements": [
                    {"id": 1, "element_type": 1, "team": 1, "now_cost": 200, "total_points": 60, "selected_by_percent": "10.5"}  # Expensive player
                ],
                "teams": [{"id": 1, "name": "Arsenal"}]
            },
            "fixture_difficulty": {1: {"avg_difficulty": 3.0, "home_games": 2, "away_games": 3}},
            "team_form": {1: {"goals_for": 15, "goals_against": 12, "wins": 5, "draws": 3, "losses": 2}}
        }
        
        with patch('fpl_predictor.predict_player_points') as mock_predict:
            mock_predict.side_effect = lambda player, *args: {
                "player_id": player["id"],
                "name": f"Player {player['id']}",
                "position": player["element_type"],
                "team_id": player["team"],
                "predicted_points": 6.0,
                "price": player["now_cost"] / 10,
                "ownership": float(player["selected_by_percent"]),
                "team_name": f"Team {player['team']}"
            }
            
            result = build_optimal_team(match_data, budget=100)  # £10m budget, but player costs £20m
            
            # Should handle budget constraints
            assert result["total_cost"] <= 10.0


if __name__ == "__main__":
    pytest.main([__file__])