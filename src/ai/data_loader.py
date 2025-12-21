import pandas as pd
from typing import List, Tuple
from supabase import create_client
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

    def load_current_player_data(self) -> pd.DataFrame:
        """Load current player performance data"""
        try:
            response = self.supabase.table("current_player_stats").select("*").execute()

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
        """Load current player performance data with real names"""
        try:
            print("Loading current player performance data...")

            # Get player performance stats (using pagination to get all records)
            all_records = []
            batch_size = 1000
            offset = 0

            while True:
                stats_response = (
                    self.supabase.table("player_performances")
                    .select("*")
                    .range(offset, offset + batch_size - 1)
                    .execute()
                )

                if not stats_response.data or len(stats_response.data) == 0:
                    break

                all_records.extend(stats_response.data)
                offset += batch_size

                # Safety limit
                if offset > 10000:
                    break

            if not all_records:
                # Fallback to historical_player_stats if no current data
                stats_response = (
                    self.supabase.table("historical_player_stats").select("*").execute()
                )

                if not stats_response.data:
                    print("WARNING: No performance data found")
                    return pd.DataFrame()
                all_records = stats_response.data

            stats_df = pd.DataFrame(all_records)
            print(f"SUCCESS: Loaded {len(stats_df)} performance records")

            # Map column names to match expected format
            if "player_id" in stats_df.columns:
                stats_df["fpl_player_id"] = stats_df["player_id"]
            if "gameweek_id" in stats_df.columns:
                stats_df["gameweek"] = stats_df["gameweek_id"]
            if "now_cost" in stats_df.columns:
                stats_df["value"] = stats_df["now_cost"]
            if "selected_by_percent" in stats_df.columns:
                stats_df["selected"] = stats_df["selected_by_percent"]

            # Add season column if missing (current season)
            if "season" not in stats_df.columns:
                stats_df["season"] = "2024-25"

            # Get player information (names, positions)
            players_response = (
                self.supabase.table("players")
                .select(
                    "fpl_player_id, web_name, first_name, second_name, element_type, team_id"
                )
                .execute()
            )

            if players_response.data:
                players_df = pd.DataFrame(players_response.data)

                # Merge stats with player info
                merged_df = stats_df.merge(players_df, on="fpl_player_id", how="left")

                # Get current player prices from latest gameweek in player_performances
                try:
                    # Get the latest gameweek
                    latest_gw_response = (
                        self.supabase.table("player_performances")
                        .select("gameweek_id")
                        .order("gameweek_id", desc=True)
                        .limit(1)
                        .execute()
                    )

                    if latest_gw_response.data:
                        latest_gw = latest_gw_response.data[0]["gameweek_id"]
                        print(f"INFO: Getting current prices from gameweek {latest_gw}")

                        # Get current prices from latest gameweek
                        prices_response = (
                            self.supabase.table("player_performances")
                            .select("player_id, now_cost, selected_by_percent")
                            .eq("gameweek_id", latest_gw)
                            .execute()
                        )

                        if prices_response.data:
                            prices_df = pd.DataFrame(prices_response.data)

                            # player_performances.player_id IS the fpl_player_id, so rename for merging
                            prices_df["fpl_player_id"] = prices_df["player_id"]

                            # Merge with price data
                            merged_df = merged_df.merge(
                                prices_df[
                                    ["fpl_player_id", "now_cost", "selected_by_percent"]
                                ],
                                on="fpl_player_id",
                                how="left",
                                suffixes=("", "_current"),
                            )

                            # Update the value and selected columns with current prices
                            if "now_cost_current" in merged_df.columns:
                                merged_df["now_cost"] = merged_df["now_cost_current"]
                                merged_df["value"] = merged_df["now_cost_current"]
                            if "selected_by_percent_current" in merged_df.columns:
                                merged_df["selected"] = merged_df[
                                    "selected_by_percent_current"
                                ]

                            print(
                                f"SUCCESS: Merged current pricing data from GW {latest_gw} for players"
                            )
                        else:
                            print(
                                f"WARNING: No pricing data found for gameweek {latest_gw}"
                            )
                    else:
                        print("WARNING: Could not determine latest gameweek")
                except Exception as e:
                    print(
                        f"WARNING: Could not load current prices from player_performances: {e}"
                    )

                print(f"SUCCESS: Loaded {len(merged_df)} records with player names")

                # Handle season column if it exists
                if "season" in merged_df.columns:
                    print(
                        f"INFO: Players from {merged_df['season'].unique()} season(s)"
                    )
                else:
                    print("INFO: Using current season player performance data")

                # Show sample of real players
                if "web_name" in merged_df.columns:
                    sample_players = merged_df["web_name"].dropna().unique()[:5]
                    print(f"INFO: Sample players: {list(sample_players)}")

                return merged_df
            else:
                print("WARNING: No player info found, using stats only")
                return stats_df

        except Exception as e:
            print(f"ERROR: Error loading player data: {e}")
            return pd.DataFrame()

    def load_fixture_data(self) -> pd.DataFrame:
        """Load fixture data"""
        try:
            response = self.supabase.table("fixtures").select("*").execute()

            if response.data:
                df = pd.DataFrame(response.data)
                print(f"SUCCESS: Loaded {len(df)} fixtures")
                return df
            else:
                print("No fixtures found")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading fixtures: {e}")
            return pd.DataFrame()

    def load_teams_data(self) -> pd.DataFrame:
        """Load teams data"""
        try:
            response = self.supabase.table("teams").select("*").execute()

            if response.data:
                df = pd.DataFrame(response.data)
                print(f"SUCCESS: Loaded {len(df)} teams")
                return df
            else:
                print("No teams found")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error loading teams: {e}")
            return pd.DataFrame()

    def load_current_team_stats(self) -> pd.DataFrame:
        """Load current team statistics"""
        try:
            response = self.supabase.table("current_team_stats").select("*").execute()

            if response.data:
                df = pd.DataFrame(response.data)
                print(f"SUCCESS: Loaded {len(df)} team stats records")
                return df
            else:
                print("No team stats found")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error loading team stats: {e}")
            return pd.DataFrame()

    def test_connection(self):
        """Test supabase connection"""
        try:
            resp = self.supabase.table("players").select("*").limit(1).execute()
            if resp and getattr(resp, "data", None):
                print("connected to supabase")
                return True
            print("No response from supabase test query")
            return False
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def explore_data_structure(self):
        """Explore the data"""
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

    def get_training_data(
        self, seasons: List[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
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
                historical_data = historical_data[
                    historical_data["season"].isin(seasons)
                ]
                print(
                    f" Filtered to {len(historical_data)} records for seasons: {seasons}"
                )

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
                f"SUCCESS: Training data ready: {X.shape[0]} samples, {X.shape[1]} features"
            )
            print(f"Features: {list(X.columns)}")
            print(f"Target stats: min={y.min()}, max={y.max()}, mean={y.mean():.2f}")
