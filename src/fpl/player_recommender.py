import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirnmae(__file__))))
from src.ai.point_predictor import PlayerPointsPredictor
from src.ai.data_loader import FPLDataLoader
from src.ai.feature_engineering import FPLFeatureEngineering


class FPLPlayerRecommender:
    """Recommend players using trained AI model"""

    def __init__(self, model_path="models/points_predictor.pkl"):
        self.predictor = PlayerPointsPredictor()
        self.data_loader = FPLDataLoader()
        self.feature_engine = FPLFeatureEngineering()

        # Load trained model
        try:
            import joblib

            model_data = joblib.load(model_path)
            self.predictor.model = model_data["model"]
            self.predictor.feature_columns = model_data["feature_columns"]
            self.predictor.is_trained = model_data["is_trained"]
            print(f"Loaded trained model from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")

    def get_latest_player_data(self) -> pd.DateFrame:
        """Get most recent player data"""

        historical_data = self.data_loader.load_player_data()

        if historical_data.empty:
            return pd.DataFrame()

        latest_data = (
            historical_data.sort_values("gameweek")
            .groupby("fpl_player_id")
            .last()
            .reset_index()
        )

        # Apply feature engineering
        latest_data = self.feature_engine.create_player_features(latest_data)
        latest_data = self.feature_engine.create_team_features(latest_data)
        latest_data = self.feature_engine.add_fixture_difficulty(latest_data)

        return latest_data

    def compare_players(self, player_ids: list) -> pd.DataFrame:
        latest_data = self.get_latest_player_data()

        if latest_data.empty:
            print("No player data available")
            return pd.DataFrame()

        # Filter for requested players
        comparison_data = latest_data[
            latest_data["fpl_player_id"].isin(player_ids)
        ].copy()

        if comparison_data.empty:
            print(f"No data found for players: {player_ids}")
            return pd.DataFrame()

        # Make predictions
        try:
            predictions = self.predictor.predict(comparison_data)
            comparison_data["predicted_points"] = predictions

            # Calculate useful metrics
            comparison_data["price"] = comparison_data["value"] / 10
            comparison_data["predicted_points_per_million"] = (
                comparison_data["predicted_points"] / comparison_data["price"]
            )

            # Select columns for comparison
            result_cols = [
                "fpl_player_id",
                "predicted_points",
                "price",
                "predicted_points_per_million",
                "points_last_5",
                "minutes_avg_last_5",
                "fixture_difficulty",
            ]

            available_cols = [
                col for col in result_cols if col in comparison_data.columns
            ]
            result = comparison_data[available_cols].copy()

            # Sort by predicted points
            result = result.sort_values("predicted_points", ascending=False)

            return result

        except Exception as e:
            print(f"Error making predictions: {e}")
            return pd.DataFrame()

    def find_best_value_players(
        self, max_price: float = 10.0, top_n: int = 10
    ) -> pd.DataFrame:
        """Find best value players under price limit"""
        latest_data = self.get_latest_player_data()

        if latest_data.empty:
            return pd.DataFrame()

        # Filter by price
        affordable_players = latest_data[
            (latest_data["value"] / 10) <= max_price
        ].copy()

        if affordable_players.empty:
            print(f"No players found under £{max_price}m")
            return pd.DataFrame()

        # Make predictions
        try:
            predictions = self.predictor.predict(affordable_players)
            affordable_players["predicted_points"] = predictions
            affordable_players["price"] = affordable_players["value"] / 10
            affordable_players["predicted_points_per_million"] = (
                affordable_players["predicted_points"] / affordable_players["price"]
            )

            # Select and sort by value
            result = affordable_players[
                [
                    "fpl_player_id",
                    "predicted_points",
                    "price",
                    "predicted_points_per_million",
                    "points_last_5",
                ]
            ].sort_values("predicted_points_per_million", ascending=False)

            return result.head(top_n)

        except Exception as e:
            print(f"Error finding value players: {e}")
            return pd.DataFrame()


# def demo_player_recommender():
#     return


# if __name__ == "__main__":
#     demo_player_recommender()
