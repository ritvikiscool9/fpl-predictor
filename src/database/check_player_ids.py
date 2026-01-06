#!/usr/bin/env python3
"""
Check a broader sample of players to see what IDs exist
"""

import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("Checking 20 sample players from database:")
print("-" * 70)

try:
    response = (
        supabase.table("players")
        .select("id, fpl_player_id, web_name")
        .limit(20)
        .execute()
    )

    if response.data:
        df = pd.DataFrame(response.data)
        print(df.to_string(index=False))

        print("\n" + "-" * 70)
        print(f"Min fpl_player_id: {df['fpl_player_id'].min()}")
        print(f"Max fpl_player_id: {df['fpl_player_id'].max()}")

        # Check if we have the new IDs
        if df["fpl_player_id"].max() > 100:
            print("✅ Table has been updated with correct IDs")
        else:
            print("❌ Table still has old IDs - fix didn't work")
    else:
        print("No players found!")

except Exception as e:
    print(f"ERROR: {e}")
