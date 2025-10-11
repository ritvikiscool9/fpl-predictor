#!/usr/bin/env python3
"""
Populate database with fresh FPL data
"""

import requests
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def populate_fresh_fpl_data():
    """Get fresh FPL data and populate database"""
    
    print("Fetching fresh FPL data from API...")
    
    # Get FPL data
    response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    if response.status_code != 200:
        raise Exception(f"Failed to get FPL data: {response.status_code}")
    
    data = response.json()
    
    # Save gameweek info
    print("Saving gameweek information...")
    for gw in data['events']:
        supabase.table('gameweeks').upsert({
            'gameweek_number': gw['id'],
            'season': '2025-26',
            'name': gw.get('name', f"Gameweek {gw['id']}"),
            'deadline_time': gw.get('deadline_time'),
            'is_finished': gw.get('finished', False),
            'is_current': gw.get('is_current', False),
            'average_entry_score': gw.get('average_entry_score', 0),
            'highest_score': gw.get('highest_score', 0)
        }, on_conflict='gameweek_number,season').execute()
    
    # Find current gameweek
    current_gameweek = None
    current_gameweek_db_id = None
    
    for event in data['events']:
        if event.get('is_current', False):
            current_gameweek = event['id']
            # Save current gameweek to current_season table
            supabase.table('current_season').upsert({
                'season': '2025-26',
                'current_gameweek': current_gameweek,
                'is_active': True,
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            # Get gameweek database ID
            gw_result = supabase.table('gameweeks').select('id').eq('gameweek_number', current_gameweek).eq('season', '2025-26').execute()
            if gw_result.data:
                current_gameweek_db_id = gw_result.data[0]['id']
            break
    
    if not current_gameweek_db_id:
        print("Warning: Could not find current gameweek, using gameweek 8")
        # Fallback to a reasonable gameweek
        gw_result = supabase.table('gameweeks').select('id').eq('gameweek_number', 8).eq('season', '2025-26').execute()
        if gw_result.data:
            current_gameweek_db_id = gw_result.data[0]['id']
        else:
            # Create gameweek 8 if it doesn't exist
            gw_insert = supabase.table('gameweeks').insert({
                'gameweek_number': 8,
                'season': '2025-26',
                'name': 'Gameweek 8',
                'is_current': True
            }).execute()
            current_gameweek_db_id = gw_insert.data[0]['id']
    
    # Save current player stats
    print(f"Saving current stats for {len(data['elements'])} players...")
    saved_count = 0
    
    for player in data['elements']:
        # Get player database ID
        player_result = supabase.table('players').select('id').eq('fpl_player_id', player['id']).execute()
        if not player_result.data:
            print(f"Warning: Player {player['id']} not found in database")
            continue
            
        player_db_id = player_result.data[0]['id']
        
        # Save current stats
        try:
            supabase.table('current_player_stats').upsert({
                'player_id': player_db_id,
                'gameweek_id': current_gameweek_db_id,
                'total_points': player.get('total_points', 0),
                'minutes': player.get('minutes', 0),
                'goals_scored': player.get('goals_scored', 0),
                'assists': player.get('assists', 0),
                'clean_sheets': player.get('clean_sheets', 0),
                'goals_conceded': player.get('goals_conceded', 0),
                'own_goals': player.get('own_goals', 0),
                'penalties_saved': player.get('penalties_saved', 0),
                'penalties_missed': player.get('penalties_missed', 0),
                'yellow_cards': player.get('yellow_cards', 0),
                'red_cards': player.get('red_cards', 0),
                'saves': player.get('saves', 0),
                'bonus': player.get('bonus', 0),
                'bps': player.get('bps', 0),
                'influence': float(player.get('influence', 0)),
                'creativity': float(player.get('creativity', 0)),
                'threat': float(player.get('threat', 0)),
                'ict_index': float(player.get('ict_index', 0)),
                'now_cost': player.get('now_cost', 50),
                'selected_by_percent': float(player.get('selected_by_percent', 0)),
                'transfers_in': player.get('transfers_in', 0),
                'transfers_out': player.get('transfers_out', 0),
                'form': float(player.get('form', 0)),
                'points_per_game': float(player.get('points_per_game', 0)),
                'status': player.get('status', 'a'),
                'news': player.get('news', ''),
                'chance_of_playing_this_round': player.get('chance_of_playing_this_round'),
                'chance_of_playing_next_round': player.get('chance_of_playing_next_round'),
                'data_updated_at': datetime.now().isoformat()
            }, on_conflict='player_id,gameweek_id').execute()
            saved_count += 1
        except Exception as e:
            print(f"Error saving player {player['id']}: {e}")
            continue
            
    print(f"✅ Successfully populated database with fresh FPL data!")
    print(f"   - {len(data['events'])} gameweeks")
    print(f"   - Current gameweek: {current_gameweek}")
    print(f"   - {saved_count} player stats updated")

if __name__ == "__main__":
    populate_fresh_fpl_data()