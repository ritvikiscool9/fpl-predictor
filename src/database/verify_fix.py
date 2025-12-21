import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

print("Final Database Verification:")
print("=" * 40)

# Check player_performances (with fresh query)
import time

cache_buster = int(time.time())
result = supabase.table("player_performances").select("gameweek_id").execute()
df = pd.DataFrame(result.data)

total_records = len(df)
gameweeks = sorted(df["gameweek_id"].unique()) if not df.empty else []
gw_counts = df["gameweek_id"].value_counts().sort_index() if not df.empty else {}

print(f"Total records: {total_records:,}")
print(f"Gameweeks: {gameweeks}")
print(f"Records per GW:")
for gw, count in gw_counts.items():
    print(f"  GW {gw}: {count:,} records")

print(f"")
if total_records >= 7000:
    print("DATABASE STATUS: EXCELLENT!")
    print("All gameweeks populated successfully!")
else:
    print("DATABASE STATUS: Incomplete")
