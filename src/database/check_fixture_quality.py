"""
Check fixture data quality and inconsistencies
"""

import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_fixture_data_quality():
    """Check fixture data for inconsistencies"""
    print("Checking Fixture Data Quality...")
    print("=" * 50)

    # Check gameweeks table
    print("\nGAMEWEEKS TABLE:")
    try:
        gameweeks_result = supabase.table("gameweeks").select("*").order("id").execute()
        if gameweeks_result.data:
            gw_df = pd.DataFrame(gameweeks_result.data)
            print(f"Total gameweeks: {len(gw_df)}")

            # Show recent gameweeks
            if not gw_df.empty:
                recent_gws = gw_df.tail(5)
                print("\nRecent gameweeks:")
                for _, row in recent_gws.iterrows():
                    status = "FINISHED" if row.get("is_finished") else "UPCOMING"
                    current = "CURRENT" if row.get("is_current") else ""
                    print(
                        f"  GW {row.get('id', 'N/A')}: {row.get('deadline_time', 'N/A')} - {status} {current}"
                    )
        else:
            print("No gameweeks found")

    except Exception as e:
        print(f"❌ Error checking gameweeks: {e}")

    # Check fixtures table
    print("\nFIXTURES TABLE:")
    try:
        fixtures_result = (
            supabase.table("fixtures")
            .select("*")
            .order("gameweek_id", ascending=False)
            .limit(20)
            .execute()
        )
        if fixtures_result.data:
            fixtures_df = pd.DataFrame(fixtures_result.data)
            print(f"Total fixtures: {len(fixtures_df)}")

            # Analyze by gameweek
            if "gameweek_id" in fixtures_df.columns:
                # gw_analysis = (
                #     fixtures_df.groupby("gameweek_id")
                #     .agg(
                #         {
                #             "finished": ["count", "sum"],
                #             "team_home_score": lambda x: x.notna().sum(),
                #             "team_away_score": lambda x: x.notna().sum(),
                #         }
                #     )
                #     .round(2)
                # )

                print("\nGameweek Analysis:")
                print("GW | Total | Finished | With Scores")
                print("-" * 35)

                for gw in sorted(fixtures_df["gameweek_id"].unique())[
                    -5:
                ]:  # Last 5 GWs
                    gw_fixtures = fixtures_df[fixtures_df["gameweek_id"] == gw]
                    total = len(gw_fixtures)
                    finished = (
                        gw_fixtures["finished"].sum()
                        if "finished" in gw_fixtures.columns
                        else 0
                    )
                    with_scores = (
                        gw_fixtures["team_home_score"].notna().sum()
                        if "team_home_score" in gw_fixtures.columns
                        else 0
                    )
                    print(f"{gw:2} | {total:5} | {finished:8} | {with_scores:11}")

            # Show sample of recent fixtures
            print(f"\nSample recent fixtures:")
            sample_cols = [
                "gameweek_id",
                "team_home_id",
                "team_away_id",
                "finished",
                "team_home_score",
                "team_away_score",
            ]
            available_cols = [col for col in sample_cols if col in fixtures_df.columns]

            if available_cols:
                print(fixtures_df[available_cols].head(10).to_string(index=False))

        else:
            print("No fixtures found")

    except Exception as e:
        print(f"❌ Error checking fixtures: {e}")

    # Check for data inconsistencies
    print(f"\nINCONSISTENCY CHECK:")
    try:
        # Find gameweeks marked as finished
        finished_gws_result = (
            supabase.table("gameweeks")
            .select("id, is_finished")
            .eq("is_finished", True)
            .execute()
        )
        if finished_gws_result.data:
            finished_gws = [gw["id"] for gw in finished_gws_result.data]
            print(f"Gameweeks marked as finished: {finished_gws}")

            # Check if their fixtures have scores
            for gw in finished_gws[-3:]:  # Check last 3 finished GWs
                fixtures_result = (
                    supabase.table("fixtures")
                    .select("*")
                    .eq("gameweek_id", gw)
                    .execute()
                )
                if fixtures_result.data:
                    fixtures_df = pd.DataFrame(fixtures_result.data)

                    finished_count = (
                        fixtures_df["finished"].sum()
                        if "finished" in fixtures_df.columns
                        else 0
                    )
                    with_scores = (
                        fixtures_df["team_home_score"].notna().sum()
                        if "team_home_score" in fixtures_df.columns
                        else 0
                    )

                    if finished_count == 0 or with_scores == 0:
                        print(
                            f"  GW {gw}: Marked finished but {finished_count}/{len(fixtures_df)} fixtures finished, {with_scores}/{len(fixtures_df)} have scores"
                        )
                    else:
                        print(
                            f"  GW {gw}: {finished_count}/{len(fixtures_df)} fixtures finished, {with_scores}/{len(fixtures_df)} have scores"
                        )

    except Exception as e:
        print(f"Error checking inconsistencies: {e}")


if __name__ == "__main__":
    check_fixture_data_quality()
