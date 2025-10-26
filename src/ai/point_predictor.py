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
            n_estimators=100, max_depth=6, random_state=42, n_jobs=-1
        )
        self.feature_columns = []
        self.is_trained = False

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for prediciting"""

        # Base features
        base_features = [
            "value",
            "goals_scored_avg_last_5",
            "assists_avg_last_5",
            "clean_sheets_avg_last_5",
            "minutes_avg_last_5",
            "saves_avg_last_5",
        ]

        # Engineered features
        engineered_features = [
            "points_last_3",
            "points_last_5",
            "minutes_last_3",
            "form_trend",
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

    def train(self, enhanced_data: pd.DataFrame) -> dict:
        """Train the model and return the metrics"""
        X = self.prepare_features(enhanced_data)
        y = enhanced_data["total_points"]

        print(f"Features shape: {X.shape}")
        print(f"Target shape: {y.shape}")
        print(f"Target range: {y.min():.1f} to {y.max():.1f} points")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"Training on {len(X_train)} samples")
        print(f"Testing on {len(X_test)} samples")

        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Evalute
        y_pred = self.model.predict(X_test)

        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred),
            "feature_importance": dict(
                zip(self.feature_columns, self.model.feature_importances_)
            ),
        }

        print("\nModel Performance:")
        print(f"MAE: {metrics['mae']:.2f} points")
        print(f"R²: {metrics['r2']:.3f}")

        # Show top 5 most important features
        importance = sorted(
            metrics["feature_importance"].items(), key=lambda x: x[1], reverse=True
        )[:8]
        print(f"\nTop Features by Importance:")
        for i, (feature, score) in enumerate(importance, 1):
            print(f"  {i}. {feature}: {score:.3f}")

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict points"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        X_prepared = self.prepare_features(X)
        return self.model.predict(X_prepared)

    def save_model(self, filepath: str):
        """Save trained model"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "feature_columns": self.feature_columns,
                "is_trained": self.is_trained,
            },
            filepath,
        )
        print(f"Model saved to {filepath}")


if __name__ == "__main__":
    print("Training FPL Points Predictor")

    # Initialize components
    loader = FPLDataLoader()
    feature_engine = FPLFeatureEngineering()
    predictor = PlayerPointsPredictor()

    # Load and enhance data (reuse your working pipeline)
    print("\nLoading and preparing data...")
    historical_data = loader.load_player_data()

    if not historical_data.empty:
        # Apply the same feature engineering that worked
        enhanced_data = feature_engine.create_player_features(historical_data)
        enhanced_data = feature_engine.create_team_features(enhanced_data)
        enhanced_data = feature_engine.add_fixture_difficulty(enhanced_data)

        print(f"Final training data: {enhanced_data.shape}")

        # Train the model
        print("\nTraining AI model...")
        metrics = predictor.train(enhanced_data)

        # Save model
        os.makedirs("models", exist_ok=True)
        predictor.save_model("models/points_predictor.pkl")

        # Test predictions on sample
        print(f"\nTesting predictions...")
        sample_data = enhanced_data.head(5)
        predictions = predictor.predict(sample_data)
        actual = sample_data["total_points"].values

        print(f"Sample Predictions:")
        for i, (pred, act) in enumerate(zip(predictions, actual)):
            print(f"  Player {i+1}: Predicted {pred:.1f}, Actual {act:.1f}")

        print(f"\nTraining Complete!")
        print(f"Final MAE: {metrics['mae']:.2f} points")
        print(f"Final R²: {metrics['r2']:.3f}")

    else:
        print("No training data available")
