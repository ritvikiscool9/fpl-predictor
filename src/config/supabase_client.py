import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Create and return Supabase client"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found. Check your .env file.")

    return create_client(supabase_url, supabase_key)


# Create global client instance
supabase = get_supabase_client()
