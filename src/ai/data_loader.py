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

    def load_player_data(self) -> pd.DataFrame:
        """Load historical player performance data"""
        try:
            response = (
                self.supabase.table("historical_player_stats").select("*").execute()
            )

            if response.data:
                df = pd.DataFrame(response.data)
                print(f"Loaded {len(df)} historical records")
                return df
            else:
                print("No historical data found")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error loading player data: {e}")
            return pd.DataFrame()

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

    def test_connection(self):
        """Test supabase connection"""
        try:
            response = self.supabase.table("players").select("*").execute
            print("connected to supabase")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def explore_data_structure(self):
        """Explore the data """
        print(" Exploring data ...")

        tables = [
            "players",
            "teams",
            "current_player_stats",
            "historical_player_stats",
            "fixtures",
            "historical_fixtures",
            "gameweeks",
            "current_season",
            "current_team_stats",
            "player_performances",
            "player_form_last_5",
            "current_player_prices",
        ]

        for table_name in tables:
            try:
                response = (
                    self.supabase.table(table_name).select("*").limit(2).execute()
                )
                if response.data:
                    df = pd.DataFrame(response.data)
                    print(f"\n {table_name.upper()}:")
                    print(f"   Rows: {len(response.data)}")
                    print(f"   Columns: {list(df.columns)}")
                else:
                    print(f"\n {table_name}: No data")
            except Exception as e:
                print(f"\n{table_name}: Error - {e}")

    def load_teams_data(self) -> pd.DataFrame:
        """Load teams data"""
        try:
            response = self.supabase.table("teams").select("*").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                print(f"Loaded {len(df)} teams")
                return df
            else:
                print("No teams found")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading teams: {e}")
            return pd.DataFrame()

    def get_training_data(self, seasons: List[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get features (X) and target (y) for training by combining tables"""
        try:
            print(" Preparing training data from existing tables")

            # Load historical player stats as base data
            historical_data = self.load_player_data()  # historical_player_stats

            if historical_data.empty:
                print(" No historical player data available for training")
                return pd.DataFrame(), pd.Series()

            print(f" Loaded {len(historical_data)} historical records")
            print(f"Available columns: {list(historical_data.columns)}")

            # Filter by seasons if specified
            if seasons and "season" in historical_data.columns:
                historical_data = historical_data[historical_data["season"].isin(seasons)]
                print(f" Filtered to {len(historical_data)} records for seasons: {seasons}")

            # Try to merge with team data if available
            try:
                teams_data = self.load_teams_data()
                if not teams_data.empty and "team" in historical_data.columns:
                    # Merge team strength data
                    historical_data = historical_data.merge(
                        teams_data,
                        left_on="team",
                        right_on="id",
                        how="left",
                        suffixes=("", "_team"),
                    )
                    print(" Merged with team data")
            except Exception as e:
                print(f" Could not merge team data: {e}")

            # Define potential feature columns
            potential_features = [
                # Player stats
                "minutes",
                "goals_scored",
                "assists",
                "clean_sheets",
                "goals_conceded",
                "own_goals",
                "penalties_saved",
                "penalties_missed",
                "yellow_cards",
                "red_cards",
                "saves",
                "bonus",
                "bps",
                "influence",
                "creativity",
                "threat",
                "ict_index",
                "now_cost",
                "selected_by_percent",
                "form",
                "points_per_game",
                "value_form",
                "value_season",
                # Team stats (if merged)
                "strength_overall_home",
                "strength_overall_away",
                "strength_attack_home",
                "strength_attack_away",
                "strength_defence_home",
                "strength_defence_away",
            ]

            # Filter to columns that actually exist
            available_features = [
                col for col in potential_features if col in historical_data.columns
            ]
            print(f" Available features for training: {available_features}")

            if not available_features:
                print(" No suitable feature columns found")
                return pd.DataFrame(), pd.Series()

            # Create feature matrix
            X = historical_data[available_features].copy()

            # Handle missing values
            X = X.fillna(0)

            # Find target variable
            target_columns = [
                "total_points",
                "points",
                "gameweek_points",
                "round_points",
            ]
            y = None

            for target_col in target_columns:
                if target_col in historical_data.columns:
                    y = historical_data[target_col].fillna(0)
                    print(f" Using '{target_col}' as target variable")
                    break

            if y is None:
                print(" No suitable target column found")
                available_cols = list(historical_data.columns)
                print(f"Available columns: {available_cols}")
                return X, pd.Series()

            # Remove rows where target is null or features are all null
            valid_indices = ~(y.isna() | (X.isna().all(axis=1)))
            X = X[valid_indices]
            y = y[valid_indices]

            print(f" Training data prepared:")
            print(f"   Samples: {len(X)}")
            print(f"   Features: {len(X.columns)}")
            print(f"   Target range: {y.min():.1f} - {y.max():.1f}")
            print(f"   Target mean: {y.mean():.2f}")

            return X, y

        except Exception as e:
            print(f" Error preparing training data: {e}")
            return pd.DataFrame(), pd.Series()


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
