"""
Test data collection and database operations
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
import pandas as pd

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Supabase before importing modules that use it
with patch('supabase.create_client'):
    with patch.dict(os.environ, {'SUPABASE_URL': 'test', 'SUPABASE_KEY': 'test', 'API_KEY': 'test_api'}):
        from data_collector import (
            collect_season_gameweeks,
            validate_collected_data,
            analyze_data_quality
        )


class TestDataCollection:
    """Test data collection functions"""

    @patch('data_collector.requests.get')
    def test_collect_season_gameweeks_success(self, mock_get):
        """Test successful gameweek data collection"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "player_name,total_points,minutes\nSalah,12,90\nKane,8,85"
        mock_get.return_value = mock_response
        
        # Mock the database save function
        with patch('data_collector.save_gameweek_data_to_db') as mock_save:
            collect_season_gameweeks("2023-24", "https://test.com")
            
            # Check that save was called (at least once for successful GW1)
            assert mock_save.called

    @patch('data_collector.requests.get')
    def test_collect_season_gameweeks_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Should not raise exception, just handle gracefully
        with patch('data_collector.save_gameweek_data_to_db') as mock_save:
            collect_season_gameweeks("2023-24", "https://test.com")
            
            # Save should not be called for failed requests
            assert not mock_save.called

    def test_validate_collected_data_structure(self):
        """Test data validation returns expected structure"""
        # This tests the structure without actually hitting the database
        with patch('data_collector.supabase') as mock_supabase:
            # Mock database responses
            mock_supabase.table().select().execute.return_value.count = 50000
            
            # Should not raise exceptions
            validate_collected_data()

    def test_analyze_data_quality_with_data(self):
        """Test data quality analysis with mock data"""
        mock_data = [
            {"minutes": 90, "total_points": 8, "element_type": 3},
            {"minutes": 0, "total_points": 0, "element_type": 2},
            {"minutes": 85, "total_points": 6, "element_type": 4}
        ]
        
        with patch('data_collector.supabase') as mock_supabase:
            mock_supabase.table().select().limit().execute.return_value.data = mock_data
            
            # Should complete without errors
            analyze_data_quality()


class TestDataValidation:
    """Test data validation and quality checks"""

    def test_empty_dataframe_handling(self):
        """Test handling of empty data"""
        empty_data = []
        
        with patch('data_collector.supabase') as mock_supabase:
            mock_supabase.table().select().limit().execute.return_value.data = empty_data
            
            # Should handle empty data gracefully
            analyze_data_quality()

    def test_missing_columns_handling(self):
        """Test handling of data with missing expected columns"""
        incomplete_data = [
            {"minutes": 90, "total_points": 8},  # Missing element_type
            {"total_points": 0, "element_type": 2}  # Missing minutes
        ]
        
        with patch('data_collector.supabase') as mock_supabase:
            mock_supabase.table().select().limit().execute.return_value.data = incomplete_data
            
            # Should handle missing columns gracefully
            analyze_data_quality()


if __name__ == "__main__":
    pytest.main([__file__])