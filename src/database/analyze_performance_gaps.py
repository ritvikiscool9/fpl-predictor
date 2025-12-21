"""
Analyze current player_performances data to identify gaps
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def analyze_player_performances_gaps():
    """Analyze what gameweeks are missing in player_performances"""
    print("Analyzing player_performances data gaps...")
    print("=" * 60)

    try:
        # Get all player performances
        result = supabase.table("player_performances").select("gameweek_id").execute()

        if not result.data:
            print("ERROR: No player_performances data found!")
            return

        df = pd.DataFrame(result.data)

        # Analyze gameweek coverage
        gameweeks_present = sorted(df["gameweek_id"].unique())
        total_records = len(df)

        print(f"Total records: {total_records:,}")
        print(f"Gameweeks with data: {gameweeks_present}")

        # Count records per gameweek
        gw_counts = df["gameweek_id"].value_counts().sort_index()
        print(f"\nRecords per gameweek:")
        for gw, count in gw_counts.items():
            print(f"  GW {gw}: {count:,} records")

        # Identify gaps
        if gameweeks_present:
            expected_gws = list(range(1, max(gameweeks_present) + 1))
            missing_gws = [gw for gw in expected_gws if gw not in gameweeks_present]

            if missing_gws:
                print(f"\nMissing gameweeks: {missing_gws}")
            else:
                print(f"\nAll gameweeks 1-{max(gameweeks_present)} are present")

        # Check for consistency
        if len(gw_counts) > 1:
            avg_records = gw_counts.mean()
            inconsistent_gws = []

            for gw, count in gw_counts.items():
                if count < avg_records * 0.8:  # Less than 80% of average
                    inconsistent_gws.append(f"GW{gw}({count})")

            if inconsistent_gws:
                print(f"\nGameweeks with low record counts: {inconsistent_gws}")
                print(f"    Average records per GW: {avg_records:.0f}")

        return gameweeks_present, gw_counts.to_dict()

    except Exception as e:
        print(f"ERROR: Error analyzing data: {e}")
        return None, None


def check_fpl_api_availability():
    """Check what gameweeks are available from FPL API"""
    import requests

    print(f"\nChecking FPL API availability...")

    try:
        # Get current season info
        response = requests.get(
            "https://fantasy.premierleague.com/api/bootstrap-static/"
        )
        data = response.json()

        # Find finished gameweeks
        finished_gws = [gw["id"] for gw in data["events"] if gw.get("finished", False)]
        current_gw = next(
            (gw["id"] for gw in data["events"] if gw.get("is_current", False)), None
        )

        print(f"Finished gameweeks available: {finished_gws}")
        print(f"Current gameweek: {current_gw}")

        # Test API access for a specific gameweek
        if finished_gws:
            test_gw = finished_gws[-1]  # Latest finished GW
            test_url = f"https://fantasy.premierleague.com/api/event/{test_gw}/live/"
            test_response = requests.get(test_url)

            if test_response.status_code == 200:
                test_data = test_response.json()
                player_count = len(test_data.get("elements", []))
                print(
                    f"API test successful - GW{test_gw} has {player_count} player records"
                )
            else:
                print(
                    f"API test failed for GW{test_gw}: HTTP {test_response.status_code}"
                )

        return finished_gws, current_gw

    except Exception as e:
        print(f"ERROR: Error checking FPL API: {e}")
        return None, None


def main():
    print("FPL Database - Player Performances Gap Analysis")
    print("=" * 70)

    # Analyze current database
    db_gameweeks, db_counts = analyze_player_performances_gaps()

    # Check API availability
    api_gameweeks, current_gw = check_fpl_api_availability()

    # Compare and recommend
    if db_gameweeks and api_gameweeks:
        missing_from_db = [gw for gw in api_gameweeks if gw not in db_gameweeks]

        print(f"\nRECOMMENDATION:")
        if missing_from_db:
            print(f"  Your database is missing data for: {missing_from_db}")
            print(f"  TIP: Run: echo 3 | python database_refresh.py")
            print(f"     This will populate all missing gameweeks")
        else:
            print(f"  Your database has all available gameweeks!")

        if db_counts and len(set(db_counts.values())) > 1:
            print(f"  Some gameweeks have inconsistent record counts")
            print(f"  TIP: Consider refreshing to ensure data quality")


if __name__ == "__main__":
    main()
