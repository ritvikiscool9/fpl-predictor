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
# Fantasy Stats
urlFantasy = "https://fantasy.premierleague.com/api/bootstrap-static/"
# More in-depth stats
urlPlayerSpecificStats = "https://fantasy.premierleague.com/api/fixtures/"

# Test code to ensure endpoints return correct information
headers = {"X-Auth-Token": API_KEY}
response = requests.get(urlPlayerSpecificStats, headers=headers)

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

# def calculate_player_form(player_id, matches):
#     # loop over last N matches
#     # compute goals + assists + FPL points
#     return avg_form_score

# def calculate_team_form(team_id, matches):
#     # last N matches
#     # compute goals scored, goals conceded, results

#     return form_score

# def calculate_opposition_form(opponent_id, matches):
#     # similar to team form but for opponent
#     return opp_form_score

# def get_home_away(player_team, next_fixture):
#     return 1 if next_fixture['homeTeam'] == player_team else 0

# def get_injury_status(player_id, injury_data):
#     return 1 if injury_data[player_id] == 'injured' else 0

# def calculate_minutes(player_id, matches):
#     # avg minutes per match
#     return avg_minutes
