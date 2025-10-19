"""
Transform raw FPL data into machine learning features
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from .data_loader import FPLDataLoader


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
        features["is_defender"] = (df.get("element_type", 0) == 2).astype(int)
        features["is_midfielder"] = (df.get("element_type", 0) == 3).astype(int)
        features["is_attacker"] = (df.get("element_type", 0) == 4).astype(int)

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
        # For now placeholder
        df["fixture_difficulty"] = 3
        return df

    def create_team_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add team-level features"""
        try:
            teams_data = self.data_loader.load_teams_data()
            # Implementation depends on team stats structure
            return df
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

        # Add features
        enhanced_data = engine.create_player_features(historical_data)

        print(f"Enhanced data shape: {enhanced_data.shape}")
        print(
            f"New columns: {set(enhanced_data.columns) - set(historical_data.columns)}"
        )
    else:
        print("No data available for testing")
