"""
Transform raw FPL data into machine learning features
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.ai.data_loader import FPLDataLoader


class FPLFeatureEngineering:
    """Create features for predicting player performances"""

    def __init__(self):
        self.data_loader = FPLDataLoader()

    def create_player_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for individual players"""
        features = df.copy()

        if "fpl_player_id" in df.columns:
            features["points_last_3"] = (
                df.groupby("fpl_player_id")["total_points"]
                .rolling(3, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )

            features["points_last_5"] = (
                df.groupby("fpl_player_id")["total_points"]
                .rolling(5, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )

            # Minutes consistency
            features["minutes_last_3"] = (
                df.groupby("fpl_player_id")["minutes"]
                .rolling(3, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )

        # Form trend
        features["form_trend"] = self.calculate_form_trend(df)

        # Value features
        if "total_points" in df.columns and "value" in df.columns:
            features["points_per_million"] = df["total_points"] / (df["value"] / 10)

        # Defensive vs attacking players
        if "element_type" in df.columns:
            features["is_defender"] = (df["element_type"] == 2).astype(int)
            features["is_midfielder"] = (df["element_type"] == 3).astype(int)
            features["is_attacker"] = (df["element_type"] == 4).astype(int)
        else:
            # Default values if element_type column doesn't exist
            features["is_defender"] = 0
            features["is_midfielder"] = 0
            features["is_attacker"] = 0

        return features

    def calculate_form_trend(self, df: pd.DataFrame) -> pd.Series:
        """Calcualte if player is improving or not"""
        if "fpl_player_id" not in df.columns or "total_points" not in df.columns:
            return pd.Series(0, index=df.index)

        return (
            df.groupby("fpl_player_id")["total_points"]
            .rolling(3, min_periods=2)
            .apply(lambda x: 1 if len(x) >= 2 and x.iloc[-1] > x.iloc[0] else 0)
            .reset_index(level=0, drop=True)
            .fillna(0)
        )

    def add_fixture_difficulty(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add fixture difficulty features"""
        try:
            fixtures = self.data_loader.load_fixture_data()
            teams_data = self.data_loader.load_teams_data()

            if fixtures.empty or teams_data.empty:
                print("Missing fixture or team data, using default difficulty")
                df["fixture_difficulty"] = 3  # Default medium difficulty
                return df

            features = df.copy()

            # If we have gameweek and team info, calculate real difficulty
            if "gameweek_id" in df.columns and "team_id" in df.columns:
                # Get upcoming fixtures for each team/gameweek combination
                upcoming_fixtures = fixtures[fixtures["finished"] == False]

                # Merge to get opponent strength
                fixture_difficulty = []

                for _, row in df.iterrows():
                    team_id = row.get("team_id")
                    gameweek_id = row.get("gameweek_id")

                    # Find fixture for this team in this gameweek
                    team_fixtures = upcoming_fixtures[
                        (upcoming_fixtures["gameweek_id"] == gameweek_id)
                        & (
                            (upcoming_fixtures["team_home_id"] == team_id)
                            | (upcoming_fixtures["team_away_id"] == team_id)
                        )
                    ]

                    if not team_fixtures.empty:
                        fixture = team_fixtures.iloc[0]
                        # Use the difficulty rating from your data
                        if fixture["team_home_id"] == team_id:
                            difficulty = fixture.get("difficulty_home", 3)
                        else:
                            difficulty = fixture.get("difficulty_away", 3)
                    else:
                        difficulty = 3  # Default

                    fixture_difficulty.append(difficulty)

                features["fixture_difficulty"] = fixture_difficulty

            else:
                features["fixture_difficulty"] = 3

            return features

        except Exception as e:
            print(f"Error adding fixture difficulty: {e}")
            df["fixture_difficulty"] = 3
            return df

    def create_team_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add team-level features"""
        try:
            # Load team data
            teams_data = self.data_loader.load_teams_data()
            current_team_stats = self.data_loader.load_current_team_stats()

            if teams_data.empty:
                print("No teams data available")
                return df

            features = df.copy()

            # Merge with team basic info (if player has team_id)
            if "team_id" in df.columns and not teams_data.empty:
                # Get team name and code
                team_info = teams_data[["id", "name", "short_name", "code"]].rename(
                    columns={"id": "team_id"}
                )
                features = features.merge(
                    team_info, on="team_id", how="left", suffixes=("", "_team")
                )

            # Merge with current team stats (strength, form, etc.)
            if "team_id" in df.columns and not current_team_stats.empty:
                # Get latest team stats for each team
                latest_team_stats = (
                    current_team_stats.sort_values("gameweek_id")
                    .groupby("team_id")
                    .last()
                    .reset_index()
                )

                # Select relevant team features
                team_features = latest_team_stats[
                    [
                        "team_id",
                        "strength",
                        "strength_overall_home",
                        "strength_overall_away",
                        "strength_attack_home",
                        "strength_attack_away",
                        "strength_defence_home",
                        "strength_defence_away",
                        "form",
                        "points",
                        "position",
                    ]
                ]

                features = features.merge(
                    team_features, on="team_id", how="left", suffixes=("", "_team")
                )

                # Create derived team features
                features["team_attack_strength"] = (
                    features.get("strength_attack_home", 0)
                    + features.get("strength_attack_away", 0)
                ) / 2

                features["team_defence_strength"] = (
                    features.get("strength_defence_home", 0)
                    + features.get("strength_defence_away", 0)
                ) / 2

                # Team form as numeric (convert if it's string)
                if "form" in features.columns:
                    features["team_form_numeric"] = pd.to_numeric(
                        features["form"], errors="coerce"
                    ).fillna(0)

            return features

        except Exception as e:
            print(f"Could not add team features: {e}")
            return df


if __name__ == "__main__":
    print("Testing Feature Engineering...")

    loader = FPLDataLoader()
    engine = FPLFeatureEngineering()

    # Get some data to test with
    historical_data = loader.load_player_data()

    if not historical_data.empty:
        print(f"Original data shape: {historical_data.shape}")
        print(f"Original columns: {list(historical_data.columns)}")

        # Add player features
        enhanced_data = engine.create_player_features(historical_data)
        print(f"After player features: {enhanced_data.shape}")

        # Add team features
        enhanced_data = engine.create_team_features(enhanced_data)
        print(f"After team features: {enhanced_data.shape}")

        # Add fixture difficulty
        enhanced_data = engine.add_fixture_difficulty(enhanced_data)
        print(f"Final shape: {enhanced_data.shape}")

        print(
            f"All new columns: {set(enhanced_data.columns) - set(historical_data.columns)}"
        )

        # Show sample of new features
        new_cols = list(set(enhanced_data.columns) - set(historical_data.columns))
        if new_cols:
            print(f"Sample new features:\n{enhanced_data[new_cols].head()}")
    else:
        print("No data available for testing")
