"""
FPL Historical Data Collector
Collects historical FPL data from vaastav/Fantasy-Premier-League GitHub repository
"""

import requests
import pandas as pd
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import io

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def collect_historical_gameweek_data():
    """Collect historical FPL data for seasons 2020-21 to 2024-25"""
    github_base = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"
    seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
    
    print("Starting historical data collection...")
    
    for season in seasons:
        print(f"Collecting {season} data...")
        collect_season_data(season, github_base)
    
    print("Historical data collection complete!")

def collect_season_data(season, github_base):
    """Collect all data for a specific season"""
    collect_season_gameweeks(season, github_base)
    collect_season_players(season, github_base)
    collect_season_fixtures(season, github_base)
    
def collect_season_gameweeks(season, github_base):
    """Collect gameweek-by-gameweek player performance data"""
    print(f"Collecting gameweek data for {season}...")
    
    all_gameweek_data = []
    
    for gw in range(1, 39):
        url = f"{github_base}/{season}/gws/gw{gw}.csv"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                df['season'] = season
                df['gameweek'] = gw
                records = df.to_dict('records')
                all_gameweek_data.extend(records)
                
        except Exception as e:
            print(f"Error collecting GW{gw}: {e}")
        
        time.sleep(0.2)
    
    if all_gameweek_data:
        save_gameweek_data_to_db(all_gameweek_data)
        print(f"Saved {len(all_gameweek_data)} gameweek records for {season}")

def collect_season_players(season, github_base):
    """Collect season summary player data"""
    url = f"{github_base}/{season}/players_raw.csv"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df['season'] = season
            print(f"Found {len(df)} players for {season}")
        else:
            print(f"Failed to get players data (Status: {response.status_code})")
            
    except Exception as e:
        print(f"Error collecting players: {e}")

def collect_season_fixtures(season, github_base):
    """Collect fixtures data for the season"""
    url = f"{github_base}/{season}/fixtures.csv"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df['season'] = season
            print(f"Found {len(df)} fixtures for {season}")
        else:
            print(f"Failed to get fixtures data (Status: {response.status_code})")
            
    except Exception as e:
        print(f"Error collecting fixtures: {e}")

def save_gameweek_data_to_db(gameweek_data):
    """Save gameweek performance data to historical_player_stats table"""
    try:
        db_records = []
        
        for record in gameweek_data:
            db_record = {
                'season': record.get('season'),
                'gameweek': record.get('gameweek'),
                'fpl_player_id': record.get('element', record.get('id')),
                'total_points': record.get('total_points', 0),
                'minutes': record.get('minutes', 0),
                'goals_scored': record.get('goals_scored', 0),
                'assists': record.get('assists', 0),
                'clean_sheets': record.get('clean_sheets', 0),
                'goals_conceded': record.get('goals_conceded', 0),
                'own_goals': record.get('own_goals', 0),
                'penalties_saved': record.get('penalties_saved', 0),
                'penalties_missed': record.get('penalties_missed', 0),
                'yellow_cards': record.get('yellow_cards', 0),
                'red_cards': record.get('red_cards', 0),
                'saves': record.get('saves', 0),
                'bonus': record.get('bonus', 0),
                'bps': record.get('bps', 0),
                'influence': float(record.get('influence', 0)),
                'creativity': float(record.get('creativity', 0)),
                'threat': float(record.get('threat', 0)),
                'ict_index': float(record.get('ict_index', 0)),
                'value': record.get('value', record.get('now_cost', 50)),
                'selected': record.get('selected', record.get('selected_by_percent', 0)),
                'transfers_in': record.get('transfers_in', 0),
                'transfers_out': record.get('transfers_out', 0)
            }
            
            if db_record['fpl_player_id']:
                db_records.append(db_record)
        
        batch_size = 100
        for i in range(0, len(db_records), batch_size):
            batch = db_records[i:i+batch_size]
            
            result = supabase.table('historical_player_stats').upsert(
                batch,
                on_conflict='season,gameweek,fpl_player_id'
            ).execute()
        
    except Exception as e:
        print(f"Error saving to database: {e}")

def collect_historical_fixtures():
    """Collect historical fixtures data for all seasons"""
    github_base = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"
    seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
    
    print("Starting historical fixtures collection...")
    
    for season in seasons:
        print(f"Collecting {season} fixtures...")
        collect_season_fixtures_data(season, github_base)
    
    print("Historical fixtures collection complete!")

