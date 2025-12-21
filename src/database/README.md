# Database Management Scripts

This folder contains all database-related scripts for the FPL Predictor project.

## Core Database Scripts

### Data Refresh & Population
- **`database_refresh.py`** - Unified database refresh system (replaces 3 separate scripts)
- **`fast_performance_refresh.py`** - Optimized player performance data loader (730x faster)
- **`update_player_prices.py`** - Updates current player prices and selection percentages from FPL API

### Data Verification & Quality
- **`check_database.py`** - Comprehensive database health check across all tables
- **`verify_fix.py`** - Verifies database fixes and data consistency
- **`verify_player_performances.py`** - Detailed verification of player performance data
- **`check_fixture_quality.py`** - Validates fixture data completeness and accuracy

### Data Analysis & Export
- **`export_complete_data.py`** - Complete data export with pagination (handles 7,302+ records)
- **`analyze_performance_gaps.py`** - Analyzes gaps in player performance data across gameweeks

## Usage Instructions

### Daily/Weekly Maintenance
```bash
# Refresh all player performance data
python database/fast_performance_refresh.py

# Update current player prices
python database/update_player_prices.py

# Verify database health
python database/check_database.py
```

### Complete Database Refresh
```bash
# Full database refresh (use when starting fresh or fixing major issues)
python database/database_refresh.py
```

### Data Export & Analysis
```bash
# Export complete dataset with pagination
python database/export_complete_data.py

# Analyze data gaps
python database/analyze_performance_gaps.py
```

## Database Tables

- **`player_performances`** - Current season performance data (7,302 records)
- **`historical_player_stats`** - Historical data from previous seasons (51,400 records)
- **`players`** - Player information and names (743 players)
- **`teams`** - Premier League teams (20 teams)
- **`fixtures`** - Match fixtures and results (380 fixtures)
- **`current_team_stats`** - Current team statistics (20 records)

## Recent Improvements

- **Complete Data Coverage**: Now includes all 10 finished gameweeks
- **Optimized Performance**: 730x faster data loading
- **Real-time Pricing**: Current FPL prices and selection percentages
- **Pagination Support**: Handles Supabase 1,000 record query limits
- **Data Validation**: Comprehensive verification and health checks

## Configuration

All database scripts use the Supabase configuration from:
- `src/config/supabase_client.py`
- Environment variables (SUPABASE_URL, SUPABASE_KEY)

## Notes

- Run scripts from the `src/` directory to maintain proper Python paths
- All scripts include comprehensive logging and error handling
- Database refresh operations are atomic and include rollback on errors
- Export scripts handle large datasets with proper pagination