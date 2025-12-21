# env\Scripts\activate
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

API_KEY = os.getenv("API_KEY")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials not found. Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


if API_KEY is None:
    raise ValueError("API Key not found. Ensure you have a .env file.")


# Database helper functions
def save_teams_to_db(teams_data):
    """Save teams data to Supabase database"""
    try:
        for team in teams_data:
            # Use upsert to avoid duplicates
            supabase.table("teams").upsert(
                {
                    "fpl_team_id": team["id"],
                    "name": team["name"],
                    "short_name": team["short_name"],
                    "code": team.get("code"),
                },
                on_conflict="fpl_team_id",
            ).execute()
        print(f"Successfully saved {len(teams_data)} teams to database")
    except Exception as e:
        print(f"Error saving teams to database: {e}")
        raise


def get_teams_from_db():
    """Get all teams from database"""
    try:
        result = supabase.table("teams").select("*").execute()
        return result.data
    except Exception as e:
        print(f"Error getting teams from database: {e}")
        return []


def save_players_to_db(players_data, team_mapping):
    """Save players data to Supabase database"""
    try:
        saved_count = 0
        for player in players_data:
            # Find the database team_id using FPL team_id
            team_id = None
            fpl_team_id = player["team"]

            # Get team database ID
            team_result = (
                supabase.table("teams")
                .select("id")
                .eq("fpl_team_id", fpl_team_id)
                .execute()
            )
            if team_result.data:
                team_id = team_result.data[0]["id"]

            if team_id:
                supabase.table("players").upsert(
                    {
                        "fpl_player_id": player["id"],
                        "first_name": player["first_name"],
                        "second_name": player["second_name"],
                        "web_name": player["web_name"],
                        "team_id": team_id,
                        "element_type": player["element_type"],
                        "status": player.get("status", "a"),
                    },
                    on_conflict="fpl_player_id",
                ).execute()
                saved_count += 1

        print(f"Successfully saved {saved_count} players to database")
    except Exception as e:
        print(f"Error saving players to database: {e}")
        raise


def get_team_mapping_from_db():
    """Get team mapping from database (football_data_id -> fpl_team_id)"""
    try:
        result = (
            supabase.table("teams")
            .select("football_data_team_id, fpl_team_id")
            .execute()
        )
        mapping = {}
        for team in result.data:
            if team["football_data_team_id"]:
                mapping[team["football_data_team_id"]] = team["fpl_team_id"]
        return mapping
    except Exception as e:
        print(f"Error getting team mapping from database: {e}")
        return {}


def save_team_mapping_to_db(fd_team_id, fpl_team_id):
    """Save individual team mapping to database"""
    try:
        # Update the team with football_data_team_id
        result = (
            supabase.table("teams")
            .update({"football_data_team_id": fd_team_id})
            .eq("fpl_team_id", fpl_team_id)
            .execute()
        )
        return result.data
    except Exception as e:
        print(f"Error saving team mapping to database: {e}")
        return None


def get_player_mapping_from_db():
    """Get player mapping from database (football_data_id -> fpl_player_id)"""
    try:
        result = (
            supabase.table("players")
            .select("football_data_player_id, fpl_player_id")
            .execute()
        )
        mapping = {}
        for player in result.data:
            if player["football_data_player_id"]:
                mapping[player["football_data_player_id"]] = player["fpl_player_id"]
        return mapping
    except Exception as e:
        print(f"Error getting player mapping from database: {e}")
        return {}


def save_player_mapping_to_db(fd_player_id, fpl_player_id):
    """Save individual player mapping to database"""
    try:
        result = (
            supabase.table("players")
            .update({"football_data_player_id": fd_player_id})
            .eq("fpl_player_id", fpl_player_id)
            .execute()
        )
        return result.data
    except Exception as e:
        print(f"Error saving player mapping to database: {e}")
        return None


# Gameweek and FPL data functions
def get_current_gameweek():
    """Get current gameweek from database"""
    try:
        result = (
            supabase.table("current_season").select("*").eq("is_active", True).execute()
        )

        if result.data:
            # If multiple rows exist, clean up and keep only one
            if len(result.data) > 1:
                print(f"Found {len(result.data)} current season rows, cleaning up...")
                # Delete all rows first
                supabase.table("current_season").delete().gte("id", 0).execute()
                # Insert one correct row
                supabase.table("current_season").upsert(
                    {"season": "2025-26", "current_gameweek": 1, "is_active": True}
                ).execute()
                return {"season": "2025-26", "current_gameweek": 1, "is_active": True}
            else:
                return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting current gameweek: {e}")
        return None


def save_current_gameweek(season, gameweek_number):
    """Save or update current gameweek"""
    try:
        result = (
            supabase.table("current_season")
            .upsert(
                {
                    "season": season,
                    "current_gameweek": gameweek_number,
                    "is_active": True,
                    "updated_at": datetime.now().isoformat(),
                }
            )
            .execute()
        )
        return result.data
    except Exception as e:
        print(f"Error saving current gameweek: {e}")
        return None


def save_gameweek_info(gameweek_data):
    """Save gameweek information to database"""
    try:
        for gw in gameweek_data:
            supabase.table("gameweeks").upsert(
                {
                    "gameweek_number": gw["id"],
                    "season": "2025-26",
                    "name": gw.get("name", f"Gameweek {gw['id']}"),
                    "deadline_time": gw.get("deadline_time"),
                    "is_finished": gw.get("finished", False),
                    "is_current": gw.get("is_current", False),
                    "average_entry_score": gw.get("average_entry_score", 0),
                    "highest_score": gw.get("highest_score", 0),
                },
                on_conflict="gameweek_number,season",
            ).execute()
        print(f"Saved {len(gameweek_data)} gameweeks to database")
    except Exception as e:
        print(f"Error saving gameweeks: {e}")


