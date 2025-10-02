import requests 

import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")


if API_KEY is None:
    raise ValueError("API Key not found. Ensure you have a .env file.")

# Team information
urlTeams = "https://api.football-data.org/v4/competitions/PL/teams"
# Team fixtures
urlMatches = "https://api.football-data.org/v4/competitions/PL/matches"
# League Standings
urlStandings =  "http://api.football-data.org/v4/competitions/PL/standings"
# Fantasy Stats - Main comprehensive data (teams, players, gameweeks, etc.)
urlFantasy = "https://fantasy.premierleague.com/api/bootstrap-static/"
# Individual player detailed stats (requires player ID)
urlPlayerDetails = "https://fantasy.premierleague.com/api/element-summary/{player_id}/"
# Fixture data with player stats
urlFixtures = "https://fantasy.premierleague.com/api/fixtures/"
# Live gameweek data with player points
urlLiveGameweek = "https://fantasy.premierleague.com/api/event/{gameweek}/live/"

# Test code to ensure endpoints return correct information
headers = {"X-Auth-Token": API_KEY}
response = requests.get(urlFixtures, headers=headers)

# if response.status_code == 200:
#     data = response.json()
#     print(data)
# else:
#     print("Error:", response.status_code, response.text)

# Create a mapping between football-data.org and the FPL API
def create_team_mapping():

    # Get FPL team data
    fplResponse = requests.get(urlFantasy)
    if fplResponse.status_code != 200:
        raise Exception(f"Failed to get data from FPL API: {fplResponse.status_code}")

    fplData = fplResponse.json()
    fplTeams = {team['name']: team['id'] for team in fplData['teams']}

    # Get football-data.org teams
    headers = {"X-Auth-Token": API_KEY}    
    fdResponse = requests.get(urlTeams, headers=headers)
    if fdResponse.status_code != 200:
        raise Exception(f"Failed to get data from FPL API: {fdResponse.status_code}")
    
    fdData = fdResponse.json()
    fdTeams = {team['name']: team['id'] for team in fdData['teams']}

    # Manuel mapping teams with different names between APIs
    nameMapping = {
        'Brighton & Hove Albion FC': 'Brighton',
        'Newcastle United FC': 'Newcastle',
        'Manchester United FC': 'Man Utd',
        'Manchester City FC': 'Man City',
        'Tottenham Hotspur FC': 'Spurs',
        'Nottingham Forest FC': "Nott'm Forest",
        'Sunderland AFC': 'Sunderland',
        'West Ham United FC': 'West Ham',
        'Wolverhampton Wanderers FC': 'Wolves',
        'Arsenal FC': 'Arsenal',
        'Aston Villa FC': 'Aston Villa',
        'Chelsea FC': 'Chelsea',
        'Everton FC': 'Everton',
        'Fulham FC': 'Fulham',
        'Liverpool FC': 'Liverpool',
        'Crystal Palace FC': 'Crystal Palace',
        'Brentford FC': 'Brentford',
        'AFC Bournemouth': 'Bournemouth',
        'Burnley FC': 'Burnley',
        'Leeds United FC': 'Leeds'
    }

    # Create the mapping dictionary
    teamMapping = {}
    for fdName, fdID in fdTeams.items():
        # Try direct name match first
        if fdName in fplTeams:
            teamMapping[fdID] = fplTeams[fdName]
        # Try mapped name
        elif fdName in nameMapping and nameMapping[fdName] in fplTeams:
            teamMapping[fdID] = fplTeams[nameMapping[fdName]]
        else:
            print(f"Warning: Could not map team {fdName}")
    
    return teamMapping

def get_fpl_team_id(fd_team_id):
    # Convert football-data.org team ID to FPL team ID
    return TEAM_MAPPING.get(fd_team_id)

def get_fd_team_id(fpl_team_id):
    # Convert FPL team ID to football-data.org team ID
    reverse_mapping = {v: k for k, v in TEAM_MAPPING.items()}
    return reverse_mapping.get(fpl_team_id)

# Initialize the mapping
TEAM_MAPPING = create_team_mapping()
print(f"Successfully created mapping for {len(TEAM_MAPPING)} teams")
print("Team mapping:", TEAM_MAPPING)

