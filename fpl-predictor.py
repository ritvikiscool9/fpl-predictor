import requests 

import requests
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

# Cache settings
CACHE_DIR = "cache"
TEAM_MAPPING_CACHE = os.path.join(CACHE_DIR, "team_mapping.json")
PLAYER_MAPPING_CACHE = os.path.join(CACHE_DIR, "player_mapping.json")
FPL_DATA_CACHE = os.path.join(CACHE_DIR, "fpl_data.json")
CACHE_DURATION_HOURS = 24  # Cache data for 24 hours

# Create cache directory if it doesn't exist
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


if API_KEY is None:
    raise ValueError("API Key not found. Ensure you have a .env file.")

# Cache utility functions
def save_to_cache(data, cache_file):
    """Save data to cache with timestamp"""
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f)
    print(f"Data cached to {cache_file}")

def load_from_cache(cache_file, max_age_hours=CACHE_DURATION_HOURS):
    """Load data from cache if it's still fresh"""
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is still valid
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        if datetime.now() - cache_time < timedelta(hours=max_age_hours):
            print(f"Loading fresh data from cache: {cache_file}")
            return cache_data['data']
        else:
            print(f"Cache expired for {cache_file}")
            return None
    except Exception as e:
        print(f"Error reading cache {cache_file}: {e}")
        return None

def is_cache_valid(cache_file, max_age_hours=CACHE_DURATION_HOURS):
    """Check if cache file exists and is still valid"""
    return load_from_cache(cache_file, max_age_hours) is not None

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

# Create a mapping between football-data.org and the FPL API
def create_team_mapping():
    """Create team mapping with caching to avoid repeated API calls"""
    
    # Try to load from cache first
    cached_mapping = load_from_cache(TEAM_MAPPING_CACHE)
    if cached_mapping is not None:
        return cached_mapping

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
    
    # Save to cache before returning
    save_to_cache(teamMapping, TEAM_MAPPING_CACHE)
    return teamMapping

