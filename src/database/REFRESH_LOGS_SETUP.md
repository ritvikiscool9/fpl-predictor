# Database Refresh Setup Guide

## Supabase Table: `refresh_logs`

The weekly database refresh workflow logs its status to a `refresh_logs` table in Supabase. This table needs to be created manually.

### Create the Table

1. Go to your Supabase project dashboard
2. Navigate to the SQL Editor
3. Create a new query and paste this SQL:

```sql
-- Create refresh_logs table
CREATE TABLE IF NOT EXISTS refresh_logs (
    id BIGSERIAL PRIMARY KEY,
    refresh_type TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT NOT NULL,
    github_run_id TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE refresh_logs ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserts (adjust as needed for your security requirements)
CREATE POLICY "Allow inserts for refresh logs" ON refresh_logs
    FOR INSERT
    WITH CHECK (true);

-- Create policy to allow selects
CREATE POLICY "Allow selects for refresh logs" ON refresh_logs
    FOR SELECT
    USING (true);
```

4. Click "Run" to execute the query

### Verify the Table

Run the initialization script to verify the table exists:

```bash
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
python src/database/init_refresh_logs_table.py
```

### Workflow Behavior

- **If the table exists**: The workflow will log refresh attempts and their status
- **If the table doesn't exist**: The workflow will continue and complete successfully, but won't log to the database

The logging step is non-blocking and won't cause the workflow to fail if the table is missing.

## Troubleshooting

### "Could not find the table 'public.refresh_logs'"

This means the table hasn't been created yet. Follow the steps above to create it.

### DeprecationWarning about datetime.utcnow()

This is a Python 3.13+ deprecation warning. The code has been updated to use `datetime.now(timezone.utc)` which is the recommended approach.