fplID = get_fpl_team_id(57)
print(fplID)
def create_player_mapping():
    
    # Creates a mapping between football-data.org players and FPL players
    # Returns: Dictionary mapping fd_player_id -> fpl_player_id
    
    # Get player data from FPL bootstrap (contains all players)
    fplResponse = requests.get(urlFantasy)
    if fplResponse.status_code != 200:
         raise Exception(f"Failed to get data from FPL API: {fplResponse.status_code}")
    
    fplData = fplResponse.json()
    fplPlayers = fplData['elements']  # All FPL players
    
    # Create FPL player lookup by team and name
    fplPlayerLookup = {}
    for player in fplPlayers:
        team_id = player['team']
        # Create multiple name variations for matching
        full_name = f"{player['first_name']} {player['second_name']}".strip()
        web_name = player['web_name']
        
        if team_id not in fplPlayerLookup:
            fplPlayerLookup[team_id] = {}
        
        # Store player under multiple name formats for better matching
        name_variations = [
            full_name.lower(),
            web_name.lower(),
            player['second_name'].lower(),
            player['first_name'].lower(),
            # Handle common name formats
            f"{player['first_name'][0].lower()}. {player['second_name'].lower()}",
            # Remove accents and special characters
            full_name.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        ]
        
        for name_var in name_variations:
            if name_var.strip():  # Only add non-empty names
                fplPlayerLookup[team_id][name_var] = player['id']
    
    # Get team data from football-data.org (needed for player-team mapping)
    headers = {"X-Auth-Token": API_KEY}
    fdResponse = requests.get(urlTeams, headers=headers)
    if fdResponse.status_code != 200:
        raise Exception(f"Failed to get data from football-data.org API: {fdResponse.status_code}")
    
    fdTeams = fdResponse.json()['teams']
    
    # Get player data from each team's squad
    playerMapping = {}
    
    for team in fdTeams:
        fd_team_id = team['id']
        fpl_team_id = get_fpl_team_id(fd_team_id)
        
        if not fpl_team_id:
            print(f"Warning: No FPL mapping for team {team['name']}")
            continue
            
        # Get squad for this team with retry logic
        squadUrl = f"https://api.football-data.org/v4/teams/{fd_team_id}"
        
        import time
        time.sleep(1.5)  # Longer delay to avoid rate limiting (max 10 requests per minute)
        
        squadResponse = requests.get(squadUrl, headers=headers)
        
        if squadResponse.status_code != 200:
            print(f"Warning: Failed to get squad for team {team['name']} (Status: {squadResponse.status_code})")
            continue
            
        squadData = squadResponse.json()
        fdPlayers = squadData.get('squad', [])
        
        # Match players between APIs
        for fdPlayer in fdPlayers:
            fd_player_id = fdPlayer['id']
            fd_player_name = fdPlayer['name'].lower()
            
            # Try to find matching FPL player with improved matching
            fpl_player_id = None
            if fpl_team_id in fplPlayerLookup:
                team_players = fplPlayerLookup[fpl_team_id]
                
                # Clean the football-data name for better matching
                clean_fd_name = fd_player_name.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                
                # Try exact name match first
                if clean_fd_name in team_players:
                    fpl_player_id = team_players[clean_fd_name]
                elif fd_player_name in team_players:
                    fpl_player_id = team_players[fd_player_name]
                else:
                    # Try partial matches with better logic
                    fd_name_parts = clean_fd_name.split()
                    
                    for fpl_name, fpl_id in team_players.items():
                        fpl_parts = fpl_name.split()
                        
                        # Check if last names match (most reliable)
                        if len(fd_name_parts) > 0 and len(fpl_parts) > 0:
                            if fd_name_parts[-1] == fpl_parts[-1]:
                                fpl_player_id = fpl_id
                                break
                        
                        # Check if any significant part matches (length > 3)
                        for fd_part in fd_name_parts:
                            if len(fd_part) > 3 and fd_part in fpl_name:
                                fpl_player_id = fpl_id
                                break
                        if fpl_player_id:
                            break
            
            if fpl_player_id:
                playerMapping[fd_player_id] = fpl_player_id
            else:
                print(f"Warning: Could not match player {fdPlayer['name']} from {team['name']}")
    
    return playerMapping

def get_fpl_player_id(fd_player_id):
    """Convert football-data.org player ID to FPL player ID"""
    return PLAYER_MAPPING.get(fd_player_id)

def get_fd_player_id(fpl_player_id):
    """Convert FPL player ID to football-data.org player ID"""
    reverse_mapping = {v: k for k, v in PLAYER_MAPPING.items()}
    return reverse_mapping.get(fpl_player_id)

def get_combined_player_data(fpl_player_id):
    """
    Get combined data for a player from both APIs
    Returns: Dictionary with FPL and football-data.org stats
    """
    # Get FPL data
    fplResponse = requests.get(urlFantasy)
    if fplResponse.status_code == 200:
        fplData = fplResponse.json()
        fpl_player = next((p for p in fplData['elements'] if p['id'] == fpl_player_id), None)
        
        if fpl_player:
            # Get corresponding football-data player
            fd_player_id = get_fd_player_id(fpl_player_id)
            
            combined_data = {
                'fpl_data': fpl_player,
                'fd_player_id': fd_player_id,
                'player_name': f"{fpl_player['first_name']} {fpl_player['second_name']}",
                'team_name': next((t['name'] for t in fplData['teams'] if t['id'] == fpl_player['team']), 'Unknown')
            }
            
            return combined_data
    
    return None

# Initialize the player mapping
print("Creating player mapping... This may take a moment.")
PLAYER_MAPPING = create_player_mapping()
print(f"Successfully created mapping for {len(PLAYER_MAPPING)} players")

# Test the mapping
if PLAYER_MAPPING:
    first_mapping = next(iter(PLAYER_MAPPING.items()))
    print(f"Sample mapping: FD Player ID {first_mapping[0]} -> FPL Player ID {first_mapping[1]}")
    
    # Test combined data function
    sample_data = get_combined_player_data(first_mapping[1])
    if sample_data:
        print(f"Sample player: {sample_data['player_name']} from {sample_data['team_name']}")