def get_fpl_team_id(fd_team_id):
    # Convert football-data.org team ID to FPL team ID
    # Handle both integer and string keys from cache
    return TEAM_MAPPING.get(fd_team_id) or TEAM_MAPPING.get(str(fd_team_id))

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
    """
    Creates a mapping between football-data.org players and FPL players
    Returns: Dictionary mapping fd_player_id -> fpl_player_id
    """
    
    # Try to load from cache first
    cached_mapping = load_from_cache(PLAYER_MAPPING_CACHE)
    if cached_mapping is not None:
        return cached_mapping
    
    print("Building fresh player mapping from APIs...")
    
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
    total_teams = len(fdTeams)
    processed_teams = 0
    
    print(f"Processing {total_teams} teams for player mapping...")
    
    for team in fdTeams:
        fd_team_id = team['id']
        fpl_team_id = get_fpl_team_id(fd_team_id)
        
        if not fpl_team_id:
            print(f"Warning: No FPL mapping for team {team['name']}")
            continue
            
        # Get squad for this team with retry logic
        squadUrl = f"https://api.football-data.org/v4/teams/{fd_team_id}"
        
        import time
        time.sleep(6.5)  # Wait 6.5 seconds between requests (safer for 10 req/min limit)
        
        max_retries = 3
        retry_count = 0
        squadResponse = None
        
        while retry_count < max_retries:
            squadResponse = requests.get(squadUrl, headers=headers)
            
            if squadResponse.status_code == 200:
                break
            elif squadResponse.status_code == 429:  # Rate limit
                wait_time = (retry_count + 1) * 15  # Wait 15, 30, 45 seconds
                print(f"Rate limit hit for {team['name']}, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                retry_count += 1
            else:
                print(f"Warning: Failed to get squad for team {team['name']} (Status: {squadResponse.status_code})")
                break
        
        if squadResponse is None or squadResponse.status_code != 200:
            print(f"Skipping team {team['name']} after {retry_count} retries")
            processed_teams += 1
            print(f"Progress: {processed_teams}/{total_teams} teams processed")
            continue
            
        squadData = squadResponse.json()
        fdPlayers = squadData.get('squad', [])
        
        # Match players between APIs
        matched_count = 0
        total_players = len(fdPlayers)
        
        for fdPlayer in fdPlayers:
            fd_player_id = fdPlayer['id']
            fd_player_name = fdPlayer['name'].lower()
            player_position = fdPlayer.get('position', 'Unknown')
            
            # Skip obvious non-FPL players (youth/academy players, etc.)
            skip_keywords = ['u18', 'u19', 'u21', 'u23', 'academy', 'youth', 'development']
            if any(keyword in fd_player_name for keyword in skip_keywords):
                continue
                
            # Skip players who are likely loans or not in FPL (common patterns)
            likely_non_fpl = ['russ oakley', 'aidan borland', 'max merrick', 'ted curd', 
                            'reggie walsh', 'shumaira mheuka', 'ollie harrison', 
                            'kieran morrison', 'tommy pilling', 'kaden braithwaite',
                            'jaden heskey', 'reigan heskey', 'max thompson']
            if fd_player_name in likely_non_fpl:
                continue
            
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
                    best_match = None
                    best_score = 0
                    
                    for fpl_name, fpl_id in team_players.items():
                        fpl_parts = fpl_name.split()
                        match_score = 0
                        
                        # Check if last names match (most reliable) - high score
                        if len(fd_name_parts) > 0 and len(fpl_parts) > 0:
                            if fd_name_parts[-1] == fpl_parts[-1]:
                                match_score += 10
                        
                        # Check for first name match
                        if len(fd_name_parts) > 0 and len(fpl_parts) > 0:
                            if fd_name_parts[0] == fpl_parts[0]:
                                match_score += 5
                        
                        # Check if any significant part matches (length > 3)
                        for fd_part in fd_name_parts:
                            if len(fd_part) > 3 and fd_part in fpl_name:
                                match_score += 3
                        
                        # Update best match if this one is better
                        if match_score > best_score and match_score >= 8:  # Require decent confidence
                            best_match = fpl_id
                            best_score = match_score
                    
                    fpl_player_id = best_match
            
            if fpl_player_id:
                playerMapping[fd_player_id] = fpl_player_id
                matched_count += 1
            else:
                # Only show warning for likely first-team players
                if player_position in ['Goalkeeper', 'Centre-Back', 'Left-Back', 'Right-Back', 
                                     'Defensive Midfield', 'Central Midfield', 'Attacking Midfield',
                                     'Left Winger', 'Right Winger', 'Centre-Forward']:
                    print(f"Warning: Could not match player {fdPlayer['name']} ({player_position}) from {team['name']}")
        
        if total_players > 0:
            match_rate = (matched_count / total_players) * 100
            processed_teams += 1
            print(f"Team {team['name']}: Matched {matched_count}/{total_players} players ({match_rate:.1f}%)")
            print(f"Progress: {processed_teams}/{total_teams} teams processed")
        else:
            processed_teams += 1
            print(f"No players found for {team['name']}")
            print(f"Progress: {processed_teams}/{total_teams} teams processed")
    
    # Save to cache before returning
    save_to_cache(playerMapping, PLAYER_MAPPING_CACHE)
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

def get_cached_fpl_data():
    """Get FPL data with caching to reduce API calls"""
    cached_data = load_from_cache(FPL_DATA_CACHE, max_age_hours=6)  # Refresh every 6 hours
    if cached_data is not None:
        return cached_data
    
    print("Fetching fresh FPL data...")
    response = requests.get(urlFantasy)
    if response.status_code == 200:
        data = response.json()
        save_to_cache(data, FPL_DATA_CACHE)
        return data
    else:
        raise Exception(f"Failed to get FPL data: {response.status_code}")

def process_match_data():
    """
    Process upcoming fixtures and recent results for predictions
    Uses primarily FPL data to minimize API calls
    """
    print("Processing match data...")
    
    # Get FPL data (cached)
    fpl_data = get_cached_fpl_data()
    
    # Get fixture data from FPL (free and unlimited)
    fixtures_response = requests.get(urlFixtures)
    if fixtures_response.status_code != 200:
        raise Exception(f"Failed to get fixtures: {fixtures_response.status_code}")
    
    fixtures = fixtures_response.json()
    
    # Process upcoming fixtures
    upcoming_fixtures = []
    completed_fixtures = []
    
    for fixture in fixtures:
        if fixture['finished']:
            completed_fixtures.append(fixture)
        else:
            upcoming_fixtures.append(fixture)
    
    # Analyze team form from recent fixtures
    team_form = analyze_team_form(completed_fixtures[-50:])  # Last 50 completed games
    
    # Analyze fixture difficulty
    fixture_analysis = analyze_fixture_difficulty(upcoming_fixtures[:38])  # Next 38 games
    
    return {
        'upcoming_fixtures': upcoming_fixtures,
        'completed_fixtures': completed_fixtures,
        'team_form': team_form,
        'fixture_difficulty': fixture_analysis,
        'fpl_data': fpl_data
    }

def analyze_team_form(recent_fixtures):
    """Analyze recent team performance"""
    team_stats = {}
    
    for fixture in recent_fixtures:
        home_team = fixture['team_h']
        away_team = fixture['team_a']
        
        # Initialize team stats if not exists
        for team in [home_team, away_team]:
            if team not in team_stats:
                team_stats[team] = {
                    'games_played': 0,
                    'wins': 0,
                    'draws': 0,
                    'losses': 0,
                    'goals_for': 0,
                    'goals_against': 0,
                    'clean_sheets': 0
                }
        
        # Update stats based on fixture result
        home_score = fixture['team_h_score']
        away_score = fixture['team_a_score']
        
        if home_score is not None and away_score is not None:
            # Update games played
            team_stats[home_team]['games_played'] += 1
            team_stats[away_team]['games_played'] += 1
            
            # Update goals
            team_stats[home_team]['goals_for'] += home_score
            team_stats[home_team]['goals_against'] += away_score
            team_stats[away_team]['goals_for'] += away_score
            team_stats[away_team]['goals_against'] += home_score
            
            # Update win/draw/loss
            if home_score > away_score:
                team_stats[home_team]['wins'] += 1
                team_stats[away_team]['losses'] += 1
            elif away_score > home_score:
                team_stats[away_team]['wins'] += 1
                team_stats[home_team]['losses'] += 1
            else:
                team_stats[home_team]['draws'] += 1
                team_stats[away_team]['draws'] += 1
            
            # Update clean sheets
            if home_score == 0:
                team_stats[away_team]['clean_sheets'] += 1
            if away_score == 0:
                team_stats[home_team]['clean_sheets'] += 1
    
    return team_stats

def analyze_fixture_difficulty(upcoming_fixtures):
    """Analyze upcoming fixture difficulty for each team"""
    fixture_difficulty = {}
    
    for fixture in upcoming_fixtures:
        home_team = fixture['team_h']
        away_team = fixture['team_a']
        difficulty_h = fixture.get('team_h_difficulty', 3)  # Default difficulty
        difficulty_a = fixture.get('team_a_difficulty', 3)
        
        # Initialize if not exists
        for team in [home_team, away_team]:
            if team not in fixture_difficulty:
                fixture_difficulty[team] = {
                    'next_5_fixtures': [],
                    'avg_difficulty': 0,
                    'home_games': 0,
                    'away_games': 0
                }
        
        # Add fixture info
        if len(fixture_difficulty[home_team]['next_5_fixtures']) < 5:
            fixture_difficulty[home_team]['next_5_fixtures'].append({
                'opponent': away_team,
                'is_home': True,
                'difficulty': difficulty_h
            })
            fixture_difficulty[home_team]['home_games'] += 1
        
        if len(fixture_difficulty[away_team]['next_5_fixtures']) < 5:
            fixture_difficulty[away_team]['next_5_fixtures'].append({
                'opponent': home_team,
                'is_home': False,
                'difficulty': difficulty_a
            })
            fixture_difficulty[away_team]['away_games'] += 1
    
    # Calculate average difficulty
    for team, data in fixture_difficulty.items():
        if data['next_5_fixtures']:
            avg_diff = sum(f['difficulty'] for f in data['next_5_fixtures']) / len(data['next_5_fixtures'])
            data['avg_difficulty'] = round(avg_diff, 2)
    
    return fixture_difficulty

# Test the match data processing
print("\n" + "="*50)
print("Testing Match Data Processing...")
try:
    match_data = process_match_data()
    print(f"Found {len(match_data['upcoming_fixtures'])} upcoming fixtures")
    print(f"Found {len(match_data['completed_fixtures'])} completed fixtures")
    print(f"Analyzed form for {len(match_data['team_form'])} teams")
    print(f"Fixture difficulty calculated for {len(match_data['fixture_difficulty'])} teams")
    
    # Show sample team form
    if match_data['team_form']:
        sample_team = list(match_data['team_form'].keys())[0]
        form = match_data['team_form'][sample_team]
        print(f"\nSample team form (Team {sample_team}):")
        print(f"  Games: {form['games_played']}, Wins: {form['wins']}, Clean Sheets: {form['clean_sheets']}")
        
    # Show sample fixture difficulty
    if match_data['fixture_difficulty']:
        sample_team = list(match_data['fixture_difficulty'].keys())[0]
        difficulty = match_data['fixture_difficulty'][sample_team]
        print(f"\nSample fixture difficulty (Team {sample_team}):")
        print(f"  Next 5 games avg difficulty: {difficulty['avg_difficulty']}")
        
except Exception as e:
    print(f"Error processing match data: {e}")

# =============================================================================
# PREDICTION MODEL STRUCTURE
# =============================================================================

def calculate_player_form_score(player, recent_gameweeks=5):
    """
    Calculate a player's recent form score based on FPL points
    Returns score between 0-10 (10 = excellent form)
    """
    # Get player's recent performances (this would need historical data)
    # For now, use current season stats as proxy
    
    total_points = player.get('total_points', 0)
    games_played = player.get('minutes', 0) / 90  # Rough games estimate
    
    if games_played == 0:
        return 0
    
    points_per_game = total_points / max(games_played, 1)
    
    # Normalize to 0-10 scale based on position
    position = player.get('element_type', 1)
    
    # Expected points per game by position (more realistic estimates)
    position_benchmarks = {
        1: 2.5,  # Goalkeepers - lower baseline
        2: 3.0,  # Defenders  
        3: 3.5,  # Midfielders
        4: 4.0   # Forwards
    }
    
    benchmark = position_benchmarks.get(position, 3.5)
    form_score = min(10, (points_per_game / benchmark) * 8)  # More generous scaling
    
    return round(form_score, 2)

def calculate_fixture_favorability(team_id, fixture_difficulty_data):
    """
    Calculate how favorable upcoming fixtures are for a team
    Returns score between 0-10 (10 = very easy fixtures)
    """
    if team_id not in fixture_difficulty_data:
        return 5  # Neutral if no data
    
    team_fixtures = fixture_difficulty_data[team_id]
    avg_difficulty = team_fixtures.get('avg_difficulty', 3)
    
    # Convert difficulty to favorability (lower difficulty = higher favorability)
    # FPL difficulty: 1=easy, 5=hard
    favorability = 6 - avg_difficulty  # Inverts scale
    favorability = max(1, min(10, favorability * 2))  # Scale to 1-10
    
    return round(favorability, 2)

def calculate_team_strength_score(team_id, team_form_data):
    """
    Calculate overall team strength based on recent form
    Returns score between 0-10
    """
    if team_id not in team_form_data:
        return 5  # Neutral if no data
    
    form = team_form_data[team_id]
    games = form.get('games_played', 1)
    
    if games == 0:
        return 5
    
    # Calculate various strength metrics
    win_rate = form.get('wins', 0) / games
    goals_per_game = form.get('goals_for', 0) / games
    clean_sheet_rate = form.get('clean_sheets', 0) / games
    goals_against_per_game = form.get('goals_against', 0) / games
    
    # Weighted strength score
    attacking_strength = min(10, goals_per_game * 2.5)  # Scale goals to 0-10
    defensive_strength = min(10, clean_sheet_rate * 10)  # Clean sheets to 0-10
    general_form = win_rate * 10
    
    # Penalty for conceding goals
    defensive_penalty = min(5, goals_against_per_game * 2)
    
    overall_strength = (attacking_strength + defensive_strength + general_form - defensive_penalty) / 3
    
    return round(max(0, min(10, overall_strength)), 2)

def predict_player_points(player, match_data, position_multipliers=None):
    """
    Predict FPL points for a player in upcoming gameweek
    
    Args:
        player: FPL player data
        match_data: Processed match data including form and fixtures
        position_multipliers: Optional position-specific adjustments
        
    Returns:
        Dictionary with prediction details
    """
    if position_multipliers is None:
        position_multipliers = {1: 0.8, 2: 0.9, 3: 1.1, 4: 1.2}  # GK, DEF, MID, FWD
    
    player_id = player['id']
    team_id = player['team']
    position = player['element_type']
    
    # Base metrics
    form_score = calculate_player_form_score(player)
    fixture_favorability = calculate_fixture_favorability(team_id, match_data['fixture_difficulty'])
    team_strength = calculate_team_strength_score(team_id, match_data['team_form'])
    
    # Player-specific factors
    minutes_likelihood = min(1.0, player.get('minutes', 0) / (38 * 90 * 0.7))  # Likelihood to play
    price_value = player.get('now_cost', 50) / 10  # Price in millions
    ownership = float(player.get('selected_by_percent', '5.0'))
    
    # Calculate base prediction (scale to realistic FPL points range)
    base_prediction = (form_score * 0.4 + 
                      fixture_favorability * 0.3 + 
                      team_strength * 0.3) * 0.8  # Scale to ~2-8 point range
    
    # Add position baseline points
    position_baselines = {1: 2.0, 2: 2.5, 3: 3.0, 4: 3.5}  # Minimum expected points
    base_prediction += position_baselines.get(position, 3.0)
    
    # Apply position multiplier
    position_adjusted = base_prediction * position_multipliers.get(position, 1.0)
    
    # Apply minutes likelihood (but not too harsh)
    minutes_adjusted = position_adjusted * max(0.5, minutes_likelihood)
    
    # Injury/suspension check (basic)
    availability_multiplier = 1.0
    if player.get('status') != 'a':  # 'a' = available
        availability_multiplier = 0.3
    
    final_prediction = minutes_adjusted * availability_multiplier
    
    # Risk assessment
    risk_factors = []
    if minutes_likelihood < 0.7:
        risk_factors.append("Rotation risk")
    if ownership > 25:
        risk_factors.append("High ownership")
    if player.get('status') != 'a':
        risk_factors.append("Injury/suspension concern")
    
    return {
        'player_id': player_id,
        'name': f"{player['first_name']} {player['second_name']}",
        'team_id': team_id,
        'position': position,
        'predicted_points': round(final_prediction, 2),
        'confidence': round(min(10, form_score + minutes_likelihood * 5), 1),
        'form_score': form_score,
        'fixture_favorability': fixture_favorability,
        'team_strength': team_strength,
        'price': price_value,
        'ownership': ownership,
        'risk_factors': risk_factors,
        'value_rating': round(final_prediction / price_value, 2) if price_value > 0 else 0
    }

def get_best_players_by_position(match_data, top_n=5):
    """
    Get top predicted players for each position
    """
    fpl_data = match_data['fpl_data']
    players = fpl_data['elements']
    
    # Group players by position
    position_names = {1: 'Goalkeepers', 2: 'Defenders', 3: 'Midfielders', 4: 'Forwards'}
    best_players = {}
    
    for position in range(1, 5):
        position_players = [p for p in players if p['element_type'] == position]
        
        # Get predictions for all players in this position
        predictions = []
        for player in position_players:
            try:
                prediction = predict_player_points(player, match_data)
                predictions.append(prediction)
            except Exception as e:
                continue  # Skip problematic players
        
        # Sort by predicted points
        predictions.sort(key=lambda x: x['predicted_points'], reverse=True)
        
        best_players[position_names[position]] = predictions[:top_n]
    
    return best_players

def generate_transfer_recommendations(match_data, budget=1000, top_n=3):
    """
    Generate transfer recommendations based on predictions
    """
    fpl_data = match_data['fpl_data']
    players = fpl_data['elements']
    
    # Get all predictions
    all_predictions = []
    player_ids_seen = set()
    duplicates_found = 0
    
    for player in players:
        try:
            # Check for duplicate players in source data
            player_id = player['id']
            if player_id in player_ids_seen:
                duplicates_found += 1
                print(f"Warning: Duplicate player ID {player_id} found: {player['first_name']} {player['second_name']}")
                continue
            player_ids_seen.add(player_id)
            
            prediction = predict_player_points(player, match_data)
            if prediction['predicted_points'] > 3:  # Only consider decent predictions
                all_predictions.append(prediction)
        except Exception as e:
            continue
    
    if duplicates_found > 0:
        print(f"Found {duplicates_found} duplicate players in FPL data")
    
    # Sort by value rating (points per million)
    all_predictions.sort(key=lambda x: x['value_rating'], reverse=True)
    
    # Filter by budget (price already converted to millions)
    affordable_players = [p for p in all_predictions if p['price'] <= budget/10]
    
    # Debug: print budget info
    print(f"Budget: £{budget/10}m, Total players: {len(all_predictions)}, Affordable: {len(affordable_players)}")
    
    # Create separate sorted lists to avoid mutation issues
    highest_predicted_sorted = sorted(all_predictions.copy(), key=lambda x: x['predicted_points'], reverse=True)
    differential_picks = [p for p in affordable_players if p['ownership'] < 5]
    
    # Remove duplicates by player_id and keep only unique players
    def remove_duplicates(player_list):
        seen_ids = set()
        unique_players = []
        for player in player_list:
            if player['player_id'] not in seen_ids:
                seen_ids.add(player['player_id'])
                unique_players.append(player)
        return unique_players
    
    recommendations = {
        'best_value': remove_duplicates(affordable_players[:top_n]),
        'highest_predicted': remove_duplicates(highest_predicted_sorted[:top_n]),
        'differential_picks': remove_duplicates(differential_picks[:top_n])
    }
    
    return recommendations

def build_optimal_team(match_data, budget=1000):  # £100m budget
    """
    Build optimal 15-player FPL team following all constraints
    
    FPL Rules:
    - 2 Goalkeepers, 5 Defenders, 5 Midfielders, 3 Forwards
    - Max 3 players from same team
    - Budget constraint (default £100m)
    - Starting XI: 1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD
    """
    fpl_data = match_data['fpl_data']
    players = fpl_data['elements']
    teams = {team['id']: team['name'] for team in fpl_data['teams']}
    
    # Get all predictions
    all_predictions = []
    for player in players:
        try:
            prediction = predict_player_points(player, match_data)
            prediction['team_name'] = teams.get(prediction['team_id'], 'Unknown')
            all_predictions.append(prediction)
        except Exception as e:
            continue
    
    # Sort by predicted points within each position
    goalkeepers = sorted([p for p in all_predictions if p['position'] == 1], 
                        key=lambda x: x['predicted_points'], reverse=True)
    defenders = sorted([p for p in all_predictions if p['position'] == 2], 
                      key=lambda x: x['predicted_points'], reverse=True)
    midfielders = sorted([p for p in all_predictions if p['position'] == 3], 
                        key=lambda x: x['predicted_points'], reverse=True)
    forwards = sorted([p for p in all_predictions if p['position'] == 4], 
                     key=lambda x: x['predicted_points'], reverse=True)
    
    # Team selection algorithm with constraints
    def select_squad_with_constraints():
        selected_squad = []
        team_counts = {}
        total_cost = 0
        budget_millions = budget / 10  # Convert to millions
        
        # Position requirements: [position_type, min_required, max_allowed]
        requirements = [
            (goalkeepers, 'GK', 2, 2),
            (defenders, 'DEF', 5, 5), 
            (midfielders, 'MID', 5, 5),
            (forwards, 'FWD', 3, 3)
        ]
        
        # Greedy selection with constraints
        for player_pool, pos_name, min_req, max_req in requirements:
            position_selected = 0
            
            for player in player_pool:
                if position_selected >= max_req:
                    break
                    
                team_id = player['team_id']
                player_cost = player['price']
                
                # Check constraints
                if (total_cost + player_cost <= budget_millions and 
                    team_counts.get(team_id, 0) < 3 and 
                    position_selected < max_req):
                    
                    selected_squad.append(player)
                    team_counts[team_id] = team_counts.get(team_id, 0) + 1
                    total_cost += player_cost
                    position_selected += 1
            
            # Check if we met minimum requirements
            if position_selected < min_req:
                print(f"Warning: Could not select minimum {min_req} {pos_name}s (only got {position_selected})")
        
        return selected_squad, total_cost
    
    squad, total_cost = select_squad_with_constraints()
    
    # Determine best formation and starting XI
    squad_gk = [p for p in squad if p['position'] == 1]
    squad_def = [p for p in squad if p['position'] == 2]
    squad_mid = [p for p in squad if p['position'] == 3] 
    squad_fwd = [p for p in squad if p['position'] == 4]
    
    # Sort each position by predicted points for starting XI selection
    squad_gk.sort(key=lambda x: x['predicted_points'], reverse=True)
    squad_def.sort(key=lambda x: x['predicted_points'], reverse=True)
    squad_mid.sort(key=lambda x: x['predicted_points'], reverse=True)
    squad_fwd.sort(key=lambda x: x['predicted_points'], reverse=True)
    
    # Try different formations and pick best total points
    formations = [
        {'name': '3-4-3', 'def': 3, 'mid': 4, 'fwd': 3},
        {'name': '3-5-2', 'def': 3, 'mid': 5, 'fwd': 2},
        {'name': '4-3-3', 'def': 4, 'mid': 3, 'fwd': 3},
        {'name': '4-4-2', 'def': 4, 'mid': 4, 'fwd': 2},
        {'name': '4-5-1', 'def': 4, 'mid': 5, 'fwd': 1},
        {'name': '5-3-2', 'def': 5, 'mid': 3, 'fwd': 2},
        {'name': '5-4-1', 'def': 5, 'mid': 4, 'fwd': 1}
    ]
    
    best_formation = None
    best_starting_xi = None
    best_bench = None
    best_total_points = 0
    
    for formation in formations:
        if (len(squad_def) >= formation['def'] and 
            len(squad_mid) >= formation['mid'] and 
            len(squad_fwd) >= formation['fwd']):
            
            starting_xi = []
            
            # Add best GK
            starting_xi.extend(squad_gk[:1])
            
            # Add players by formation
            starting_xi.extend(squad_def[:formation['def']])
            starting_xi.extend(squad_mid[:formation['mid']])
            starting_xi.extend(squad_fwd[:formation['fwd']])
            
            # Calculate total predicted points for starting XI
            formation_points = sum(p['predicted_points'] for p in starting_xi)
            
            if formation_points > best_total_points:
                best_total_points = formation_points
                best_formation = formation
                best_starting_xi = starting_xi
                
                # Create bench (remaining players)
                bench = []
                starting_ids = {p['player_id'] for p in starting_xi}
                for player in squad:
                    if player['player_id'] not in starting_ids:
                        bench.append(player)
                best_bench = bench
    
    return {
        'squad': squad,
        'starting_xi': best_starting_xi,
        'bench': best_bench,
        'formation': best_formation,
        'total_cost': total_cost,
        'budget_remaining': (budget/10) - total_cost,
        'predicted_points': best_total_points
    }

# Test the prediction model
print("\n" + "="*60)
print("TESTING PREDICTION MODEL")
print("="*60)

try:
    # Get match data
    match_data = process_match_data()
    
    # Test predictions for top players by position
    print("Getting best predicted players by position...")
    best_players = get_best_players_by_position(match_data, top_n=3)
    
    for position, players in best_players.items():
        print(f"\n🏆 TOP 3 {position.upper()}:")
        for i, player in enumerate(players, 1):
            print(f"  {i}. {player['name']} - {player['predicted_points']} pts "
                  f"(£{player['price']}m, {player['ownership']}% owned)")
    
    # Generate transfer recommendations
    print(f"\n💰 TRANSFER RECOMMENDATIONS (Budget: £10.0m):")
    recommendations = generate_transfer_recommendations(match_data, budget=100)  # £10m budget
    
    if recommendations['best_value']:
        print("\n🎯 Best Value Picks:")
        for i, player in enumerate(recommendations['best_value'][:3], 1):
            print(f"  {i}. {player['name']} - {player['predicted_points']} pts "
                  f"(£{player['price']}m, Value: {player['value_rating']})")
    else:
        print("\n🎯 Best Value Picks: No affordable players found")
    
    if recommendations['highest_predicted']:
        print("\n📈 Highest Predicted Points:")
        highest_list = recommendations['highest_predicted'][:3]  # Take slice first
        for i, player in enumerate(highest_list, 1):
            print(f"  {i}. {player['name']} - {player['predicted_points']} pts "
                  f"(£{player['price']}m, {player['ownership']}% owned)")
    else:
        print("\n📈 Highest Predicted Points: No predictions available")
    
    if recommendations['differential_picks']:
        print("\n🔥 Differential Picks (<5% owned):")
        for i, player in enumerate(recommendations['differential_picks'][:3], 1):
            print(f"  {i}. {player['name']} - {player['predicted_points']} pts "
                  f"(£{player['price']}m, {player['ownership']}% owned)")
    
    # Generate optimal 15-player team
    print("\n" + "="*80)
    print("🏆 OPTIMAL 15-PLAYER TEAM FOR NEXT GAMEWEEK")
    print("="*80)
    
    optimal_team = build_optimal_team(match_data, budget=1000)  # £100m budget
    
    print(f"\n💰 BUDGET: £{optimal_team['total_cost']:.1f}m / £100.0m (£{optimal_team['budget_remaining']:.1f}m remaining)")
    print(f"📊 FORMATION: {optimal_team['formation']['name']}")
    print(f"⚡ PREDICTED POINTS: {optimal_team['predicted_points']:.1f}")
    
    # Display Starting XI
    print(f"\n🔥 STARTING XI ({optimal_team['formation']['name']}):")
    
    starting_xi = optimal_team['starting_xi']
    position_names = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
    
    # Group and display by position
    for pos_num, pos_name in position_names.items():
        position_players = [p for p in starting_xi if p['position'] == pos_num]
        if position_players:
            print(f"\n  {pos_name}:")
            for player in position_players:
                print(f"    • {player['name']} ({player['team_name']}) - {player['predicted_points']:.1f}pts - £{player['price']:.1f}m")
    
    # Display Bench
    print(f"\n🪑 BENCH (4 players):")
    bench = optimal_team['bench']
    for i, player in enumerate(bench, 1):
        pos_name = position_names.get(player['position'], 'UNK')
        print(f"  {i}. {player['name']} ({pos_name}) - {player['predicted_points']:.1f}pts - £{player['price']:.1f}m")
    
    # Team summary stats
    print(f"\n📈 TEAM STATISTICS:")
    team_count = {}
    for player in optimal_team['squad']:
        team_name = player['team_name']
        team_count[team_name] = team_count.get(team_name, 0) + 1
    
    print("  Team Distribution:")
    for team, count in sorted(team_count.items(), key=lambda x: x[1], reverse=True):
        print(f"    • {team}: {count} players")
    
    # Position breakdown
    pos_breakdown = {1: 0, 2: 0, 3: 0, 4: 0}
    for player in optimal_team['squad']:
        pos_breakdown[player['position']] += 1
    
    print(f"  Squad Composition: {pos_breakdown[1]} GK, {pos_breakdown[2]} DEF, {pos_breakdown[3]} MID, {pos_breakdown[4]} FWD")
    
except Exception as e:
    print(f"Error testing prediction model: {e}")
    import traceback
    traceback.print_exc()

