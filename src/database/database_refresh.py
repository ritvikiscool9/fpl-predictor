#!/usr/bin/env python3
"""
Unified FPL Database Refresh System
Replaces and combines: populate_db.py, data_collector.py, fix_fixtures.py
Comprehensive refresh of all FPL data from multiple sources
"""

import os
import sys
import requests
import pandas as pd
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


class FPLDatabaseRefresh:
    """Unified database refresh system for all FPL data"""

    def __init__(self):
        self.fpl_api_base = "https://fantasy.premierleague.com/api/"
        self.github_base = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/"

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        print(f"[{timestamp}] {prefix.get(level, 'ℹ️')} {message}")

    def clear_table(self, table_name: str, condition: dict = None):
        """Safely clear table data with optional condition"""
        try:
            if condition:
                result = supabase.table(table_name).delete().match(condition).execute()
            else:
                # Delete all records (use with caution)
                result = supabase.table(table_name).delete().neq("id", 0).execute()

            deleted_count = len(result.data) if result.data else 0
            self.log(f"Cleared {deleted_count} records from {table_name}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Error clearing {table_name}: {e}", "ERROR")
            return False

    def refresh_teams_data(self):
        """Refresh teams data from FPL API"""
        self.log("Refreshing teams data...")

        try:
            # Get teams from FPL API
            response = requests.get(f"{self.fpl_api_base}bootstrap-static/")
            data = response.json()
            teams = data["teams"]

            # Clear existing teams
            self.clear_table("teams")

            # Insert fresh teams data
            teams_data = []
            for team in teams:
                teams_data.append(
                    {
                        "id": team["id"],
                        "fpl_team_id": team["id"],
                        "name": team["name"],
                        "short_name": team["short_name"],
                        "code": team["code"],
                    }
                )

            supabase.table("teams").insert(teams_data).execute()
            self.log(f"Refreshed {len(teams_data)} teams", "SUCCESS")

        except Exception as e:
            self.log(f"Error refreshing teams: {e}", "ERROR")

    def refresh_players_data(self):
        """Refresh current players data from FPL API"""
        self.log("Refreshing players data...")

        try:
            # Get players from FPL API
            response = requests.get(f"{self.fpl_api_base}bootstrap-static/")
            data = response.json()
            players = data["elements"]

            # Clear existing players
            self.clear_table("players")

            # Insert fresh players data
            players_data = []
            for player in players:
                players_data.append(
                    {
                        "fpl_player_id": player["id"],
                        "first_name": player["first_name"],
                        "second_name": player["second_name"],
                        "web_name": player["web_name"],
                        "team_id": player["team"],
                        "element_type": player["element_type"],
                        "status": player["status"],
                    }
                )

            supabase.table("players").insert(players_data).execute()
            self.log(f"Refreshed {len(players_data)} players", "SUCCESS")

        except Exception as e:
            self.log(f"Error refreshing players: {e}", "ERROR")

    def refresh_gameweeks_data(self):
        """Refresh gameweeks data from FPL API"""
        self.log("Refreshing gameweeks data...")

        try:
            # Get gameweeks from FPL API
            response = requests.get(f"{self.fpl_api_base}bootstrap-static/")
            data = response.json()
            gameweeks = data["events"]

            # Clear existing gameweeks
            self.clear_table("gameweeks")

            # Insert fresh gameweeks data
            gameweeks_data = []
            for gw in gameweeks:
                gameweeks_data.append(
                    {
                        "id": gw["id"],
                        "name": gw["name"],
                        "deadline_time": gw["deadline_time"],
                        "is_current": gw.get("is_current", False),
                        "is_next": gw.get("is_next", False),
                        "is_finished": gw.get("finished", False),
                    }
                )

            supabase.table("gameweeks").insert(gameweeks_data).execute()
            self.log(f"Refreshed {len(gameweeks_data)} gameweeks", "SUCCESS")

        except Exception as e:
            self.log(f"Error refreshing gameweeks: {e}", "ERROR")

    def refresh_fixtures_data(self):
        """Refresh fixtures data with results from FPL API"""
        self.log("Refreshing fixtures data...")

        try:
            # Get fixtures from FPL API
            response = requests.get(f"{self.fpl_api_base}fixtures/")
            fixtures = response.json()

            # Clear existing fixtures
            self.clear_table("fixtures")

            # Insert fresh fixtures data
            fixtures_data = []
            for fixture in fixtures:
                fixtures_data.append(
                    {
                        "fpl_fixture_id": fixture["id"],
                        "gameweek_id": fixture["event"],
                        "team_home_id": fixture["team_h"],
                        "team_away_id": fixture["team_a"],
                        "team_home_score": fixture.get("team_h_score"),
                        "team_away_score": fixture.get("team_a_score"),
                        "finished": fixture.get("finished", False),
                        "kickoff_time": fixture["kickoff_time"],
                        "difficulty_home": fixture.get("team_h_difficulty", 3),
                        "difficulty_away": fixture.get("team_a_difficulty", 3),
                    }
                )

            supabase.table("fixtures").insert(fixtures_data).execute()
            self.log(f"Refreshed {len(fixtures_data)} fixtures", "SUCCESS")

        except Exception as e:
            self.log(f"Error refreshing fixtures: {e}", "ERROR")

    def refresh_current_team_stats(self):
        """Refresh current team stats"""
        self.log("Refreshing current team stats...")

        try:
            # Get teams data for stats calculation
            response = requests.get(f"{self.fpl_api_base}bootstrap-static/")
            data = response.json()
            teams = data["teams"]

            # Clear existing stats
            self.clear_table("current_team_stats")

            # Insert fresh team stats
            stats_data = []
            current_gw = next(
                (gw["id"] for gw in data["events"] if gw.get("is_current")), 1
            )

            for team in teams:
                stats_data.append(
                    {
                        "team_id": team["id"],
                        "gameweek_id": current_gw,
                        "strength": team.get("strength", 3),
                        "strength_overall_home": team.get(
                            "strength_overall_home", 1000
                        ),
                        "strength_overall_away": team.get(
                            "strength_overall_away", 1000
                        ),
                        "strength_attack_home": team.get("strength_attack_home", 1000),
                        "strength_attack_away": team.get("strength_attack_away", 1000),
                        "strength_defence_home": team.get(
                            "strength_defence_home", 1000
                        ),
                        "strength_defence_away": team.get(
                            "strength_defence_away", 1000
                        ),
                        "wins": team.get("win", 0),
                        "draws": team.get("draw", 0),
                        "losses": team.get("loss", 0),
                        "points": team.get("points", 0),
                        "position": team.get("position", 20),
                        "form": team.get("form", "0"),
                    }
                )

            supabase.table("current_team_stats").insert(stats_data).execute()
            self.log(f"Refreshed {len(stats_data)} team stats", "SUCCESS")

        except Exception as e:
            self.log(f"Error refreshing team stats: {e}", "ERROR")

    def refresh_historical_player_stats(self, seasons: list = ["2022-23", "2023-24"]):
        """Refresh historical player stats from GitHub data"""
        self.log(f"Refreshing historical data for seasons: {seasons}...")

        try:
            # Clear existing historical data
            self.clear_table("historical_player_stats")

            all_records = []

            for season in seasons:
                self.log(f"Processing season {season}...")

                # Get gameweeks for this season
                try:
                    gws_url = f"{self.github_base}{season}/gws/merged_gw.csv"
                    gws_df = pd.read_csv(gws_url)

                    self.log(f"Found {len(gws_df)} records for {season}")

                    # Process in chunks to avoid memory issues
                    chunk_size = 1000
                    for i in range(0, len(gws_df), chunk_size):
                        chunk = gws_df.iloc[i : i + chunk_size]

                        for _, row in chunk.iterrows():
                            record = {
                                "season": season,
                                "gameweek": int(row.get("GW", 0)),
                                "fpl_player_id": int(row.get("element", 0)),
                                "total_points": int(row.get("total_points", 0)),
                                "minutes": int(row.get("minutes", 0)),
                                "goals_scored": int(row.get("goals_scored", 0)),
                                "assists": int(row.get("assists", 0)),
                                "clean_sheets": int(row.get("clean_sheets", 0)),
                                "goals_conceded": int(row.get("goals_conceded", 0)),
                                "own_goals": int(row.get("own_goals", 0)),
                                "penalties_saved": int(row.get("penalties_saved", 0)),
                                "penalties_missed": int(row.get("penalties_missed", 0)),
                                "yellow_cards": int(row.get("yellow_cards", 0)),
                                "red_cards": int(row.get("red_cards", 0)),
                                "saves": int(row.get("saves", 0)),
                                "bonus": int(row.get("bonus", 0)),
                                "bps": int(row.get("bps", 0)),
                                "influence": float(row.get("influence", 0)),
                                "creativity": float(row.get("creativity", 0)),
                                "threat": float(row.get("threat", 0)),
                                "ict_index": float(row.get("ict_index", 0)),
                                "value": int(row.get("value", 40)),
                                "selected": float(row.get("selected", 0)),
                                "transfers_in": int(row.get("transfers_in", 0)),
                                "transfers_out": int(row.get("transfers_out", 0)),
                            }
                            all_records.append(record)

                        # Insert chunk to database
                        if len(all_records) >= chunk_size:
                            supabase.table("historical_player_stats").insert(
                                all_records
                            ).execute()
                            self.log(
                                f"Inserted {len(all_records)} records for {season}"
                            )
                            all_records = []

                except Exception as e:
                    self.log(f"Error processing season {season}: {e}", "WARNING")
                    continue

            # Insert remaining records
            if all_records:
                supabase.table("historical_player_stats").insert(all_records).execute()
                self.log(f"Inserted final {len(all_records)} records")

            # Get total count
            result = (
                supabase.table("historical_player_stats")
                .select("*", count="exact")
                .limit(1)
                .execute()
            )
            total_count = result.count if result.count else 0
            self.log(
                f"Historical refresh complete: {total_count} total records", "SUCCESS"
            )

        except Exception as e:
            self.log(f"Error refreshing historical data: {e}", "ERROR")

    def refresh_player_performances_current_season(self):
        """Refresh current season player performances for all gameweeks"""
        self.log("Refreshing current season player performances...")

        try:
            # Clear existing performances
            self.clear_table("player_performances")

            # Get current gameweek
            response = requests.get(f"{self.fpl_api_base}bootstrap-static/")
            data = response.json()
            current_gw = max(
                [gw["id"] for gw in data["events"] if gw.get("finished", False)],
                default=1,
            )

            self.log(f"Processing gameweeks 1 to {current_gw}...")

            all_performances = []

            # Process each finished gameweek
            for gw in range(1, current_gw + 1):
                try:
                    self.log(f"Processing gameweek {gw}...")

                    # Get live data for this gameweek
                    gw_url = f"{self.fpl_api_base}event/{gw}/live/"
                    gw_response = requests.get(gw_url)

                    if gw_response.status_code != 200:
                        self.log(f"No data available for gameweek {gw}", "WARNING")
                        continue

                    gw_data = gw_response.json()

                    # Preload valid player IDs once per run to avoid N+1 queries
                    # (player_performances.player_id stores the external FPL id)
                    if "valid_player_ids" not in locals():
                        try:
                            players_resp = (
                                supabase.table("players")
                                .select("fpl_player_id")
                                .execute()
                            )
                            if players_resp.data:
                                valid_player_ids = set(
                                    p.get("fpl_player_id")
                                    for p in players_resp.data
                                    if p.get("fpl_player_id") is not None
                                )
                                self.log(
                                    f"Loaded {len(valid_player_ids)} valid player IDs for membership checks"
                                )
                            else:
                                valid_player_ids = set()
                                self.log(
                                    "WARNING: No players found when preloading player IDs",
                                    "WARNING",
                                )
                        except Exception as e:
                            valid_player_ids = set()
                            self.log(
                                f"WARNING: Could not preload player IDs: {e}", "WARNING"
                            )

                    # Process each player's performance
                    for element in gw_data["elements"]:
                        # Skip if player not in our players table (avoid foreign key errors)
                        if element.get("id") not in valid_player_ids:
                            continue

                        stats = element["stats"]
                        performance = {
                            "player_id": element["id"],
                            "gameweek_id": gw,
                            "minutes": stats.get("minutes", 0),
                            "goals_scored": stats.get("goals_scored", 0),
                            "assists": stats.get("assists", 0),
                            "clean_sheets": stats.get("clean_sheets", 0),
                            "goals_conceded": stats.get("goals_conceded", 0),
                            "own_goals": stats.get("own_goals", 0),
                            "penalties_saved": stats.get("penalties_saved", 0),
                            "penalties_missed": stats.get("penalties_missed", 0),
                            "yellow_cards": stats.get("yellow_cards", 0),
                            "red_cards": stats.get("red_cards", 0),
                            "saves": stats.get("saves", 0),
                            "bonus": stats.get("bonus", 0),
                            "bps": stats.get("bps", 0),
                            "influence": float(stats.get("influence", 0)),
                            "creativity": float(stats.get("creativity", 0)),
                            "threat": float(stats.get("threat", 0)),
                            "ict_index": float(stats.get("ict_index", 0)),
                            "total_points": stats.get("total_points", 0),
                        }
                        all_performances.append(performance)

                    # Insert in batches
                    if len(all_performances) >= 1000:
                        supabase.table("player_performances").insert(
                            all_performances
                        ).execute()
                        self.log(
                            f"Inserted {len(all_performances)} performance records"
                        )
                        all_performances = []

                    time.sleep(0.5)  # Rate limiting

                except Exception as e:
                    self.log(f"Error processing gameweek {gw}: {e}", "WARNING")
                    continue

            # Insert remaining performances
            if all_performances:
                supabase.table("player_performances").insert(all_performances).execute()
                self.log(f"Inserted final {len(all_performances)} performance records")

            # Get total count
            result = (
                supabase.table("player_performances")
                .select("*", count="exact")
                .limit(1)
                .execute()
            )
            total_count = result.count if result.count else 0
            self.log(
                f"Player performances refresh complete: {total_count} total records",
                "SUCCESS",
            )

        except Exception as e:
            self.log(f"Error refreshing player performances: {e}", "ERROR")

    def full_database_refresh(self, include_historical: bool = True):
        """Perform complete database refresh"""
        self.log("🚀 Starting FULL DATABASE REFRESH", "SUCCESS")
        self.log("=" * 60)

        start_time = time.time()

        # Core data (always refresh)
        self.log("Phase 1: Core FPL Data")
        self.refresh_teams_data()
        self.refresh_players_data()
        self.refresh_gameweeks_data()
        self.refresh_fixtures_data()
        self.refresh_current_team_stats()

        # Current season performances (fixes your gameweek 1 issue)
        self.log("\nPhase 2: Current Season Player Performances")
        self.refresh_player_performances_current_season()

        # Historical data (optional, takes longer)
        if include_historical:
            self.log("\nPhase 3: Historical Data (This will take 10-15 minutes)")
            self.refresh_historical_player_stats(["2022-23", "2023-24"])

        # Summary
        elapsed = time.time() - start_time
        self.log("=" * 60)
        self.log(f"🎉 DATABASE REFRESH COMPLETE! ({elapsed:.1f}s)", "SUCCESS")

        # Verify refresh
        self.verify_database_health()

    def verify_database_health(self):
        """Verify database has been properly refreshed"""
        self.log("\n🔍 Database Health Check:")

        tables_to_check = [
            ("teams", 20),
            ("players", 700),
            ("gameweeks", 38),
            ("fixtures", 380),
            ("current_team_stats", 20),
            ("historical_player_stats", 40000),
            ("player_performances", 5000),
        ]

        all_healthy = True

        for table, expected_min in tables_to_check:
            try:
                result = (
                    supabase.table(table).select("*", count="exact").limit(1).execute()
                )
                count = result.count if result.count else 0

                if count >= expected_min:
                    self.log(f"  ✅ {table}: {count:,} records", "SUCCESS")
                else:
                    self.log(
                        f"  ⚠️  {table}: {count:,} records (expected >{expected_min:,})",
                        "WARNING",
                    )
                    all_healthy = False

            except Exception as e:
                self.log(f"  ❌ {table}: Error - {e}", "ERROR")
                all_healthy = False

        if all_healthy:
            self.log("\n🎉 All tables are healthy!", "SUCCESS")
        else:
            self.log("\n⚠️  Some tables may need attention", "WARNING")


def main():
    """Main execution function"""
    print("🏆 FPL Database Refresh System")
    print("=" * 60)

    refresher = FPLDatabaseRefresh()

    # Ask user what to refresh
    print("\nRefresh options:")
    print("1. Quick refresh (current data only, ~2 minutes)")
    print("2. Full refresh (current + historical, ~15 minutes)")
    print("3. Current season performances only")

    choice = input("\nEnter choice (1-3) or press Enter for full refresh: ").strip()

    if choice == "1":
        # Quick refresh
        refresher.log("Starting quick refresh...")
        refresher.refresh_teams_data()
        refresher.refresh_players_data()
        refresher.refresh_gameweeks_data()
        refresher.refresh_fixtures_data()
        refresher.refresh_current_team_stats()
        refresher.refresh_player_performances_current_season()
        refresher.verify_database_health()

    elif choice == "3":
        # Just player performances
        refresher.refresh_player_performances_current_season()
        refresher.verify_database_health()

    else:
        # Full refresh (default)
        refresher.full_database_refresh(include_historical=True)


if __name__ == "__main__":
    main()
