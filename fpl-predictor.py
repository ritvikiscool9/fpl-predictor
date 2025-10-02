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

# if response.status_code == 200:
#     data = response.json()
#     print(data)
# else:
#     print("Error:", response.status_code, response.text)

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
    for player in players:
        try:
            prediction = predict_player_points(player, match_data)
            if prediction['predicted_points'] > 3:  # Only consider decent predictions
                all_predictions.append(prediction)
        except Exception as e:
            continue
    
    # Sort by value rating (points per million)
    all_predictions.sort(key=lambda x: x['value_rating'], reverse=True)
    
    # Filter by budget (price already converted to millions)
    affordable_players = [p for p in all_predictions if p['price'] <= budget/10]
    
    # Debug: print budget info
    print(f"Budget: £{budget/10}m, Total players: {len(all_predictions)}, Affordable: {len(affordable_players)}")
    
    recommendations = {
        'best_value': affordable_players[:top_n],
        'highest_predicted': sorted(all_predictions, key=lambda x: x['predicted_points'], reverse=True)[:top_n],
        'differential_picks': [p for p in affordable_players if p['ownership'] < 5][:top_n]
    }
    
    return recommendations

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
        for i, player in enumerate(recommendations['highest_predicted'][:3], 1):
            print(f"  {i}. {player['name']} - {player['predicted_points']} pts "
                  f"(£{player['price']}m, {player['ownership']}% owned)")
    else:
        print("\n📈 Highest Predicted Points: No predictions available")
    
    if recommendations['differential_picks']:
        print("\n🔥 Differential Picks (<5% owned):")
        for i, player in enumerate(recommendations['differential_picks'][:3], 1):
            print(f"  {i}. {player['name']} - {player['predicted_points']} pts "
                  f"(£{player['price']}m, {player['ownership']}% owned)")
    
except Exception as e:
    print(f"Error testing prediction model: {e}")
    import traceback
    traceback.print_exc()

