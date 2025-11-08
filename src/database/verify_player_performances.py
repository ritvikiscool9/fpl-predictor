#!/usr/bin/env python3
"""
Comprehensive verification of player_performances table
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "config"))
from supabase_client import get_supabase_client


def verify_player_performances():
    """Verify the state of player_performances table"""
    supabase = get_supabase_client()

    print("🔍 Verifying player_performances table...")

    # Method 1: Count per gameweek using individual queries
    print("\n📊 Method 1: Individual gameweek queries")
    total_individual = 0
    gameweeks_with_data = []

    for gw in range(1, 11):
        try:
            result = (
                supabase.table("player_performances")
                .select("id")
                .eq("gameweek_id", gw)
                .execute()
            )
            count = len(result.data) if result.data else 0
            if count > 0:
                print(f"  Gameweek {gw}: {count} records")
                total_individual += count
                gameweeks_with_data.append(gw)
        except Exception as e:
            print(f"  Gameweek {gw}: Error - {e}")

    print(f"  Total from individual queries: {total_individual}")
    print(f"  Gameweeks with data: {gameweeks_with_data}")

    # Method 2: Total count query
    print("\n📊 Method 2: Total count query")
    try:
        total_result = supabase.table("player_performances").select("id").execute()
        total_count = len(total_result.data) if total_result.data else 0
        print(f"  Total records from full query: {total_count}")
    except Exception as e:
        print(f"  Error getting total count: {e}")

    # Method 3: Get unique gameweeks
    print("\n📊 Method 3: Unique gameweeks from full data")
    try:
        unique_result = (
            supabase.table("player_performances").select("gameweek_id").execute()
        )
        if unique_result.data:
            unique_gameweeks = sorted(
                set(record["gameweek_id"] for record in unique_result.data)
            )
            print(f"  Unique gameweeks in full query: {unique_gameweeks}")
            print(f"  Records in full query: {len(unique_result.data)}")
        else:
            print("  No data in full query")
    except Exception as e:
        print(f"  Error getting unique gameweeks: {e}")

    # Method 4: Sample recent records
    print("\n📊 Method 4: Sample recent records")
    try:
        sample_result = (
            supabase.table("player_performances")
            .select("gameweek_id", "player_id", "total_points")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        if sample_result.data:
            print("  Recent records:")
            for record in sample_result.data:
                print(
                    f"    GW {record['gameweek_id']}: Player {record['player_id']}, Points: {record['total_points']}"
                )
        else:
            print("  No sample records found")
    except Exception as e:
        print(f"  Error getting sample records: {e}")


if __name__ == "__main__":
    verify_player_performances()
