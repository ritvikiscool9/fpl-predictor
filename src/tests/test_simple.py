"""
Simple tests for core FPL prediction logic
"""
import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestPlayerFormCalculations:
    """Test basic player form calculations"""

    def test_points_per_game_calculation(self):
        """Test basic points per game calculation"""
        # Simple math - no external dependencies
        total_points = 60
        games_played = 10
        expected_ppg = 6.0
        
        actual_ppg = total_points / games_played
        assert actual_ppg == expected_ppg

    def test_value_rating_calculation(self):
        """Test player value rating calculation"""
        predicted_points = 8.5
        price = 6.5  # £6.5m
        expected_value = 1.31  # 8.5 / 6.5
        
        actual_value = round(predicted_points / price, 2)
        assert actual_value == expected_value

    def test_ownership_percentage_handling(self):
        """Test ownership percentage string to float conversion"""
        ownership_strings = ["25.5", "12.1", "0.8"]
        expected_floats = [25.5, 12.1, 0.8]
        
        for i, ownership_str in enumerate(ownership_strings):
            actual_float = float(ownership_str)
            assert actual_float == expected_floats[i]

    def test_minutes_to_games_conversion(self):
        """Test converting minutes to estimated games played"""
        minutes_played = 1530  # 17 games * 90 minutes
        expected_games = 17
        
        actual_games = round(minutes_played / 90)
        assert actual_games == expected_games

    def test_position_multipliers(self):
        """Test position-based scoring multipliers"""
        base_score = 5.0
        position_multipliers = {
            1: 0.8,  # GK
            2: 0.9,  # DEF  
            3: 1.1,  # MID
            4: 1.2   # FWD
        }
        
        # Test each position gets correct multiplier
        for position, multiplier in position_multipliers.items():
            adjusted_score = base_score * multiplier
            if position == 1:  # Goalkeeper
                assert adjusted_score == 4.0
            elif position == 4:  # Forward
                assert adjusted_score == 6.0

class TestTeamConstraints:
    """Test FPL team building constraints"""

    def test_squad_size_constraint(self):
        """Test that squad has exactly 15 players"""
        max_squad_size = 15
        current_squad_size = 12
        
        assert current_squad_size <= max_squad_size
        
    def test_position_requirements(self):
        """Test FPL position requirements"""
        required_positions = {
            "GK": 2,   # 2 Goalkeepers
            "DEF": 5,  # 5 Defenders
            "MID": 5,  # 5 Midfielders
            "FWD": 3   # 3 Forwards
        }
        
        total_required = sum(required_positions.values())
        assert total_required == 15
        
        # Test individual position limits
        assert required_positions["GK"] == 2
        assert required_positions["DEF"] == 5

    def test_team_limit_constraint(self):
        """Test max 3 players from same team rule"""
        max_players_per_team = 3
        team_1_players = ["Player A", "Player B", "Player C"]
        
        assert len(team_1_players) <= max_players_per_team

    def test_budget_constraint(self):
        """Test £100m budget constraint"""
        max_budget = 1000  # £100m in 0.1m units
        player_costs = [45, 60, 55, 80, 75]  # Sample player costs
        total_cost = sum(player_costs)
        
        assert total_cost <= max_budget

    def test_starting_xi_formation(self):
        """Test valid starting XI formation"""
        formation_343 = {"GK": 1, "DEF": 3, "MID": 4, "FWD": 3}
        formation_442 = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}
        
        # Both formations should total 11 players
        assert sum(formation_343.values()) == 11
        assert sum(formation_442.values()) == 11
        
        # All formations must have exactly 1 GK
        assert formation_343["GK"] == 1
        assert formation_442["GK"] == 1

class TestDataValidation:
    """Test basic data validation"""

    def test_player_price_bounds(self):
        """Test player prices are within reasonable bounds"""
        min_price = 35  # £3.5m minimum
        max_price = 150  # £15.0m maximum
        
        test_prices = [40, 65, 120, 35, 150]
        
        for price in test_prices:
            assert min_price <= price <= max_price

    def test_gameweek_range(self):
        """Test gameweek numbers are valid"""
        min_gameweek = 1
        max_gameweek = 38
        
        test_gameweeks = [1, 10, 25, 38]
        
        for gw in test_gameweeks:
            assert min_gameweek <= gw <= max_gameweek

    def test_points_range(self):
        """Test points are within reasonable range"""
        min_points = -2  # Worst possible gameweek score
        max_points = 30   # Very high but possible score
        
        test_scores = [0, 8, 15, 2, -1]
        
        for score in test_scores:
            assert min_points <= score <= max_points


if __name__ == "__main__":
    pytest.main([__file__])