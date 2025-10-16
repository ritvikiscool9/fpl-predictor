"""
Test environment setup and utilities
"""
import os
import sys
from unittest.mock import patch, Mock

# Ensure we have required environment variables for testing
def setup_test_environment():
    """Setup test environment with mock credentials"""
    test_env = {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test_key_12345'
    }
    
    for key, value in test_env.items():
        if key not in os.environ:
            os.environ[key] = value

# Set up environment before any imports
setup_test_environment()

def mock_supabase_client():
    """Create a mock Supabase client for testing"""
    mock_client = Mock()
    mock_table = Mock()
    mock_query = Mock()
    
    # Mock the chained methods
    mock_query.execute.return_value = Mock(data=[], count=0)
    mock_table.select.return_value = mock_query
    mock_table.insert.return_value = mock_query
    mock_table.upsert.return_value = mock_query
    mock_table.update.return_value = mock_query
    mock_table.delete.return_value = mock_query
    mock_client.table.return_value = mock_table
    
    return mock_client

# Global mock for Supabase
MOCK_SUPABASE = mock_supabase_client()

def get_mock_supabase():
    """Get the global mock Supabase client"""
    return MOCK_SUPABASE