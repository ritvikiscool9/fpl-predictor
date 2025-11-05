import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.fpl.player_recommender import FPLPlayerRecommender


def test_real_premier_league_players():
    """Test AI with actual Premier League players"""
    print("🏆 FPL AI - Real Premier League Player Predictions")
    print("=" * 60)

    recommender = FPLPlayerRecommender()

    # Train model with real data
    if not recommender.train_model_if_needed():
        print("❌ Could not train model")
        return

    # Get real player data
    latest_data = recommender.get_latest_player_data()

    if latest_data.empty:
        print("❌ No player data available")
        return

    print(f"✅ Loaded data for {len(latest_data)} players")

    # Show available real players
    if "web_name" in latest_data.columns:
        all_players = latest_data["web_name"].dropna().unique()
        print(f"🌟 Total players available: {len(all_players)}")
        print(f"📝 Sample players: {list(all_players[:10])}")

        # Test with top-performing players from your data
        print("\n🎯 Finding Top Performers from Your Data:")

        # Get players with highest average points
        if "total_points" in latest_data.columns:
            top_performers = (
                latest_data.groupby(["fpl_player_id", "web_name"])["total_points"]
                .mean()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )

            print("🏆 Top 10 Average Point Scorers in Your Data:")
            for _, row in top_performers.iterrows():
                print(f"   {row['web_name']}: {row['total_points']:.1f} avg points")

            # Test AI predictions on these top players
            top_player_ids = top_performers["fpl_player_id"].tolist()[:5]
            print(f"\n🤖 AI Predictions for Top 5 Players:")

            comparison = recommender.compare_players(top_player_ids)

            if not comparison.empty:
                # Show predictions with names
                result_cols = [
                    "web_name",
                    "predicted_points",
                    "price",
                    "predicted_points_per_million",
                ]
                available_cols = [
                    col for col in result_cols if col in comparison.columns
                ]

                if available_cols:
                    print(comparison[available_cols].round(2).to_string(index=False))
                else:
                    print(comparison.round(2).to_string(index=False))
            else:
                print("❌ Could not generate predictions")

    # Test with specific player names
    print(f"\n🔍 Testing with Specific Arsenal Players:")
    test_arsenal_players(recommender, latest_data)


def test_arsenal_players(recommender, data):
    """Test with Arsenal players from your data"""
    if "web_name" not in data.columns:
        print("❌ Player names not available")
        return

    # Find Arsenal players in your data
    arsenal_keywords = [
        "Gabriel",
        "Martinelli",
        "Saka",
        "Odegaard",
        "Raya",
        "White",
        "Rice",
    ]

    arsenal_players = data[
        data["web_name"].str.contains("|".join(arsenal_keywords), case=False, na=False)
    ]

    if not arsenal_players.empty:
        print(f"Found {len(arsenal_players)} Arsenal players:")
        for name in arsenal_players["web_name"].unique():
            print(f"   • {name}")

        # Make predictions for Arsenal players
        arsenal_ids = arsenal_players["fpl_player_id"].unique()[:5]
        comparison = recommender.compare_players(arsenal_ids)

        if not comparison.empty:
            print(f"\n🎯 AI Predictions for Arsenal Players:")
            result_cols = [
                "web_name",
                "predicted_points",
                "price",
                "predicted_points_per_million",
            ]
            available_cols = [col for col in result_cols if col in comparison.columns]

            if available_cols:
                print(comparison[available_cols].round(2).to_string(index=False))
    else:
        print("❌ No Arsenal players found in data")


if __name__ == "__main__":
    test_real_premier_league_players()
