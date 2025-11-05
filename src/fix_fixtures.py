"""
Fix fixture data by updating match results from FPL API
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def update_fixture_results():
    """Update fixture results from FPL API"""
    print("🔄 Updating fixture results from FPL API...")

    try:
        # Get fixture data from FPL API
        fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"
        response = requests.get(fixtures_url)
        fpl_fixtures = response.json()

        print(f"✅ Fetched {len(fpl_fixtures)} fixtures from FPL API")

        # Get current fixtures from database
        db_fixtures_result = supabase.table("fixtures").select("*").execute()
        db_fixtures = pd.DataFrame(db_fixtures_result.data)

        print(f"✅ Found {len(db_fixtures)} fixtures in database")

        # Update fixtures with results
        updated_count = 0

        for fpl_fixture in fpl_fixtures:
            # Skip if not finished
            if not fpl_fixture.get("finished"):
                continue

            fpl_id = fpl_fixture["id"]
            home_score = fpl_fixture.get("team_h_score")
            away_score = fpl_fixture.get("team_a_score")

            # Find matching fixture in database
            matching_fixtures = db_fixtures[db_fixtures["fpl_fixture_id"] == fpl_id]

            if not matching_fixtures.empty:
                fixture_id = matching_fixtures.iloc[0]["id"]

                # Update the fixture
                update_data = {
                    "finished": True,
                    "team_home_score": home_score,
                    "team_away_score": away_score,
                }

                supabase.table("fixtures").update(update_data).eq(
                    "id", fixture_id
                ).execute()
                updated_count += 1

                if updated_count <= 5:  # Show first few updates
                    print(f"  ✅ Updated fixture {fpl_id}: {home_score}-{away_score}")

        print(f"\n🎯 Updated {updated_count} fixtures with results")

        # Verify the fix
        print(f"\n🔍 Verifying fix...")

        # Check gameweeks 8-10
        for gw in [8, 9, 10]:
            gw_fixtures_result = (
                supabase.table("fixtures").select("*").eq("gameweek_id", gw).execute()
            )
            if gw_fixtures_result.data:
                gw_fixtures_df = pd.DataFrame(gw_fixtures_result.data)

                finished_count = gw_fixtures_df["finished"].sum()
                with_scores = gw_fixtures_df["team_home_score"].notna().sum()
                total = len(gw_fixtures_df)

                if finished_count > 0 or with_scores > 0:
                    print(
                        f"  ✅ GW {gw}: {finished_count}/{total} finished, {with_scores}/{total} with scores"
                    )
                else:
                    print(
                        f"  ❌ GW {gw}: Still no results - {finished_count}/{total} finished, {with_scores}/{total} with scores"
                    )

        return updated_count

    except Exception as e:
        print(f"❌ Error updating fixtures: {e}")
        return 0


if __name__ == "__main__":
    updated_count = update_fixture_results()
    if updated_count > 0:
        print(f"\n🎉 Successfully updated {updated_count} fixtures!")
        print("🔄 Database inconsistency should now be resolved.")
    else:
        print(f"\n⚠️  No fixtures were updated. Check FPL API or fixture mapping.")
