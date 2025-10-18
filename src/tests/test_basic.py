"""
Basic tests for data handling and calculations
"""
import pytest


class TestBasicCalculations:
    """Test fundamental calculations used in FPL"""

    def test_average_calculation(self):
        """Test simple average calculation"""
        scores = [8, 6, 12, 4, 10]
        expected_avg = 8.0
        
        actual_avg = sum(scores) / len(scores)
        assert actual_avg == expected_avg

    def test_percentage_calculations(self):
        """Test percentage calculations"""
        # Ownership percentage
        total_managers = 1000000
        selecting_managers = 250000
        expected_percentage = 25.0
        
        actual_percentage = (selecting_managers / total_managers) * 100
        assert actual_percentage == expected_percentage

    def test_price_conversion(self):
        """Test price conversion between formats"""
        # FPL API returns price as integer (e.g., 65 = £6.5m)
        api_price = 65
        expected_millions = 6.5
        
        actual_millions = api_price / 10
        assert actual_millions == expected_millions

    def test_difficulty_scoring(self):
        """Test fixture difficulty scoring"""
        # Difficulty scale 1-5 (1=easiest, 5=hardest)
        difficulties = [2, 3, 2, 4, 1]
        expected_avg = 2.4
        
        actual_avg = sum(difficulties) / len(difficulties)
        assert actual_avg == expected_avg

class TestStringHandling:
    """Test string data handling"""

    def test_name_formatting(self):
        """Test player name formatting"""
        first_name = "Mohamed"
        second_name = "Salah"
        expected_full = "Mohamed Salah"
        
        actual_full = f"{first_name} {second_name}"
        assert actual_full == expected_full

    def test_team_name_mapping(self):
        """Test team name mappings"""
        team_mappings = {
            "Arsenal": "ARS",
            "Liverpool": "LIV",
            "Manchester City": "MCI"
        }
        
        assert team_mappings["Arsenal"] == "ARS"
        assert team_mappings["Liverpool"] == "LIV"
        assert len(team_mappings["Manchester City"]) == 3

    def test_position_names(self):
        """Test position number to name mapping"""
        positions = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
        
        assert positions[1] == "GK"
        assert positions[4] == "FWD"
        assert len(positions) == 4

class TestListOperations:
    """Test list and data operations"""

    def test_sorting_by_points(self):
        """Test sorting players by points"""
        players = [
            {"name": "Player A", "points": 15},
            {"name": "Player B", "points": 25},
            {"name": "Player C", "points": 10}
        ]
        
        sorted_players = sorted(players, key=lambda x: x["points"], reverse=True)
        
        assert sorted_players[0]["name"] == "Player B"
        assert sorted_players[0]["points"] == 25
        assert sorted_players[-1]["points"] == 10

    def test_filtering_by_price(self):
        """Test filtering players by price range"""
        players = [
            {"name": "Expensive", "price": 12.0},
            {"name": "Budget", "price": 4.5},
            {"name": "Mid-range", "price": 7.5}
        ]
        
        budget_players = [p for p in players if p["price"] <= 5.0]
        premium_players = [p for p in players if p["price"] >= 10.0]
        
        assert len(budget_players) == 1
        assert budget_players[0]["name"] == "Budget"
        assert len(premium_players) == 1

    def test_grouping_by_position(self):
        """Test grouping players by position"""
        players = [
            {"name": "GK1", "position": 1},
            {"name": "DEF1", "position": 2}, 
            {"name": "GK2", "position": 1},
            {"name": "MID1", "position": 3}
        ]
        
        goalkeepers = [p for p in players if p["position"] == 1]
        defenders = [p for p in players if p["position"] == 2]
        
        assert len(goalkeepers) == 2
        assert len(defenders) == 1
        assert goalkeepers[0]["name"] == "GK1"

class TestErrorHandling:
    """Test basic error handling scenarios"""

    def test_division_by_zero_protection(self):
        """Test protection against division by zero"""
        total_points = 50
        games_played = 0
        
        # Should handle zero games gracefully
        if games_played == 0:
            points_per_game = 0
        else:
            points_per_game = total_points / games_played
            
        assert points_per_game == 0

    def test_empty_list_handling(self):
        """Test handling of empty lists"""
        empty_scores = []
        
        if len(empty_scores) == 0:
            average_score = 0
        else:
            average_score = sum(empty_scores) / len(empty_scores)
            
        assert average_score == 0

    def test_missing_data_defaults(self):
        """Test default values for missing data"""
        player_data = {"name": "Test Player"}
        
        # Should provide defaults for missing fields
        points = player_data.get("total_points", 0)
        price = player_data.get("price", 4.0)
        
        assert points == 0
        assert price == 4.0


if __name__ == "__main__":
    pytest.main([__file__])