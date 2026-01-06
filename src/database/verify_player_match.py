#!/usr/bin/env python3
"""
Check if player_performances IDs exist in players table
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("Checking if performance data IDs exist in players table...")
print("-" * 70)

try:
    # Get sample IDs from player_performances
    perf_response = (
        supabase.table("player_performances").select("player_id").limit(10).execute()
    )
    perf_ids = [r["player_id"] for r in perf_response.data]
    print(f"Sample player_performances IDs: {perf_ids}")

    # Check if these IDs exist in players table
    for pid in perf_ids[:3]:
        player_response = (
            supabase.table("players")
            .select("id, fpl_player_id, web_name")
            .eq("fpl_player_id", pid)
            .execute()
        )

        if player_response.data:
            player = player_response.data[0]
            print(f"✅ ID {pid} found: {player['web_name']} (ID: {player['id']})")
        else:
            print(f"❌ ID {pid} NOT FOUND in players table")

    # Get total counts
    perf_count = (
        supabase.table("player_performances")
        .select("player_id", count="exact")
        .limit(1)
        .execute()
        .count
    )
    players_count = (
        supabase.table("players").select("id", count="exact").limit(1).execute().count
    )

    print(f"\nTotal player_performances records: {perf_count}")
    print(f"Total players in table: {players_count}")

except Exception as e:
    print(f"ERROR: {e}")
