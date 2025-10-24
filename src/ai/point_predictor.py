from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pandas as pd
import numpy as np
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.ai.data_loader import FPLDataLoader
from src.ai.feature_engineering import FPLFeatureEngineering


class PlayerPointsPredictor:
    """Predict points for individual players"""

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        )
        self.feature_columns = []
        self.is_trained = False

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for prediciting"""

        # Base features
        base_features = [
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
            "value",
        ]

        # Engineered features
        engineered_features = [
            "points_last_3",
            "points_last_5",
            "minutes_last_3",
            "form_trend",
            "points_per_million",
            "is_defender",
            "is_midfielder",
            "is_attacker",
            "fixture_difficulty",
        ]

        # Select avaible features
        all_features = base_features + engineered_features
        available_features = [col for col in all_features if col in df.columns]

        features = df[available_features].fillna(0)
        self.feature_columns = available_features

        print(f"Using {len(available_features)} for training")
        return features


if __name__ == "__main__":

    # Initialize components
    loader = FPLDataLoader()
    feature_engine = FPLFeatureEngineering()
    predictor = PlayerPointsPredictor()
