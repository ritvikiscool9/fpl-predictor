#!/usr/bin/env python3
"""
Check Weekly Database Refresh Status
=====================================

This script helps you verify if the weekly database refresh ran successfully.
It checks multiple sources to give you a comprehensive status report.
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client, Client
import requests


def check_refresh_status():
    """Check the status of the weekly database refresh."""

    print("🔍 Weekly Database Refresh Status Check")
    print("=" * 50)

    # 1. Check database refresh logs
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in environment variables")
            print("   Please set SUPABASE_URL and SUPABASE_KEY")
            return False

        supabase: Client = create_client(supabase_url, supabase_key)

        # Check recent refresh logs
        print("\n📊 Database Refresh Logs:")
        try:
            # Get refresh logs from the last 7 days
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

            logs = (
                supabase.table("refresh_logs")
                .select("*")
                .gte("timestamp", week_ago)
                .order("timestamp", desc=True)
                .limit(5)
                .execute()
            )

            if logs.data:
                for log in logs.data:
                    timestamp = log.get("timestamp", "Unknown")
                    status = log.get("status", "Unknown")
                    refresh_type = log.get("refresh_type", "Unknown")

                    status_icon = "✅" if status == "completed" else "❌"
                    print(f"   {status_icon} {timestamp} - {refresh_type} - {status}")
            else:
                print("   ℹ️  No recent refresh logs found")

        except Exception as e:
            print(f"   ⚠️  Could not fetch refresh logs: {e}")

        # 2. Check data freshness
        print("\n📅 Data Freshness Check:")
        try:
            # Check latest player performance data
            latest_perf = (
                supabase.table("player_performances")
                .select("created_at")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if latest_perf.data:
                latest_time = latest_perf.data[0]["created_at"]
                print(f"   📈 Latest performance data: {latest_time}")

                # Check if data is recent (within last 3 days)
                latest_dt = datetime.fromisoformat(latest_time.replace("Z", "+00:00"))
                days_old = (
                    datetime.utcnow().replace(tzinfo=latest_dt.tzinfo) - latest_dt
                ).days

                if days_old <= 3:
                    print(f"   ✅ Data is fresh ({days_old} days old)")
                else:
                    print(f"   ⚠️  Data may be stale ({days_old} days old)")
            else:
                print("   ❌ No performance data found")

        except Exception as e:
            print(f"   ⚠️  Could not check data freshness: {e}")

        # 3. Check current gameweek data
        print("\n🎮 Current Gameweek Check:")
        try:
            current_gw = (
                supabase.table("players").select("current_gameweek").limit(1).execute()
            )

            if current_gw.data and current_gw.data[0].get("current_gameweek"):
                gw = current_gw.data[0]["current_gameweek"]
                print(f"   🎯 Current gameweek: {gw}")
            else:
                print("   ℹ️  Gameweek data not available")

        except Exception as e:
            print(f"   ⚠️  Could not check gameweek: {e}")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # 4. Manual verification instructions
    print("\n🔗 Manual Verification:")
    print(
        "   1. GitHub Actions: https://github.com/ritvikiscool9/fpl-predictor/actions"
    )
    print("   2. Look for 'Weekly Database Refresh' workflows")
    print("   3. Check for green checkmarks ✅ indicating success")
    print("   4. Review logs if any runs show red X ❌")

    print("\n💡 Next Steps:")
    print("   • If no recent refresh: Check GitHub Actions for failures")
    print("   • If data is stale: Run manual refresh with:")
    print("     python src/database/fast_performance_refresh.py")
    print("   • If errors persist: Check Supabase credentials and API limits")

    return True


if __name__ == "__main__":
    success = check_refresh_status()
    sys.exit(0 if success else 1)
