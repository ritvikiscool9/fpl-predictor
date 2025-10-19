import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv
import os

"""
Load and prepare FPL data for AI training
"""


class FPLDataLoader:

    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path

        load_dotenv()

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found. Check your .env file.")

        self.supabase = create_client(supabase_url, supabase_key)

    def load_player_data(self) -> pd.DataFrame:
        """Load historical player performance data"""
        try:
            response = self.supabase.table("historical_player_stats")

            if response.data:
                df = pd.DataFrame(response.data)
                print("loaded data")
                return df
            else:
                print("no data found")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error loading player data: {e}")
            return pd.DataFrame()

    def load_current_player_data(self) -> pd.DataFrame:
        """Load current player performance data"""
        try:
            response = self.supabase.table("current_player_stats")

            if response.data:
                df = pd.DataFrame(response.data)
                print("loaded data")
                return df
            else:
                print("no data found")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading player data: {e}")
            return pd.DataFrame()

    # def load_player_performance(self) -> pd.DataFrame:
    #     """Load player gameweek performances"""

    def load_fixture_data(self) -> pd.DataFrame:
        """Load fixture data"""
        try:
            response = self.supabase.table("fixtures").select("*").execute

            if response.data:
                df = pd.DataFrame(response.data)
                print(f"loaded {len(df)} fixtures")
                return df
            else:
                print("no fixtures loaded")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading player data: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    print("Testing FPL Data Loader...")
    loader = FPLDataLoader()

    if loader.test_connection():
        print("\n" + "=" * 50)
        loader.explore_data_structure()

        print("\n" + "=" * 50)
        print("Testing training data preparation...")
        X, y = loader.get_training_data()
        if not X.empty and not y.empty:
            print(
                f"✅ Training data ready: {X.shape[0]} samples, {X.shape[1]} features"
            )
            print(f"Features: {list(X.columns)}")
            print(f"Target stats: min={y.min()}, max={y.max()}, mean={y.mean():.2f}")
