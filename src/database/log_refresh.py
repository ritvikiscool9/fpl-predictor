#!/usr/bin/env python3
"""Log workflow completion to refresh_logs table"""

import os
from datetime import datetime, timezone
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
github_run_id = os.environ.get("GITHUB_RUN_ID")

if url and key:
    try:
        supabase = create_client(url, key)
        refresh_log = {
            "refresh_type": "weekly_automated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "github_run_id": github_run_id,
            "notes": "Automated weekly refresh via GitHub Actions",
        }
        result = supabase.table("refresh_logs").insert(refresh_log).execute()
        print("✅ Refresh logged to database successfully")
    except Exception as e:
        print(f"⚠️ Could not log to database: {e}")
else:
    print("⚠️ Database credentials not available for logging")