def save_current_player_stats(players_data, current_gameweek_id):
    """Save current player statistics to database"""
    try:
        saved_count = 0
        for player in players_data:
            # Get player database ID
            player_result = (
                supabase.table("players")
                .select("id")
                .eq("fpl_player_id", player["id"])
                .execute()
            )
            if not player_result.data:
                continue

            player_db_id = player_result.data[0]["id"]

            # Save current stats
            supabase.table("current_player_stats").upsert(
                {
                    "player_id": player_db_id,
                    "gameweek_id": current_gameweek_id,
                    "total_points": player.get("total_points", 0),
                    "minutes": player.get("minutes", 0),
                    "goals_scored": player.get("goals_scored", 0),
                    "assists": player.get("assists", 0),
                    "clean_sheets": player.get("clean_sheets", 0),
                    "goals_conceded": player.get("goals_conceded", 0),
                    "own_goals": player.get("own_goals", 0),
                    "penalties_saved": player.get("penalties_saved", 0),
                    "penalties_missed": player.get("penalties_missed", 0),
                    "yellow_cards": player.get("yellow_cards", 0),
                    "red_cards": player.get("red_cards", 0),
                    "saves": player.get("saves", 0),
                    "bonus": player.get("bonus", 0),
                    "bps": player.get("bps", 0),
                    "influence": float(player.get("influence", 0)),
                    "creativity": float(player.get("creativity", 0)),
                    "threat": float(player.get("threat", 0)),
                    "ict_index": float(player.get("ict_index", 0)),
                    "now_cost": player.get("now_cost", 50),
                    "selected_by_percent": float(player.get("selected_by_percent", 0)),
                    "transfers_in": player.get("transfers_in", 0),
                    "transfers_out": player.get("transfers_out", 0),
                    "form": float(player.get("form", 0)),
                    "points_per_game": float(player.get("points_per_game", 0)),
                    "status": player.get("status", "a"),
                    "news": player.get("news", ""),
                    "chance_of_playing_this_round": player.get(
                        "chance_of_playing_this_round"
                    ),
                    "chance_of_playing_next_round": player.get(
                        "chance_of_playing_next_round"
                    ),
                    "data_updated_at": datetime.now().isoformat(),
                },
                on_conflict="player_id,gameweek_id",
            ).execute()
            saved_count += 1

        print(f"Saved current stats for {saved_count} players")
    except Exception as e:
        print(f"Error saving player stats: {e}")


def get_fpl_data_from_db():
    """Get FPL data from database instead of API/cache"""
    try:
        # Get current gameweek
        current_gw = get_current_gameweek()
        if not current_gw:
            return None

        # Get teams
        teams_result = supabase.table("teams").select("*").execute()
        teams = []
        for team in teams_result.data:
            teams.append(
                {
                    "id": team["fpl_team_id"],
                    "name": team["name"],
                    "short_name": team["short_name"],
                    "code": team.get("code"),
                }
            )

        # Use simpler approach without complex SQL (previous SQL query removed)
        players_result = None

        if not players_result:
            # Fallback: get basic player data
            players_result = (
                supabase.table("players")
                .select(
                    "fpl_player_id, first_name, second_name, web_name, element_type, status, teams!inner(fpl_team_id)"
                )
                .execute()
            )

            players = []
            for player in players_result.data:
                players.append(
                    {
                        "id": player["fpl_player_id"],
                        "first_name": player["first_name"],
                        "second_name": player["second_name"],
                        "web_name": player["web_name"],
                        "team": player["teams"]["fpl_team_id"],
                        "element_type": player["element_type"],
                        "status": player["status"],
                        "total_points": 0,
                        "now_cost": 50,
                        "selected_by_percent": "0.0",
                    }
                )
        else:
            players = players_result.data

        # Get gameweeks
        gameweeks_result = (
            supabase.table("gameweeks")
            .select("*")
            .eq("season", current_gw["season"])
            .order("gameweek_number")
            .execute()
        )
        gameweeks = []
        for gw in gameweeks_result.data:
            gameweeks.append(
                {
                    "id": gw["gameweek_number"],
                    "name": gw["name"],
                    "deadline_time": gw["deadline_time"],
                    "finished": gw["is_finished"],
                    "is_current": gw["is_current"],
                }
            )

        return {
            "teams": teams,
            "elements": players,
            "events": gameweeks,
            "total_players": len(players),
        }

    except Exception as e:
        print(f"Error getting FPL data from database: {e}")
        return None


# Team information
urlTeams = "https://api.football-data.org/v4/competitions/PL/teams"
# Team fixtures
urlMatches = "https://api.football-data.org/v4/competitions/PL/matches"
# League Standings
urlStandings = "http://api.football-data.org/v4/competitions/PL/standings"
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


