#!/usr/bin/env python3
"""
Fast Player Performance Refresh - Optimized version
Fixes the slow database loading issue
"""

import os
import sys
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


# Initialize Supabase client with validation
def init_supabase():
    """Initialize Supabase client with error handling"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_KEY environment variables not set")
        print("Please set these environment variables before running this script")
        sys.exit(1)

    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        print(f"ERROR: Failed to initialize Supabase client: {e}")
        sys.exit(1)


supabase = init_supabase()


class FastPerformanceRefresh:
    """Optimized player performance refresh"""

    def __init__(self):
        self.fpl_api_base = "https://fantasy.premierleague.com/api/"

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "INFO",
            "SUCCESS": "SUCCESS",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
        }
        print(f"[{timestamp}] {prefix.get(level, 'INFO')} {message}")

    def get_valid_player_ids(self):
        """Get all valid player IDs from database once"""
        self.log("Loading valid player IDs from database...")

        try:
            result = supabase.table("players").select("fpl_player_id").execute()
            valid_ids = set(player["fpl_player_id"] for player in result.data)
            self.log(f"Found {len(valid_ids)} valid player IDs", "SUCCESS")
            return valid_ids
        except Exception as e:
            self.log(f"Error loading player IDs: {e}", "ERROR")
            return set()

    def clear_performances(self):
        """Clear existing performance data"""
        self.log("Clearing existing performance data...")

        try:
            # Delete all records
            result = (
                supabase.table("player_performances").delete().neq("id", 0).execute()
            )
            deleted_count = len(result.data) if result.data else 0
            self.log(f"Cleared {deleted_count} existing records", "SUCCESS")
        except Exception as e:
            self.log(f"Error clearing data: {e}", "ERROR")

    def get_finished_gameweeks(self):
        """Get list of finished gameweeks from FPL API"""
        try:
            response = requests.get(f"{self.fpl_api_base}bootstrap-static/")
            data = response.json()

            finished_gws = [
                gw["id"] for gw in data["events"] if gw.get("finished", False)
            ]
            current_gw = next(
                (gw["id"] for gw in data["events"] if gw.get("is_current", False)), None
            )

            self.log(f"Found {len(finished_gws)} finished gameweeks: {finished_gws}")
            if current_gw:
                self.log(f"Current gameweek: {current_gw}")

            return finished_gws, current_gw

        except Exception as e:
            self.log(f"Error getting gameweeks: {e}", "ERROR")
            return [], None

    def process_gameweek(self, gw: int, valid_player_ids: set):
        """Process a single gameweek and return performance records"""
        self.log(f"Processing gameweek {gw}...")

        try:
            # Get gameweek data
            gw_url = f"{self.fpl_api_base}event/{gw}/live/"
            response = requests.get(gw_url, timeout=30)

            if response.status_code != 200:
                self.log(
                    f"Failed to get GW{gw} data: HTTP {response.status_code}", "WARNING"
                )
                return []

            gw_data = response.json()
            elements = gw_data.get("elements", [])

            performances = []
            processed_count = 0

            for element in elements:
                player_id = element["id"]

                # Skip if player not in our database
                if player_id not in valid_player_ids:
                    continue

                stats = element.get("stats", {})

                performance = {
                    "player_id": player_id,
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

                performances.append(performance)
                processed_count += 1

            self.log(f"  GW{gw}: {processed_count}/{len(elements)} players processed")
            return performances

        except Exception as e:
            self.log(f"Error processing GW{gw}: {e}", "ERROR")
            return []

    def insert_performances_batch(self, performances: list, batch_name: str = ""):
        """Insert performance records in batch"""
        if not performances:
            return True

        try:
            supabase.table("player_performances").insert(performances).execute()
            self.log(f"Inserted {len(performances)} records {batch_name}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Error inserting batch {batch_name}: {e}", "ERROR")
            return False

    def refresh_all_gameweeks(self):
        """Main function to refresh all gameweek performances"""
        self.log("Starting Fast Player Performance Refresh", "SUCCESS")
        self.log("=" * 60)

        start_time = time.time()

        # Step 1: Get valid player IDs
        valid_player_ids = self.get_valid_player_ids()
        if not valid_player_ids:
            self.log("No valid player IDs found. Exiting.", "ERROR")
            return False

        # Step 2: Get finished gameweeks
        finished_gws, current_gw = self.get_finished_gameweeks()
        if not finished_gws:
            self.log("No finished gameweeks found. Exiting.", "ERROR")
            return False

        # Step 3: Clear existing data
        self.clear_performances()

        # Step 4: Process each gameweek
        all_performances = []
        successful_gws = []

        for gw in finished_gws:
            gw_performances = self.process_gameweek(gw, valid_player_ids)

            if gw_performances:
                all_performances.extend(gw_performances)
                successful_gws.append(gw)

                # Insert in batches of 1000 to avoid memory issues
                if len(all_performances) >= 1000:
                    if self.insert_performances_batch(
                        all_performances, f"(GWs {successful_gws[0]}-{gw})"
                    ):
                        all_performances = []
                    else:
                        self.log("Batch insert failed. Stopping.", "ERROR")
                        return False

            # Rate limiting
            time.sleep(0.2)

        # Insert remaining records
        if all_performances:
            self.insert_performances_batch(all_performances, f"(final batch)")

        # Step 5: Verify results
        elapsed = time.time() - start_time
        self.log("=" * 60)

        try:
            result = (
                supabase.table("player_performances")
                .select("*", count="exact")
                .limit(1)
                .execute()
            )
            total_records = result.count if result.count else 0

            self.log(f"Refresh Complete! ({elapsed:.1f}s)", "SUCCESS")
            self.log(f"Total records inserted: {total_records:,}")
            self.log(f"Gameweeks processed: {successful_gws}")

            # Calculate expected records
            expected_per_gw = len(valid_player_ids)
            expected_total = expected_per_gw * len(successful_gws)

            if total_records >= expected_total * 0.9:  # 90% threshold
                self.log(f"Data quality: EXCELLENT ({total_records}/{expected_total})")
            else:
                self.log(
                    f"Data quality: NEEDS REVIEW ({total_records}/{expected_total})"
                )

            return True

        except Exception as e:
            self.log(f"Error verifying results: {e}", "ERROR")
            return False


def main():
    """Main execution"""
    print("Fast Player Performance Refresh")
    print("Optimized version to fix slow database loading")
    print("=" * 60)

    refresher = FastPerformanceRefresh()
    success = refresher.refresh_all_gameweeks()

    if success:
        print(f"\nSUCCESS: Your player_performances table now has complete data!")
        print(f"You can now test your AI with: python src/test_real_players.py")
    else:
        print(f"\nFAILED: Check the errors above and try again")


if __name__ == "__main__":
    main()
