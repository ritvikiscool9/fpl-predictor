# Create check_database.py
import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_existing_data():
    """Check what data we already have"""
    print("🔍 Checking existing database content...")

    tables_to_check = [
        "historical_player_stats",
        "teams",
        "players",
        "fixtures",
        "current_team_stats",
    ]

    for table in tables_to_check:
        try:
            result = supabase.table(table).select("*", count="exact").limit(1).execute()
            count = result.count if result.count else 0

            if count > 0:
                # Get sample data
                sample = supabase.table(table).select("*").limit(3).execute()
                df = pd.DataFrame(sample.data)

                print(f"\n✅ {table}: {count:,} records")
                print(f"   Columns: {list(df.columns)}")

                # Show season info if available
                if "season" in df.columns and not df.empty:
                    seasons = df["season"].unique()
                    print(f"   Seasons: {list(seasons)}")

                # Show sample player names if available
                if "web_name" in df.columns and not df.empty:
                    names = df["web_name"].dropna().head(3).tolist()
                    print(f"   Sample players: {names}")

            else:
                print(f"\n❌ {table}: Empty or doesn't exist")

        except Exception as e:
            print(f"\n❌ {table}: Error - {e}")


if __name__ == "__main__":
    check_existing_data()
