#!/usr/bin/env python3
"""
Fix player IDs by clearing and re-importing from FPL API
"""

import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("Fetching player data from FPL API...")

try:
    response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/")
    data = response.json()

    elements = data.get("elements", [])
    print(f"Found {len(elements)} players from FPL API")

    if not elements:
        print("ERROR: No players found in FPL API")
        exit(1)

    # Clear existing players table
    print("\nClearing existing players...")
    try:
        supabase.table("players").delete().neq("id", 0).execute()
        print("✅ Cleared players table")
    except Exception as e:
        print(f"⚠️ Could not clear (may already be empty): {e}")

    # Insert all players with correct FPL IDs
    print("\nInserting players with correct IDs...")

    players_to_insert = []
    for element in elements:
        player = {
            "fpl_player_id": element["id"],
            "first_name": element.get("first_name", ""),
            "second_name": element.get("second_name", ""),
            "web_name": element.get("web_name", ""),
            "team_id": element.get("team", None),
            "element_type": element.get("element_type", None),
            "status": element.get("status", "u"),
        }
        players_to_insert.append(player)

    # Insert in batches
    batch_size = 100
    inserted_count = 0

    for i in range(0, len(players_to_insert), batch_size):
        batch = players_to_insert[i : i + batch_size]
        try:
            result = supabase.table("players").insert(batch).execute()
            inserted_count += len(batch)
            print(
                f"✅ Inserted batch {i//batch_size + 1} ({inserted_count}/{len(players_to_insert)})"
            )
        except Exception as e:
            print(f"ERROR in batch {i//batch_size + 1}: {e}")
            # Continue with next batch

    print(f"\n✅ Total inserted: {inserted_count} players")
    print("\nNow run: python src/database/diagnostic.py")
    print("Then: python src/database/fast_performance_refresh.py")

except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
