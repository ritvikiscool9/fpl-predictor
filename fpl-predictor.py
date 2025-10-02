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

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print("Error:", response.status_code, response.text)

def calculate_player_form(player_id, matches):
    # loop over last N matches
    # compute goals + assists + FPL points
    return avg_form_score

def calculate_team_form(team_id, matches):
    # last N matches
    # compute goals scored, goals conceded, results

    return form_score

def calculate_opposition_form(opponent_id, matches):
    # similar to team form but for opponent
    return opp_form_score

def get_home_away(player_team, next_fixture):
    return 1 if next_fixture['homeTeam'] == player_team else 0

def get_injury_status(player_id, injury_data):
    return 1 if injury_data[player_id] == 'injured' else 0

def calculate_minutes(player_id, matches):
    # avg minutes per match
    return avg_minutes
