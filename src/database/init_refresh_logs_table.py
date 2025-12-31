#!/usr/bin/env python3
"""
Initialize the refresh_logs table in Supabase
This script creates the table if it doesn't exist
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


def init_refresh_logs_table():
    """Create the refresh_logs table if it doesn't exist"""

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_KEY not set")
        return False

    try:
        supabase = create_client(url, key)

        # Try to insert a test record to see if table exists
        # If it doesn't exist, we'll get an error and can handle it
        test_record = {
            "refresh_type": "initialization_test",
            "timestamp": "2025-12-31T00:00:00+00:00",
            "status": "test",
            "github_run_id": "0",
            "notes": "Table initialization test",
        }

        try:
            result = supabase.table("refresh_logs").insert(test_record).execute()
            print("✅ refresh_logs table exists and is accessible")

            # Clean up test record
            try:
                supabase.table("refresh_logs").delete().eq(
                    "github_run_id", "0"
                ).execute()
            except Exception:
                pass

            return True
        except Exception as e:
            if "PGRST205" in str(e) or "Could not find the table" in str(e):
                print("⚠️  refresh_logs table does not exist")
                print("   The table needs to be created manually in Supabase")
                print("   SQL to create the table:")
                print(
                    """
CREATE TABLE refresh_logs (
    id BIGSERIAL PRIMARY KEY,
    refresh_type TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT NOT NULL,
    github_run_id TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE refresh_logs ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserts
CREATE POLICY "Allow inserts" ON refresh_logs
    FOR INSERT
    WITH CHECK (true);
                """
                )
                return False
            else:
                print(f"❌ Error accessing refresh_logs table: {e}")
                return False

    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return False


if __name__ == "__main__":
    success = init_refresh_logs_table()
    sys.exit(0 if success else 1)
