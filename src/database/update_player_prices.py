#!/usr/bin/env python3
"""
Update Current Player Prices
Fetches current FPL player prices and selection percentages from the API
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.supabase_client import get_supabase_client

load_dotenv()


class PlayerPriceUpdater:
    """Update current player prices from FPL API"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.fpl_api_base = "https://fantasy.premierleague.com/api/"

    def log(self, message: str, level: str = "INFO"):
        """Simple logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def get_current_fpl_data(self):
        """Fetch current player data from FPL API"""
        self.log("Fetching current player data from FPL API...")

        try:
            response = requests.get(f"{self.fpl_api_base}bootstrap-static/")
            response.raise_for_status()
            data = response.json()

            elements = data["elements"]  # Player data

            self.log(
                f"SUCCESS: Retrieved data for {len(elements)} players from FPL API"
            )
            return elements

        except Exception as e:
            self.log(f"ERROR: Failed to fetch FPL data: {e}", "ERROR")
            return []

    def update_player_prices(self):
        """Update player_performances table with latest FPL pricing data"""
        self.log("Starting player price update in player_performances table...")

        # Get current FPL data
        fpl_players = self.get_current_fpl_data()
        if not fpl_players:
            self.log("ERROR: No FPL data available", "ERROR")
            return False

        # Create a mapping of FPL player ID to pricing data
        # NOTE: The FPL API `now_cost` is expected as an integer in tenths of £m
        # (for example, 45 == £4.5m). To avoid inconsistencies with other parts
        # of the codebase (which divide by 10 to get £m), validate and
        # normalize here. We'll accept a few input formats (int, float, str)
        # and enforce a reasonable FPL range: 35-150 (i.e. £3.5m - £15.0m).
        fpl_pricing = {}
        for player in fpl_players:
            fpl_player_id = player.get("id")
            raw_cost = player.get("now_cost")
            selected_raw = player.get("selected_by_percent", 0)

            # Parse and normalize now_cost to integer tenths (e.g., 45)
            try:
                if raw_cost is None:
                    raise ValueError("now_cost is None")

                now_cost_float = float(raw_cost)

                # If API returned a value that looks like millions
                # (e.g., 4.5) convert to tenths by multiplying by 10.
                if 3.5 <= now_cost_float < 35:
                    # most likely provided as 4.5 (millions) -> convert to 45
                    now_cost = int(round(now_cost_float * 10))
                    self.log(
                        f"Normalized now_cost {raw_cost} -> {now_cost} (tenths) for player {fpl_player_id}"
                    )
                else:
                    now_cost = int(round(now_cost_float))

                # Validate within expected FPL range (35 = £3.5m to 150 = £15.0m)
                if not (35 <= now_cost <= 150):
                    self.log(
                        f"WARNING: now_cost {now_cost} out of expected range (35-150) for player {fpl_player_id}. Skipping.",
                        "WARNING",
                    )
                    continue

            except Exception as e:
                self.log(
                    f"WARNING: Could not parse now_cost for player {fpl_player_id}: {e}. Skipping.",
                    "WARNING",
                )
                continue

            # Parse selected_by_percent safely
            try:
                selected_by_percent = (
                    float(selected_raw) if selected_raw not in (None, "") else 0.0
                )
            except Exception:
                selected_by_percent = 0.0

            fpl_pricing[fpl_player_id] = {
                "now_cost": now_cost,
                "selected_by_percent": selected_by_percent,
            }

        self.log(f"Retrieved pricing data for {len(fpl_pricing)} players")

        # Update all records in player_performances table
        # We need to map fpl_player_id to player_id first
        self.log("Getting player ID mappings...")
        try:
            players_result = (
                self.supabase.table("players").select("id, fpl_player_id").execute()
            )

            if not players_result.data:
                self.log("ERROR: No player mappings found", "ERROR")
                return False

            # Create mapping from fpl_player_id to database player_id
            player_mapping = {}
            for player in players_result.data:
                player_mapping[player["fpl_player_id"]] = player["id"]

            self.log(f"Found {len(player_mapping)} player mappings")

        except Exception as e:
            self.log(f"ERROR getting player mappings: {e}", "ERROR")
            return False

        # Update player_performances records
        updates_made = 0
        errors = 0

        for fpl_player_id, pricing_data in fpl_pricing.items():
            if fpl_player_id in player_mapping:
                try:
                    db_player_id = player_mapping[fpl_player_id]

                    # Update all records for this player in player_performances
                    result = (
                        self.supabase.table("player_performances")
                        .update(
                            {
                                "now_cost": pricing_data["now_cost"],
                                "selected_by_percent": pricing_data[
                                    "selected_by_percent"
                                ],
                            }
                        )
                        .eq("player_id", db_player_id)
                        .execute()
                    )

                    if result.data:
                        updates_made += len(result.data)

                except Exception as e:
                    self.log(f"ERROR updating player {fpl_player_id}: {e}", "ERROR")
                    errors += 1

        self.log(
            f"SUCCESS: Updated {updates_made} player performance records with pricing"
        )
        if errors > 0:
            self.log(f"WARNING: {errors} errors occurred", "WARNING")

        return updates_made > 0

    def verify_updates(self):
        """Verify that prices were updated successfully in player_performances"""
        self.log("Verifying price updates in player_performances table...")

        try:
            # Check for non-null prices in player_performances
            result = (
                self.supabase.table("player_performances")
                .select("player_id, now_cost, selected_by_percent")
                .not_.is_("now_cost", "null")
                .limit(5)
                .execute()
            )

            if result.data:
                self.log(
                    f"SUCCESS: Found {len(result.data)} performance records with updated prices"
                )
                self.log("Sample updated prices:")
                for record in result.data:
                    cost_in_millions = record["now_cost"] / 10.0
                    self.log(
                        f"  Player {record['player_id']}: £{cost_in_millions}m, {record['selected_by_percent']}% selected"
                    )

                # Count total updated records
                count_result = (
                    self.supabase.table("player_performances")
                    .select("*", count="exact")
                    .not_.is_("now_cost", "null")
                    .execute()
                )

                self.log(
                    f"Total performance records with prices: {count_result.count}/7302"
                )

                # Check unique players with prices
                unique_result = (
                    self.supabase.table("player_performances")
                    .select("player_id")
                    .not_.is_("now_cost", "null")
                    .execute()
                )

                if unique_result.data:
                    unique_players = len(
                        set(record["player_id"] for record in unique_result.data)
                    )
                    self.log(f"Unique players with pricing: {unique_players}/743")

                return True
            else:
                self.log("ERROR: No updated prices found", "ERROR")
                return False

        except Exception as e:
            self.log(f"ERROR during verification: {e}", "ERROR")
            return False


def main():
    """Main execution"""
    print("Current Player Price Updater")
    print("=" * 50)

    updater = PlayerPriceUpdater()

    # Update prices
    success = updater.update_player_prices()

    if success:
        # Verify updates
        updater.verify_updates()
        print(
            f"\nSUCCESS: Player prices updated! You can now test the AI with complete pricing data."
        )
    else:
        print(f"\nERROR: Failed to update player prices. Check the logs above.")


if __name__ == "__main__":
    main()