def collect_season_fixtures_data(season, github_base):
    """Collect fixtures data for a specific season"""
    url = f"{github_base}/{season}/fixtures.csv"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            df['season'] = season
            fixtures_data = df.to_dict('records')
            save_fixtures_data_to_db(fixtures_data)
            print(f"Saved {len(df)} fixtures for {season}")
        else:
            print(f"Failed to get fixtures data (Status: {response.status_code})")
            
    except Exception as e:
        print(f"Error collecting fixtures: {e}")

def save_fixtures_data_to_db(fixtures_data):
    """Save fixtures data to historical_fixtures table"""
    try:
        db_records = []
        
        for fixture in fixtures_data:
            db_record = {
                'season': fixture.get('season'),
                'gameweek': fixture.get('event'),
                'fpl_fixture_id': fixture.get('id'),
                'team_h': fixture.get('team_h'),
                'team_a': fixture.get('team_a'),
                'team_h_score': fixture.get('team_h_score'),
                'team_a_score': fixture.get('team_a_score'),
                'finished': fixture.get('finished', False),
                'kickoff_time': fixture.get('kickoff_time'),
                'team_h_difficulty': fixture.get('team_h_difficulty'),
                'team_a_difficulty': fixture.get('team_a_difficulty')
            }
            
            if db_record['team_h'] and db_record['team_a']:
                db_records.append(db_record)
        
        batch_size = 100
        for i in range(0, len(db_records), batch_size):
            batch = db_records[i:i+batch_size]
            
            result = supabase.table('historical_fixtures').upsert(
                batch,
                on_conflict='season,fpl_fixture_id'
            ).execute()
        
    except Exception as e:
        print(f"Error saving fixtures to database: {e}")

def collect_injury_suspension_data():
    """Collect injury/suspension data for players"""
    print("Injury/Suspension data collection...")
    print("Note: Injury data not available in current data source")
    print("Future enhancement: Integrate with injury tracking APIs")

def create_historical_tables():
    """Print SQL to create all historical data tables in Supabase"""
    
    sql = '''
    -- Historical player performance data (gameweek by gameweek)
    CREATE TABLE IF NOT EXISTS historical_player_stats (
        id SERIAL PRIMARY KEY,
        season VARCHAR(10) NOT NULL,
        gameweek INTEGER NOT NULL,
        fpl_player_id INTEGER NOT NULL,
        total_points INTEGER DEFAULT 0,
        minutes INTEGER DEFAULT 0,
        goals_scored INTEGER DEFAULT 0,
        assists INTEGER DEFAULT 0,
        clean_sheets INTEGER DEFAULT 0,
        goals_conceded INTEGER DEFAULT 0,
        own_goals INTEGER DEFAULT 0,
        penalties_saved INTEGER DEFAULT 0,
        penalties_missed INTEGER DEFAULT 0,
        yellow_cards INTEGER DEFAULT 0,
        red_cards INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0,
        bonus INTEGER DEFAULT 0,
        bps INTEGER DEFAULT 0,
        influence DECIMAL DEFAULT 0,
        creativity DECIMAL DEFAULT 0,
        threat DECIMAL DEFAULT 0,
        ict_index DECIMAL DEFAULT 0,
        value INTEGER DEFAULT 50,
        selected DECIMAL DEFAULT 0,
        transfers_in INTEGER DEFAULT 0,
        transfers_out INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(season, gameweek, fpl_player_id)
    );

    -- Historical fixtures data
    CREATE TABLE IF NOT EXISTS historical_fixtures (
        id SERIAL PRIMARY KEY,
        season VARCHAR(10) NOT NULL,
        gameweek INTEGER,
        fpl_fixture_id INTEGER,
        team_h INTEGER,
        team_a INTEGER,
        team_h_score INTEGER,
        team_a_score INTEGER,
        finished BOOLEAN DEFAULT FALSE,
        kickoff_time TIMESTAMP,
        team_h_difficulty INTEGER,
        team_a_difficulty INTEGER,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(season, fpl_fixture_id)
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_historical_stats_player ON historical_player_stats(fpl_player_id);
    CREATE INDEX IF NOT EXISTS idx_historical_stats_season_gw ON historical_player_stats(season, gameweek);
    CREATE INDEX IF NOT EXISTS idx_historical_stats_season ON historical_player_stats(season);
    CREATE INDEX IF NOT EXISTS idx_historical_fixtures_season ON historical_fixtures(season, gameweek);
    CREATE INDEX IF NOT EXISTS idx_historical_fixtures_teams ON historical_fixtures(team_h, team_a);
    '''
    
    print("📝 Run this SQL in your Supabase SQL Editor:")
    print("=" * 60)
    print(sql)
    print("=" * 60)

