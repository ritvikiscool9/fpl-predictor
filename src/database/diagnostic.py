#!/usr/bin/env python3
"""
Diagnostic script to check database schema and data
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("=" * 70)
print("DATABASE DIAGNOSTIC")
print("=" * 70)

# Check player_performances
print("\n1. PLAYER_PERFORMANCES TABLE")
print("-" * 70)
try:
    perf_response = (
        supabase.table("player_performances")
        .select("*", count="exact")
        .limit(1)
        .execute()
    )
    print(f"Total records: {perf_response.count}")

    if perf_response.data:
        df = pd.DataFrame(perf_response.data)
        print(f"Columns: {list(df.columns)}")
        print("\nSample record:")
        print(df.iloc[0])
except Exception as e:
    print(f"ERROR: {e}")

# Check players
print("\n2. PLAYERS TABLE")
print("-" * 70)
try:
    players_response = (
        supabase.table("players").select("*", count="exact").limit(1).execute()
    )
    print(f"Total records: {players_response.count}")

    if players_response.data:
        df = pd.DataFrame(players_response.data)
        print(f"Columns: {list(df.columns)}")
        print("\nSample record:")
        print(df.iloc[0])
except Exception as e:
    print(f"ERROR: {e}")

# Check for merge compatibility
print("\n3. MERGE COMPATIBILITY CHECK")
print("-" * 70)
try:
    perf_response = (
        supabase.table("player_performances")
        .select("player_id", count="exact")
        .limit(5)
        .execute()
    )
    players_response = (
        supabase.table("players").select("fpl_player_id").limit(5).execute()
    )

    if perf_response.data and players_response.data:
        perf_ids = [r["player_id"] for r in perf_response.data]
        player_ids = [r["fpl_player_id"] for r in players_response.data]

        print(f"Sample player_performances.player_id: {perf_ids}")
        print(f"Sample players.fpl_player_id: {player_ids}")

        if perf_ids[0] in player_ids:
            print("✅ IDs match - merge should work")
        else:
            print("❌ IDs don't match - merge will fail")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
