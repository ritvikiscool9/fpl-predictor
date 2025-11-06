import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.ai.point_predictor import PlayerPointsPredictor
from src.ai.data_loader import FPLDataLoader
from src.ai.feature_engineering import FPLFeatureEngineering


class FPLPlayerRecommender:
    """Recommend players using trained AI model"""

    def __init__(self, model_path=None):
        self.predictor = PlayerPointsPredictor()
        self.data_loader = FPLDataLoader()
        self.feature_engine = FPLFeatureEngineering()

        if model_path is None:
            # Get the project root directory
            current_dir = os.path.dirname(os.path.abspath(__file__))  # src/fpl/
            project_root = os.path.dirname(
                os.path.dirname(current_dir)
            )  # go up 2 levels
            model_path = os.path.join(project_root, "models", "points_predictor.pkl")

        print(f"INFO: Looking for model at: {model_path}")

        # Load trained model
        try:
            import joblib

            if os.path.exists(model_path):
                model_data = joblib.load(model_path)
                self.predictor.model = model_data["model"]
                self.predictor.feature_columns = model_data["feature_columns"]
                self.predictor.is_trained = model_data["is_trained"]
                print(f"Loaded trained model from {model_path}")
            else:
                print(f"Model file not found: {model_path}")
                print("Run 'python src/ai/point_predictor.py' first to train the model")

        except Exception as e:
            print(f"ERROR: Error loading model: {e}")

    def get_latest_player_data(self) -> pd.DataFrame:
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
            raw_predictions = self.predictor.predict(comparison_data)

            # ENHANCED: Scale predictions to realistic FPL ranges with quality bias
            # Raw predictions are ~0.5-1.0, realistic FPL is 2-15+ points
            # Apply intelligent scaling that favors proven players

            # Define premium player names that should get prediction boosts
            premium_names = {
                "Haaland",
                "Salah",
                "M.Salah",
                "Palmer",
                "Saka",
                "Son",
                "Kane",
                "De Bruyne",
                "Rashford",
                "Bruno Fernandes",
                "Alexander-Arnold",
                "Van Dijk",
                "Alisson",
                "Ederson",
                "Raya",
                "Pickford",
            }

            scaled_predictions = []
            for i, pred in enumerate(raw_predictions):
                player = comparison_data.iloc[i]
                price = player["value"] / 10.0
                player_name = player.get("web_name", "")

                # Check if this is a premium asset
                is_premium = any(name in player_name for name in premium_names)

                # Base scaling by position
                if player.get("element_type", 0) == 1:  # GK
                    scaled_pred = (pred * 4) + 3  # GK range: 3-7 points
                elif player.get("element_type", 0) == 2:  # DEF
                    scaled_pred = (pred * 6) + 3  # DEF range: 3-9 points
                elif player.get("element_type", 0) == 3:  # MID
                    scaled_pred = (pred * 8) + 4  # MID range: 4-12 points
                elif player.get("element_type", 0) == 4:  # ATT
                    scaled_pred = (pred * 10) + 3  # ATT range: 3-13 points
                else:
                    scaled_pred = (pred * 6) + 4  # Default

                # Premium player bonus (names we know are good)
                if is_premium:
                    scaled_pred += 3  # Big boost for premium assets
                elif price >= 10.0:
                    scaled_pred += 2  # Expensive player bonus
                elif price >= 8.0:
                    scaled_pred += 1  # Mid-tier bonus

                # Ownership bonus (popular players are usually good)
                ownership = player.get("selected_by_percent", 0)
                if ownership >= 20:
                    scaled_pred += 2  # High ownership bonus
                elif ownership >= 10:
                    scaled_pred += 1  # Moderate ownership bonus

                # Team quality bonus (top 6 teams)
                team_id = player.get("team_id", 0)
                if team_id in {1, 2, 3, 4, 5, 6}:  # Arsenal, Liverpool, City, etc.
                    scaled_pred += 1

                scaled_predictions.append(max(scaled_pred, 2.0))  # Minimum 2 points

            comparison_data["predicted_points"] = scaled_predictions
            comparison_data["price"] = comparison_data["value"] / 10
            comparison_data["predicted_points_per_million"] = (
                comparison_data["predicted_points"] / comparison_data["price"]
            )

            # Add player info if available
            result_cols = [
                "fpl_player_id",
                "web_name",
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

    def train_model_if_needed(self):
        """Train model if it doesn't exist"""
        if not self.predictor.is_trained:
            print("INFO: No trained model found. Training now...")

            # Load and prepare training data
            historical_data = self.data_loader.load_player_data()
            if historical_data.empty:
                print("ERROR: No training data available")
                return False

            # Feature engineering
            enhanced_data = self.feature_engine.create_player_features(historical_data)
            enhanced_data = self.feature_engine.create_team_features(enhanced_data)
            enhanced_data = self.feature_engine.add_fixture_difficulty(enhanced_data)

            # Train the model
            metrics = self.predictor.train(enhanced_data)

            # Save the model
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            models_dir = os.path.join(project_root, "models")
            os.makedirs(models_dir, exist_ok=True)

            model_path = os.path.join(models_dir, "points_predictor.pkl")
            self.predictor.save_model(model_path)

            print(f"SUCCESS: Model trained and saved. MAE: {metrics['mae']:.2f}")
            return True

        return True


def demo_player_recommender():
    print("FPL AI Player Recommender Demo")

    recommender = FPLPlayerRecommender()

    # Train model if needed
    if not recommender.train_model_if_needed():
        print("ERROR: Failed to train model. Exiting.")
        return

    # Example 1: Compare specific players (use real player IDs from your data)
    print("\nPlayer Comparison Example:")
    print("Note: Using example player IDs - replace with real ones from your database")

    # Get some example player IDs from the data
    latest_data = recommender.get_latest_player_data()
    if not latest_data.empty:
        example_players = latest_data["fpl_player_id"].head(5).tolist()
        comparison = recommender.compare_players(example_players)

        if not comparison.empty:
            print(comparison.round(2))
        else:
            print("No comparison data available")

    # Example 2: Find best value players
    print(f"\n💰 Best Value Players Under £8.0m:")
    value_players = recommender.find_best_value_players(max_price=8.0, top_n=5)

    if not value_players.empty:
        print(value_players.round(2))
    else:
        print("No value players found")


def test_specific_players():

    recommender = FPLPlayerRecommender()

    if not recommender.train_model_if_needed():
        return

    # Test with specific player IDs (adjust based on your data)
    test_players = [1, 2, 10, 20, 50]  # Adjust these IDs

    print(f"\nTesting specific players: {test_players}")
    comparison = recommender.compare_players(test_players)

    if not comparison.empty:
        print(comparison)
    else:
        print("No data for these players")


if __name__ == "__main__":
    demo_player_recommender()
    test_specific_players()