# Create a mapping between football-data.org and the FPL API
# Create a mapping between football-data.org and the FPL API
def create_team_mapping():
    """Create team mapping using Supabase database instead of JSON cache"""

    # Try to load existing mapping from database first
    existing_mapping = get_team_mapping_from_db()
    if existing_mapping:
        print(
            f"Loading existing team mapping from database: {len(existing_mapping)} teams"
        )
        return existing_mapping

    print("Creating fresh team mapping and saving to database...")

    # Get FPL team data
    fplResponse = requests.get(urlFantasy)
    if fplResponse.status_code != 200:
        raise Exception(f"Failed to get data from FPL API: {fplResponse.status_code}")

    fplData = fplResponse.json()
    fplTeams = {team["name"]: team["id"] for team in fplData["teams"]}

    # Save FPL teams to database
    save_teams_to_db(fplData["teams"])

    # Get football-data.org teams
    headers = {"X-Auth-Token": API_KEY}
    fdResponse = requests.get(urlTeams, headers=headers)
    if fdResponse.status_code != 200:
        raise Exception(
            f"Failed to get data from football-data.org API: {fdResponse.status_code}"
        )

    fdData = fdResponse.json()
    fdTeams = {team["name"]: team["id"] for team in fdData["teams"]}

    # Manual mapping teams with different names between APIs
    nameMapping = {
        "Brighton & Hove Albion FC": "Brighton",
        "Newcastle United FC": "Newcastle",
        "Manchester United FC": "Man Utd",
        "Manchester City FC": "Man City",
        "Tottenham Hotspur FC": "Spurs",
        "Nottingham Forest FC": "Nott'm Forest",
        "Sunderland AFC": "Sunderland",
        "West Ham United FC": "West Ham",
        "Wolverhampton Wanderers FC": "Wolves",
        "Arsenal FC": "Arsenal",
        "Aston Villa FC": "Aston Villa",
        "Chelsea FC": "Chelsea",
        "Everton FC": "Everton",
        "Fulham FC": "Fulham",
        "Liverpool FC": "Liverpool",
        "Crystal Palace FC": "Crystal Palace",
        "Brentford FC": "Brentford",
        "AFC Bournemouth": "Bournemouth",
        "Burnley FC": "Burnley",
        "Leeds United FC": "Leeds",
    }

    # Create the mapping dictionary and save to database
    teamMapping = {}
    for fdName, fdID in fdTeams.items():
        fpl_team_id = None

        # Try direct name match first
        if fdName in fplTeams:
            fpl_team_id = fplTeams[fdName]
        # Try mapped name
        elif fdName in nameMapping and nameMapping[fdName] in fplTeams:
            fpl_team_id = fplTeams[nameMapping[fdName]]
        else:
            print(f"Warning: Could not map team {fdName}")
            continue

        if fpl_team_id:
            teamMapping[fdID] = fpl_team_id
            # Save the mapping to database
            save_team_mapping_to_db(fdID, fpl_team_id)

    print(
        f"Successfully created and saved mapping for {len(teamMapping)} teams to database"
    )
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
    Creates a mapping between football-data.org players and FPL players using database
    Returns: Dictionary mapping fd_player_id -> fpl_player_id
    """

    # Try to load existing mapping from database first
    existing_mapping = get_player_mapping_from_db()

    # Check if we have sufficient mappings (at least 200 players should be mapped)
    # With 20 Premier League teams ~25 players each = ~500 total, so 200+ is reasonable coverage
    if existing_mapping and len(existing_mapping) >= 200:
        print(
            f"Loading existing player mapping from database: {len(existing_mapping)} players"
        )
        return existing_mapping
    elif existing_mapping:
        print(
            f"Found {len(existing_mapping)} existing mappings, but need more. Building fresh mapping..."
        )
    else:
        print(
            "No existing player mappings found. Building fresh player mapping from APIs and saving to database..."
        )

    print(
        "This will take ~20 minutes due to API rate limits but only needs to be done once."
    )

    # Get player data from FPL bootstrap (contains all players)
    fplResponse = requests.get(urlFantasy)
    if fplResponse.status_code != 200:
        raise Exception(f"Failed to get data from FPL API: {fplResponse.status_code}")

    fplData = fplResponse.json()
    fplPlayers = fplData["elements"]  # All FPL players

    # Save FPL players to database
    save_players_to_db(fplPlayers, {})  # Empty mapping for now, will be filled later

    # Create FPL player lookup by team and name
    fplPlayerLookup = {}
    for player in fplPlayers:
        team_id = player["team"]
        # Create multiple name variations for matching
        full_name = f"{player['first_name']} {player['second_name']}".strip()
        web_name = player["web_name"]

        if team_id not in fplPlayerLookup:
            fplPlayerLookup[team_id] = {}

        # Store player under multiple name formats for better matching
        name_variations = [
            full_name.lower(),
            web_name.lower(),
            player["second_name"].lower(),
            player["first_name"].lower(),
            # Handle common name formats
            f"{player['first_name'][0].lower()}. {player['second_name'].lower()}",
            # Remove accents and special characters
            full_name.lower()
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u"),
        ]

        for name_var in name_variations:
            if name_var.strip():  # Only add non-empty names
                fplPlayerLookup[team_id][name_var] = player["id"]

    # Get team data from football-data.org (needed for player-team mapping)
    headers = {"X-Auth-Token": API_KEY}
    fdResponse = requests.get(urlTeams, headers=headers)
    if fdResponse.status_code != 200:
        raise Exception(
            f"Failed to get data from football-data.org API: {fdResponse.status_code}"
        )

    fdTeams = fdResponse.json()["teams"]

    # Get player data from each team's squad
    playerMapping = {}
    total_teams = len(fdTeams)
    processed_teams = 0

    print(f"Processing {total_teams} teams for player mapping...")

    for team in fdTeams:
        fd_team_id = team["id"]
        fpl_team_id = get_fpl_team_id(fd_team_id)

        if not fpl_team_id:
            print(f"Warning: No FPL mapping for team {team['name']}")
            continue

        # Get squad for this team with retry logic
        squadUrl = f"https://api.football-data.org/v4/teams/{fd_team_id}"

        import time

        time.sleep(
            6.5
        )  # Wait 6.5 seconds between requests (safer for 10 req/min limit)

        max_retries = 3
        retry_count = 0
        squadResponse = None

        while retry_count < max_retries:
            squadResponse = requests.get(squadUrl, headers=headers)

            if squadResponse.status_code == 200:
                break
            elif squadResponse.status_code == 429:  # Rate limit
                wait_time = (retry_count + 1) * 15  # Wait 15, 30, 45 seconds
                print(
                    f"Rate limit hit for {team['name']}, waiting {wait_time} seconds..."
                )
                time.sleep(wait_time)
                retry_count += 1
            else:
                print(
                    f"Warning: Failed to get squad for team {team['name']} (Status: {squadResponse.status_code})"
                )
                break

        if squadResponse is None or squadResponse.status_code != 200:
            print(f"Skipping team {team['name']} after {retry_count} retries")
            processed_teams += 1
            print(f"Progress: {processed_teams}/{total_teams} teams processed")
            continue

        squadData = squadResponse.json()
        fdPlayers = squadData.get("squad", [])

        # Match players between APIs
        matched_count = 0
        total_players = len(fdPlayers)

        for fdPlayer in fdPlayers:
            fd_player_id = fdPlayer["id"]
            fd_player_name = fdPlayer["name"].lower()
            player_position = fdPlayer.get("position", "Unknown")

            # Skip obvious non-FPL players (youth/academy players, etc.)
            skip_keywords = [
                "u18",
                "u19",
                "u21",
                "u23",
                "academy",
                "youth",
                "development",
            ]
            if any(keyword in fd_player_name for keyword in skip_keywords):
                continue

            # Skip players who are likely loans or not in FPL (common patterns)
            likely_non_fpl = [
                "russ oakley",
                "aidan borland",
                "max merrick",
                "ted curd",
                "reggie walsh",
                "shumaira mheuka",
                "ollie harrison",
                "kieran morrison",
                "tommy pilling",
                "kaden braithwaite",
                "jaden heskey",
                "reigan heskey",
                "max thompson",
            ]
            if fd_player_name in likely_non_fpl:
                continue

            # Try to find matching FPL player with improved matching
            fpl_player_id = None
            if fpl_team_id in fplPlayerLookup:
                team_players = fplPlayerLookup[fpl_team_id]

                # Clean the football-data name for better matching
                clean_fd_name = (
                    fd_player_name.replace("á", "a")
                    .replace("é", "e")
                    .replace("í", "i")
                    .replace("ó", "o")
                    .replace("ú", "u")
                )

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
                        if (
                            match_score > best_score and match_score >= 8
                        ):  # Require decent confidence
                            best_match = fpl_id
                            best_score = match_score

                    fpl_player_id = best_match

            if fpl_player_id:
                playerMapping[fd_player_id] = fpl_player_id
                matched_count += 1
            else:
                # Only show warning for likely first-team players
                if player_position in [
                    "Goalkeeper",
                    "Centre-Back",
                    "Left-Back",
                    "Right-Back",
                    "Defensive Midfield",
                    "Central Midfield",
                    "Attacking Midfield",
                    "Left Winger",
                    "Right Winger",
                    "Centre-Forward",
                ]:
                    print(
                        f"Warning: Could not match player {fdPlayer['name']} ({player_position}) from {team['name']}"
                    )

        if total_players > 0:
            match_rate = (matched_count / total_players) * 100
            processed_teams += 1
            print(
                f"Team {team['name']}: Matched {matched_count}/{total_players} players ({match_rate:.1f}%)"
            )
            print(f"Progress: {processed_teams}/{total_teams} teams processed")
        else:
            processed_teams += 1
            print(f"No players found for {team['name']}")
            print(f"Progress: {processed_teams}/{total_teams} teams processed")

    # Save player mappings to database
    for fd_player_id, fpl_player_id in playerMapping.items():
        save_player_mapping_to_db(fd_player_id, fpl_player_id)

    print(f"Successfully saved {len(playerMapping)} player mappings to database")
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
        fpl_player = next(
            (p for p in fplData["elements"] if p["id"] == fpl_player_id), None
        )

        if fpl_player:
            # Get corresponding football-data player
            fd_player_id = get_fd_player_id(fpl_player_id)

            combined_data = {
                "fpl_data": fpl_player,
                "fd_player_id": fd_player_id,
                "player_name": f"{fpl_player['first_name']} {fpl_player['second_name']}",
                "team_name": next(
                    (
                        t["name"]
                        for t in fplData["teams"]
                        if t["id"] == fpl_player["team"]
                    ),
                    "Unknown",
                ),
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
    print(
        f"Sample mapping: FD Player ID {first_mapping[0]} -> FPL Player ID {first_mapping[1]}"
    )

    # Test combined data function
    sample_data = get_combined_player_data(first_mapping[1])
    if sample_data:
        print(
            f"Sample player: {sample_data['player_name']} from {sample_data['team_name']}"
        )


def get_cached_fpl_data():
    """Get FPL data from database or fetch fresh from API if needed"""

    # Try to get data from database first
    db_data = get_fpl_data_from_db()
    if db_data and db_data.get("elements"):
        print(f"Loading FPL data from database: {len(db_data['elements'])} players")
        return db_data

    print("Fetching fresh FPL data from API and saving to database...")
    response = requests.get(urlFantasy)
    if response.status_code != 200:
        raise Exception(f"Failed to get FPL data: {response.status_code}")

    data = response.json()

    # Save to database
    try:
        # Save gameweek info
        if "events" in data:
            save_gameweek_info(data["events"])

        # Find current gameweek
        current_gameweek = None
        if "events" in data:
            for event in data["events"]:
                if event.get("is_current", False):
                    current_gameweek = event["id"]
                    save_current_gameweek("2025-26", current_gameweek)
                    break

        # Save current player stats
        if "elements" in data and current_gameweek:
            # Get gameweek database ID
            gw_result = (
                supabase.table("gameweeks")
                .select("id")
                .eq("gameweek_number", current_gameweek)
                .eq("season", "2025-26")
                .execute()
            )
            if gw_result.data:
                gameweek_db_id = gw_result.data[0]["id"]
                save_current_player_stats(data["elements"], gameweek_db_id)

        print("Successfully saved FPL data to database")

    except Exception as e:
        print(f"Warning: Could not save to database: {e}")
        print("Continuing with API data...")

    return data


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
        if fixture["finished"]:
            completed_fixtures.append(fixture)
        else:
            upcoming_fixtures.append(fixture)

    # Analyze team form from recent fixtures
    team_form = analyze_team_form(completed_fixtures[-50:])  # Last 50 completed games

    # Analyze fixture difficulty
    fixture_analysis = analyze_fixture_difficulty(
        upcoming_fixtures[:38]
    )  # Next 38 games

    return {
        "upcoming_fixtures": upcoming_fixtures,
        "completed_fixtures": completed_fixtures,
        "team_form": team_form,
        "fixture_difficulty": fixture_analysis,
        "fpl_data": fpl_data,
    }


def analyze_team_form(recent_fixtures):
    """Analyze recent team performance"""
    team_stats = {}

    for fixture in recent_fixtures:
        home_team = fixture["team_h"]
        away_team = fixture["team_a"]

        # Initialize team stats if not exists
        for team in [home_team, away_team]:
            if team not in team_stats:
                team_stats[team] = {
                    "games_played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "clean_sheets": 0,
                }

        # Update stats based on fixture result
        home_score = fixture["team_h_score"]
        away_score = fixture["team_a_score"]

        if home_score is not None and away_score is not None:
            # Update games played
            team_stats[home_team]["games_played"] += 1
            team_stats[away_team]["games_played"] += 1

            # Update goals
            team_stats[home_team]["goals_for"] += home_score
            team_stats[home_team]["goals_against"] += away_score
            team_stats[away_team]["goals_for"] += away_score
            team_stats[away_team]["goals_against"] += home_score

            # Update win/draw/loss
            if home_score > away_score:
                team_stats[home_team]["wins"] += 1
                team_stats[away_team]["losses"] += 1
            elif away_score > home_score:
                team_stats[away_team]["wins"] += 1
                team_stats[home_team]["losses"] += 1
            else:
                team_stats[home_team]["draws"] += 1
                team_stats[away_team]["draws"] += 1

            # Update clean sheets
            if home_score == 0:
                team_stats[away_team]["clean_sheets"] += 1
            if away_score == 0:
                team_stats[home_team]["clean_sheets"] += 1

    return team_stats


def analyze_fixture_difficulty(upcoming_fixtures):
    """Analyze upcoming fixture difficulty for each team"""
    fixture_difficulty = {}

    for fixture in upcoming_fixtures:
        home_team = fixture["team_h"]
        away_team = fixture["team_a"]
        difficulty_h = fixture.get("team_h_difficulty", 3)  # Default difficulty
        difficulty_a = fixture.get("team_a_difficulty", 3)

        # Initialize if not exists
        for team in [home_team, away_team]:
            if team not in fixture_difficulty:
                fixture_difficulty[team] = {
                    "next_5_fixtures": [],
                    "avg_difficulty": 0,
                    "home_games": 0,
                    "away_games": 0,
                }

        # Add fixture info
        if len(fixture_difficulty[home_team]["next_5_fixtures"]) < 5:
            fixture_difficulty[home_team]["next_5_fixtures"].append(
                {"opponent": away_team, "is_home": True, "difficulty": difficulty_h}
            )
            fixture_difficulty[home_team]["home_games"] += 1

        if len(fixture_difficulty[away_team]["next_5_fixtures"]) < 5:
            fixture_difficulty[away_team]["next_5_fixtures"].append(
                {"opponent": home_team, "is_home": False, "difficulty": difficulty_a}
            )
            fixture_difficulty[away_team]["away_games"] += 1

    # Calculate average difficulty
    for team, data in fixture_difficulty.items():
        if data["next_5_fixtures"]:
            avg_diff = sum(f["difficulty"] for f in data["next_5_fixtures"]) / len(
                data["next_5_fixtures"]
            )
            data["avg_difficulty"] = round(avg_diff, 2)

    return fixture_difficulty


# Test the match data processing
print("\n" + "=" * 50)
print("Testing Match Data Processing...")
try:
    match_data = process_match_data()
    print(f"Found {len(match_data['upcoming_fixtures'])} upcoming fixtures")
    print(f"Found {len(match_data['completed_fixtures'])} completed fixtures")
    print(f"Analyzed form for {len(match_data['team_form'])} teams")
    print(
        f"Fixture difficulty calculated for {len(match_data['fixture_difficulty'])} teams"
    )

    # Show sample team form
    if match_data["team_form"]:
        sample_team = list(match_data["team_form"].keys())[0]
        form = match_data["team_form"][sample_team]
        print(f"\nSample team form (Team {sample_team}):")
        print(
            f"  Games: {form['games_played']}, Wins: {form['wins']}, Clean Sheets: {form['clean_sheets']}"
        )

    # Show sample fixture difficulty
    if match_data["fixture_difficulty"]:
        sample_team = list(match_data["fixture_difficulty"].keys())[0]
        difficulty = match_data["fixture_difficulty"][sample_team]
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

    total_points = player.get("total_points", 0)
    games_played = player.get("minutes", 0) / 90  # Rough games estimate

    if games_played == 0:
        return 0

    points_per_game = total_points / max(games_played, 1)

    # Normalize to 0-10 scale based on position
    position = player.get("element_type", 1)

    # Expected points per game by position (more realistic estimates)
    position_benchmarks = {
        1: 2.5,  # Goalkeepers - lower baseline
        2: 3.0,  # Defenders
        3: 3.5,  # Midfielders
        4: 4.0,  # Forwards
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
    avg_difficulty = team_fixtures.get("avg_difficulty", 3)

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
    games = form.get("games_played", 1)

    if games == 0:
        return 5

    # Calculate various strength metrics
    win_rate = form.get("wins", 0) / games
    goals_per_game = form.get("goals_for", 0) / games
    clean_sheet_rate = form.get("clean_sheets", 0) / games
    goals_against_per_game = form.get("goals_against", 0) / games

    # Weighted strength score
    attacking_strength = min(10, goals_per_game * 2.5)  # Scale goals to 0-10
    defensive_strength = min(10, clean_sheet_rate * 10)  # Clean sheets to 0-10
    general_form = win_rate * 10

    # Penalty for conceding goals
    defensive_penalty = min(5, goals_against_per_game * 2)

    overall_strength = (
        attacking_strength + defensive_strength + general_form - defensive_penalty
    ) / 3

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

    player_id = player["id"]
    team_id = player["team"]
    position = player["element_type"]

    # Base metrics
    form_score = calculate_player_form_score(player)
    fixture_favorability = calculate_fixture_favorability(
        team_id, match_data["fixture_difficulty"]
    )
    team_strength = calculate_team_strength_score(team_id, match_data["team_form"])

    # Player-specific factors
    minutes_likelihood = min(
        1.0, player.get("minutes", 0) / (38 * 90 * 0.7)
    )  # Likelihood to play
    price_value = player.get("now_cost", 50) / 10  # Price in millions
    ownership = float(player.get("selected_by_percent", "5.0"))

    # Calculate base prediction (scale to realistic FPL points range)
    base_prediction = (
        form_score * 0.4 + fixture_favorability * 0.3 + team_strength * 0.3
    ) * 0.8  # Scale to ~2-8 point range

    # Add position baseline points
    position_baselines = {1: 2.0, 2: 2.5, 3: 3.0, 4: 3.5}  # Minimum expected points
    base_prediction += position_baselines.get(position, 3.0)

    # Apply position multiplier
    position_adjusted = base_prediction * position_multipliers.get(position, 1.0)

    # Apply minutes likelihood (but not too harsh)
    minutes_adjusted = position_adjusted * max(0.5, minutes_likelihood)

    # Injury/suspension check (basic)
    availability_multiplier = 1.0
    if player.get("status") != "a":  # 'a' = available
        availability_multiplier = 0.3

    final_prediction = minutes_adjusted * availability_multiplier

    # Risk assessment
    risk_factors = []
    if minutes_likelihood < 0.7:
        risk_factors.append("Rotation risk")
    if ownership > 25:
        risk_factors.append("High ownership")
    if player.get("status") != "a":
        risk_factors.append("Injury/suspension concern")

    return {
        "player_id": player_id,
        "name": f"{player['first_name']} {player['second_name']}",
        "team_id": team_id,
        "position": position,
        "predicted_points": round(final_prediction, 2),
        "confidence": round(min(10, form_score + minutes_likelihood * 5), 1),
        "form_score": form_score,
        "fixture_favorability": fixture_favorability,
        "team_strength": team_strength,
        "price": price_value,
        "ownership": ownership,
        "risk_factors": risk_factors,
        "value_rating": (
            round(final_prediction / price_value, 2) if price_value > 0 else 0
        ),
    }


def get_best_players_by_position(match_data, top_n=5):
    """
    Get top predicted players for each position
    """
    fpl_data = match_data["fpl_data"]
    players = fpl_data["elements"]

    # Group players by position
    position_names = {1: "Goalkeepers", 2: "Defenders", 3: "Midfielders", 4: "Forwards"}
    best_players = {}

    for position in range(1, 5):
        position_players = [p for p in players if p["element_type"] == position]

        # Get predictions for all players in this position
        predictions = []
        for player in position_players:
            try:
                prediction = predict_player_points(player, match_data)
                predictions.append(prediction)
            except Exception:
                continue  # Skip problematic players

        # Sort by predicted points
        predictions.sort(key=lambda x: x["predicted_points"], reverse=True)

        best_players[position_names[position]] = predictions[:top_n]

    return best_players


def generate_transfer_recommendations(match_data, budget=1000, top_n=3):
    """
    Generate transfer recommendations based on predictions
    """
    fpl_data = match_data["fpl_data"]
    players = fpl_data["elements"]

    # Get all predictions
    all_predictions = []
    player_ids_seen = set()
    duplicates_found = 0

    for player in players:
        try:
            # Check for duplicate players in source data
            player_id = player["id"]
            if player_id in player_ids_seen:
                duplicates_found += 1
                print(
                    f"Warning: Duplicate player ID {player_id} found: {player['first_name']} {player['second_name']}"
                )
                continue
            player_ids_seen.add(player_id)

            prediction = predict_player_points(player, match_data)
            if prediction["predicted_points"] > 3:  # Only consider decent predictions
                all_predictions.append(prediction)
        except Exception:
            continue

    if duplicates_found > 0:
        print(f"Found {duplicates_found} duplicate players in FPL data")

    # Sort by value rating (points per million)
    all_predictions.sort(key=lambda x: x["value_rating"], reverse=True)

    # Filter by budget (price already converted to millions)
    affordable_players = [p for p in all_predictions if p["price"] <= budget / 10]

    # Debug: print budget info
    print(
        f"Budget: £{budget/10}m, Total players: {len(all_predictions)}, Affordable: {len(affordable_players)}"
    )

    # Create separate sorted lists to avoid mutation issues
    highest_predicted_sorted = sorted(
        all_predictions.copy(), key=lambda x: x["predicted_points"], reverse=True
    )
    differential_picks = [p for p in affordable_players if p["ownership"] < 5]

    # Remove duplicates by player_id and keep only unique players
    def remove_duplicates(player_list):
        seen_ids = set()
        unique_players = []
        for player in player_list:
            if player["player_id"] not in seen_ids:
                seen_ids.add(player["player_id"])
                unique_players.append(player)
        return unique_players

    recommendations = {
        "best_value": remove_duplicates(affordable_players[:top_n]),
        "highest_predicted": remove_duplicates(highest_predicted_sorted[:top_n]),
        "differential_picks": remove_duplicates(differential_picks[:top_n]),
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
    fpl_data = match_data["fpl_data"]
    players = fpl_data["elements"]
    teams = {team["id"]: team["name"] for team in fpl_data["teams"]}

    # Get all predictions
    all_predictions = []
    for player in players:
        try:
            prediction = predict_player_points(player, match_data)
            prediction["team_name"] = teams.get(prediction["team_id"], "Unknown")
            all_predictions.append(prediction)
        except Exception:
            continue

    # Sort by predicted points within each position
    goalkeepers = sorted(
        [p for p in all_predictions if p["position"] == 1],
        key=lambda x: x["predicted_points"],
        reverse=True,
    )
    defenders = sorted(
        [p for p in all_predictions if p["position"] == 2],
        key=lambda x: x["predicted_points"],
        reverse=True,
    )
    midfielders = sorted(
        [p for p in all_predictions if p["position"] == 3],
        key=lambda x: x["predicted_points"],
        reverse=True,
    )
    forwards = sorted(
        [p for p in all_predictions if p["position"] == 4],
        key=lambda x: x["predicted_points"],
        reverse=True,
    )

    # Team selection algorithm with constraints
    def select_squad_with_constraints():
        selected_squad = []
        team_counts = {}
        total_cost = 0
        budget_millions = budget / 10  # Convert to millions

        # Position requirements: [position_type, min_required, max_allowed]
        requirements = [
            (goalkeepers, "GK", 2, 2),
            (defenders, "DEF", 5, 5),
            (midfielders, "MID", 5, 5),
            (forwards, "FWD", 3, 3),
        ]

        # Greedy selection with constraints
        for player_pool, pos_name, min_req, max_req in requirements:
            position_selected = 0

            for player in player_pool:
                if position_selected >= max_req:
                    break

                team_id = player["team_id"]
                player_cost = player["price"]

                # Check constraints
                if (
                    total_cost + player_cost <= budget_millions
                    and team_counts.get(team_id, 0) < 3
                    and position_selected < max_req
                ):

                    selected_squad.append(player)
                    team_counts[team_id] = team_counts.get(team_id, 0) + 1
                    total_cost += player_cost
                    position_selected += 1

            # Check if we met minimum requirements
            if position_selected < min_req:
                print(
                    f"Warning: Could not select minimum {min_req} {pos_name}s (only got {position_selected})"
                )

        return selected_squad, total_cost

    squad, total_cost = select_squad_with_constraints()

    # Determine best formation and starting XI
    squad_gk = [p for p in squad if p["position"] == 1]
    squad_def = [p for p in squad if p["position"] == 2]
    squad_mid = [p for p in squad if p["position"] == 3]
    squad_fwd = [p for p in squad if p["position"] == 4]

    # Sort each position by predicted points for starting XI selection
    squad_gk.sort(key=lambda x: x["predicted_points"], reverse=True)
    squad_def.sort(key=lambda x: x["predicted_points"], reverse=True)
    squad_mid.sort(key=lambda x: x["predicted_points"], reverse=True)
    squad_fwd.sort(key=lambda x: x["predicted_points"], reverse=True)

    # Try different formations and pick best total points
    formations = [
        {"name": "3-4-3", "def": 3, "mid": 4, "fwd": 3},
        {"name": "3-5-2", "def": 3, "mid": 5, "fwd": 2},
        {"name": "4-3-3", "def": 4, "mid": 3, "fwd": 3},
        {"name": "4-4-2", "def": 4, "mid": 4, "fwd": 2},
        {"name": "4-5-1", "def": 4, "mid": 5, "fwd": 1},
        {"name": "5-3-2", "def": 5, "mid": 3, "fwd": 2},
        {"name": "5-4-1", "def": 5, "mid": 4, "fwd": 1},
    ]

    best_formation = None
    best_starting_xi = None
    best_bench = None
    best_total_points = 0

    for formation in formations:
        if (
            len(squad_def) >= formation["def"]
            and len(squad_mid) >= formation["mid"]
            and len(squad_fwd) >= formation["fwd"]
        ):

            starting_xi = []

            # Add best GK
            starting_xi.extend(squad_gk[:1])

            # Add players by formation
            starting_xi.extend(squad_def[: formation["def"]])
            starting_xi.extend(squad_mid[: formation["mid"]])
            starting_xi.extend(squad_fwd[: formation["fwd"]])

            # Calculate total predicted points for starting XI
            formation_points = sum(p["predicted_points"] for p in starting_xi)

            if formation_points > best_total_points:
                best_total_points = formation_points
                best_formation = formation
                best_starting_xi = starting_xi

                # Create bench (remaining players)
                bench = []
                starting_ids = {p["player_id"] for p in starting_xi}
                for player in squad:
                    if player["player_id"] not in starting_ids:
                        bench.append(player)
                best_bench = bench

    return {
        "squad": squad,
        "starting_xi": best_starting_xi,
        "bench": best_bench,
        "formation": best_formation,
        "total_cost": total_cost,
        "budget_remaining": (budget / 10) - total_cost,
        "predicted_points": best_total_points,
    }


# Test the prediction model
print("\n" + "=" * 60)
print("TESTING PREDICTION MODEL")
print("=" * 60)

try:
    # Get match data
    match_data = process_match_data()

    # Test predictions for top players by position
    print("Getting best predicted players by position...")
    best_players = get_best_players_by_position(match_data, top_n=3)

    for position, players in best_players.items():
        print(f"\nTOP 3 {position.upper()}:")
        for i, player in enumerate(players, 1):
            print(
                f"  {i}. {player['name']} - {player['predicted_points']} pts "
                f"(£{player['price']}m, {player['ownership']}% owned)"
            )

    # Generate transfer recommendations
    print(f"\nTRANSFER RECOMMENDATIONS (Budget: £10.0m):")
    recommendations = generate_transfer_recommendations(
        match_data, budget=100
    )  # £10m budget

    if recommendations["best_value"]:
        print("\nBest Value Picks:")
        for i, player in enumerate(recommendations["best_value"][:3], 1):
            print(
                f"  {i}. {player['name']} - {player['predicted_points']} pts "
                f"(£{player['price']}m, Value: {player['value_rating']})"
            )
    else:
        print("\n🎯 Best Value Picks: No affordable players found")

    if recommendations["highest_predicted"]:
        print("\nHighest Predicted Points:")
        highest_list = recommendations["highest_predicted"][:3]  # Take slice first
        for i, player in enumerate(highest_list, 1):
            print(
                f"  {i}. {player['name']} - {player['predicted_points']} pts "
                f"(£{player['price']}m, {player['ownership']}% owned)"
            )
    else:
        print("\n📈 Highest Predicted Points: No predictions available")

    if recommendations["differential_picks"]:
        print("\nDifferential Picks (<5% owned):")
        for i, player in enumerate(recommendations["differential_picks"][:3], 1):
            print(
                f"  {i}. {player['name']} - {player['predicted_points']} pts "
                f"(£{player['price']}m, {player['ownership']}% owned)"
            )

    # Generate optimal 15-player team
    print("\n" + "=" * 80)
    print("🏆 OPTIMAL 15-PLAYER TEAM FOR NEXT GAMEWEEK")
    print("=" * 80)

    optimal_team = build_optimal_team(match_data, budget=1000)  # £100m budget

    print(
        f"\n💰 BUDGET: £{optimal_team['total_cost']:.1f}m / £100.0m (£{optimal_team['budget_remaining']:.1f}m remaining)"
    )
    print(f"📊 FORMATION: {optimal_team['formation']['name']}")
    print(f"⚡ PREDICTED POINTS: {optimal_team['predicted_points']:.1f}")

    # Display Starting XI
    print(f"\nSTARTING XI ({optimal_team['formation']['name']}):")

    starting_xi = optimal_team["starting_xi"]
    position_names = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

    # Group and display by position
    for pos_num, pos_name in position_names.items():
        position_players = [p for p in starting_xi if p["position"] == pos_num]
        if position_players:
            print(f"\n  {pos_name}:")
            for player in position_players:
                print(
                    f"    - {player['name']} ({player['team_name']}) - {player['predicted_points']:.1f}pts "
                    f"- £{player['price']:.1f}m"
                )

    # Display Bench
    print(f"\nBENCH (4 players):")
    bench = optimal_team["bench"]
    for i, player in enumerate(bench, 1):
        pos_name = position_names.get(player["position"], "UNK")
        print(
            f"  {i}. {player['name']} ({pos_name}) - {player['predicted_points']:.1f}pts - £{player['price']:.1f}m"
        )

    # Team summary stats
    print(f"\nTEAM STATISTICS:")
    team_count = {}
    for player in optimal_team["squad"]:
        team_name = player["team_name"]
        team_count[team_name] = team_count.get(team_name, 0) + 1

    print("  Team Distribution:")
    for team, count in sorted(team_count.items(), key=lambda x: x[1], reverse=True):
        print(f"    • {team}: {count} players")

    # Position breakdown
    pos_breakdown = {1: 0, 2: 0, 3: 0, 4: 0}
    for player in optimal_team["squad"]:
        pos_breakdown[player["position"]] += 1

    print(
        "  Squad Composition: "
        f"{pos_breakdown[1]} GK, {pos_breakdown[2]} DEF, "
        f"{pos_breakdown[3]} MID, {pos_breakdown[4]} FWD"
    )

except Exception as e:
    print(f"Error testing prediction model: {e}")
    import traceback

    traceback.print_exc()