def collect_all_historical_data():
    """Collect all historical data with user confirmation"""
    print("About to collect comprehensive FPL historical data:")
    print("   • 5 seasons (2020-21 to 2024-25)")
    print("   • ~95,000 player performance records")
    print("   • ~2,000 fixture records")
    print("   • Estimated time: 15-20 minutes")
    
    confirm = input("Continue with full data collection? (y/n): ")
    
    if confirm.lower() == 'y':
        collect_historical_gameweek_data()
        collect_historical_fixtures()
        collect_injury_suspension_data()
        print("Complete historical data collection finished!")
    else:
        print("Data collection cancelled")

def validate_collected_data():
    """Validate the collected historical data"""
    print("Validating collected data...")
    
    try:
        result = supabase.table('historical_player_stats').select('season', count='exact').execute()
        player_stats_count = result.count if result.count else 0
        
        print(f"Historical player stats: {player_stats_count} records")
        
        seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]
        for season in seasons:
            season_result = supabase.table('historical_player_stats').select('*', count='exact').eq('season', season).execute()
            count = season_result.count if season_result.count else 0
            print(f"   {season}: {count} records")
        
        fixtures_result = supabase.table('historical_fixtures').select('season', count='exact').execute()
        fixtures_count = fixtures_result.count if fixtures_result.count else 0
        
        print(f"Historical fixtures: {fixtures_count} records")
        
        expected_stats = 95000
        expected_fixtures = 1900
        
        print(f"Data Collection Summary:")
        print(f"   Player Stats: {player_stats_count:,} / {expected_stats:,} expected ({(player_stats_count/expected_stats*100):.1f}%)")
        print(f"   Fixtures: {fixtures_count:,} / {expected_fixtures:,} expected ({(fixtures_count/expected_fixtures*100):.1f}%)")
        
        if player_stats_count > 50000:
            print("SUCCESS: Sufficient data for ML training!")
        else:
            print("Warning: May need more data for robust ML models")
            
    except Exception as e:
        print(f"Error validating data: {e}")

def analyze_data_quality():
    """Analyze the quality of collected data"""
    print("Analyzing data quality...")
    
    try:
        result = supabase.table('historical_player_stats').select('*').limit(1000).execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            
            print(f"Data Quality Report (sample of {len(df)} records):")
            print(f"   Missing minutes: {df['minutes'].isna().sum()} records")
            print(f"   Zero points games: {(df['total_points'] == 0).sum()} records")
            print(f"   Average points per game: {df['total_points'].mean():.2f}")
            
            if 'element_type' in df.columns:
                print(f"   Position distribution:")
                pos_dist = df['element_type'].value_counts()
                for pos, count in pos_dist.items():
                    print(f"     Position {pos}: {count} records")
        
    except Exception as e:
        print(f"Error analyzing data quality: {e}")

if __name__ == "__main__":
    print("FPL Historical Data Collector")
    print("=" * 40)
    print("Collecting 5 seasons of FPL data for ML training")
    print("Data: 2020-21 through 2024-25 seasons")
    print("Expected: ~95,000 player records + fixtures")
    print("=" * 40)
    
    print("\nSTEP 1: Database Setup")
    print("First, create the database tables...")
    
    create_historical_tables()
    
    print("\nIMPORTANT: Run the SQL above in your Supabase SQL Editor!")
    input("Press Enter after creating the database tables...")
    
    print("\nSTEP 2: Historical Data Collection")
    collect_all_historical_data()
    
    print("\nSTEP 3: Data Validation")
    validate_collected_data()
    
    print("\nSTEP 4: Data Quality Analysis")
    analyze_data_quality()
    
    print("\n" + "="*50)
    print("HISTORICAL DATA COLLECTION COMPLETE!")
    print("Next steps:")
    print("   1. Create feature_engineer.py for ML features")
    print("   2. Create ml_trainer.py for model training")
    print("   3. Create ai_predictor.py for AI predictions")
    print("=" * 50)
