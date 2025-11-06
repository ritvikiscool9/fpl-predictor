import sys
import os
import pandas as pd
import numpy as np
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.fpl.player_recommender import FPLPlayerRecommender


class FPLTeamBuilder:
    """Build optimal 15-player FPL squad within budget constraints"""

    def __init__(self):
        self.recommender = FPLPlayerRecommender()
        self.budget = 1000  # £100.0m in tenths (FPL format)
        self.squad_size = 15

        # Position requirements
        self.min_gk = 2
        self.max_gk = 2
        self.min_def = 5
        self.max_def = 5
        self.min_mid = 5
        self.max_mid = 5
        self.min_att = 3
        self.max_att = 3

        # Max players per team
        self.max_per_team = 3

    def get_all_players_with_predictions(self):
        """Get all players with AI predictions and current data"""
        print("Loading all player data and generating predictions...")

        # Train model if needed
        if not self.recommender.train_model_if_needed():
            print("ERROR: Could not train model")
            return pd.DataFrame()

        # Get all player data
        player_data = self.recommender.get_latest_player_data()
        if player_data.empty:
            print("ERROR: No player data available")
            return pd.DataFrame()

        print(f"SUCCESS: Loaded data for {len(player_data)} players")

        # Filter for players with valid data
        valid_players = player_data[
            (player_data["web_name"].notna())
            & (player_data["element_type"].notna())
            & (player_data["now_cost"] > 0)
            & (player_data["team_id"].notna())
        ].copy()

        print(f"INFO: {len(valid_players)} players have complete data")

        # Generate predictions for all valid players
        player_ids = valid_players["fpl_player_id"].unique()
        predictions = self.recommender.compare_players(player_ids)

        if predictions.empty:
            print("ERROR: Could not generate predictions")
            return pd.DataFrame()

        # Merge predictions with player data
        merged = valid_players.merge(
            predictions, on="fpl_player_id", how="inner", suffixes=("", "_pred")
        )

        # Use the price from predictions (it's already in £m format)
        merged["price_display"] = merged["price"]

        # Add position names
        position_map = {1: "GK", 2: "DEF", 3: "MID", 4: "ATT"}
        merged["position"] = merged["element_type"].map(position_map)

        # Ensure we have all required columns
        required_cols = [
            "web_name",
            "fpl_player_id",
            "element_type",
            "position",
            "now_cost",
            "team_id",
            "predicted_points",
            "predicted_points_per_million",
            "price_display",
        ]

        missing_cols = [col for col in required_cols if col not in merged.columns]
        if missing_cols:
            print(f"WARNING: Missing columns: {missing_cols}")

        print(f"SUCCESS: Generated predictions for {len(merged)} players")
        print(f"Columns available: {sorted(merged.columns.tolist())}")
        return merged

    def calculate_team_constraints(self, players_df):
        """Calculate team distribution to avoid more than 3 players per team"""
        team_counts = defaultdict(int)
        for _, player in players_df.iterrows():
            team_counts[player["team_id"]] += 1
        return team_counts

    def select_optimal_squad(self, players_df):
        """Select optimal 15-player squad using AI predictions and constraints"""
        print("\nBuilding optimal 15-player FPL squad...")

        if players_df.empty:
            return pd.DataFrame()

        # Sort by predicted points per million (value)
        players_df = players_df.sort_values(
            "predicted_points_per_million", ascending=False
        )

        selected_players = []
        remaining_budget = self.budget
        position_counts = {"GK": 0, "DEF": 0, "MID": 0, "ATT": 0}
        team_counts = defaultdict(int)

        # Position requirements
        requirements = {
            "GK": {"min": 2, "max": 2},
            "DEF": {"min": 5, "max": 5},
            "MID": {"min": 5, "max": 5},
            "ATT": {"min": 3, "max": 3},
        }

        print(f"Starting budget: £{remaining_budget/10.0:.1f}m")
        print("Position requirements: 2 GK, 5 DEF, 5 MID, 3 ATT")
        print("Max 3 players per team\n")

        # Enhanced selection algorithm: Prioritize proven FPL assets

        # Define proven premium FPL assets by name (manual override for quality)
        premium_assets = {
            "Haaland",
            "Salah",
            "M.Salah",
            "Palmer",
            "Saka",
            "Son",
            "Kane",
            "Mbappé",
            "De Bruyne",
            "Rashford",
            "Bruno Fernandes",
            "Alexander-Arnold",
            "Van Dijk",
            "Alisson",
            "Ederson",
            "Raya",
            "Pickford",
            "Walker",
            "Dias",
            "Stones",
            "Robertson",
            "Cancelo",
            "Shaw",
            "James",
            "Chilwell",
            "Trippier",
        }

        # Phase 1: Select actual premium assets if available and affordable
        premium_selected = 0
        premium_players = players_df[players_df["web_name"].isin(premium_assets)].copy()
        if len(premium_players) > 0:
            # Sort premium assets by predicted points
            premium_players = premium_players.sort_values(
                "predicted_points", ascending=False
            )

            for _, player in premium_players.iterrows():
                if premium_selected >= 3 or len(selected_players) >= self.squad_size:
                    break

                position = player["position"]
                cost = player["price_display"] * 10
                if (
                    position_counts[position] < requirements[position]["max"]
                    and cost <= remaining_budget
                    and team_counts[player["team_id"]] < self.max_per_team
                ):
                    selected_players.append(player)
                    remaining_budget -= cost
                    position_counts[position] += 1
                    team_counts[player["team_id"]] += 1
                    premium_selected += 1

                    print(
                        f"Selected (Premium): {player['web_name']:<15} ({position}) - £{player['price_display']:.1f}m - "
                        f"Pred: {player['predicted_points']:.2f} pts - "
                        f"Value: {player['predicted_points_per_million']:.3f}"
                    )

        # Phase 2: Fill with quality players from good teams (avoid unknowns)
        good_teams = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}  # Top 10 PL teams typically
        remaining_players = players_df[
            ~players_df["fpl_player_id"].isin(
                [p["fpl_player_id"] for p in selected_players]
            )
        ].copy()

        # Prefer players from good teams with reasonable prices (avoid extreme budget)
        quality_candidates = remaining_players[
            (remaining_players["team_id"].isin(good_teams))
            & (remaining_players["price_display"] >= 4.5)  # Avoid extreme budget picks
            & (remaining_players["price_display"] <= 12.0)  # Avoid overpriced unknowns
            & (
                remaining_players["selected_by_percent"] >= 1.0
            )  # Must have some ownership
        ].copy()

        # If no quality candidates, fall back to all remaining players
        if len(quality_candidates) == 0:
            quality_candidates = remaining_players.copy()

        # Sort by a combination of predicted points and value
        quality_candidates["combined_score"] = (
            quality_candidates["predicted_points"] * 0.6
            + quality_candidates["predicted_points_per_million"] * 4.0
        )
        quality_candidates = quality_candidates.sort_values(
            "combined_score", ascending=False
        )

        for _, player in quality_candidates.iterrows():
            if len(selected_players) >= self.squad_size:
                break

            position = player["position"]
            cost = player["price_display"] * 10
            if (
                position_counts[position] < requirements[position]["max"]
                and cost <= remaining_budget
                and team_counts[player["team_id"]] < self.max_per_team
            ):
                selected_players.append(player)
                remaining_budget -= cost
                position_counts[position] += 1
                team_counts[player["team_id"]] += 1

                print(
                    f"Selected (Quality): {player['web_name']:<15} ({position}) - £{player['price_display']:.1f}m - "
                    f"Pred: {player['predicted_points']:.2f} pts - "
                    f"Value: {player['predicted_points_per_million']:.3f}"
                )

        # Check if we have valid squad
        total_players = sum(position_counts.values())
        print(f"\nSquad Summary:")
        print(f"Total players: {total_players}/15")
        print(f"Remaining budget: £{remaining_budget/10.0:.1f}m")
        print(
            f"Position breakdown: GK:{position_counts['GK']}, DEF:{position_counts['DEF']}, "
            f"MID:{position_counts['MID']}, ATT:{position_counts['ATT']}"
        )

        return pd.DataFrame(selected_players)

    def analyze_squad(self, squad_df):
        """Analyze the selected squad"""
        if squad_df.empty:
            print("No squad to analyze")
            return

        print(f"\n" + "=" * 80)
        print("OPTIMAL FPL SQUAD ANALYSIS")
        print("=" * 80)

        # Squad overview
        total_cost = squad_df["now_cost"].sum()
        total_predicted_points = squad_df["predicted_points"].sum()
        avg_predicted_points = squad_df["predicted_points"].mean()

        print(f"Squad Size: {len(squad_df)}/15 players")
        print(f"Total Cost: £{total_cost/10.0:.1f}m / £100.0m")
        print(f"Remaining Budget: £{(1000-total_cost)/10.0:.1f}m")
        print(f"Total Predicted Points: {total_predicted_points:.1f}")
        print(f"Average Predicted Points: {avg_predicted_points:.2f}")

        # Position breakdown
        print(f"\nPosition Breakdown:")
        for pos in ["GK", "DEF", "MID", "ATT"]:
            pos_players = squad_df[squad_df["position"] == pos]
            if len(pos_players) > 0:
                pos_cost = pos_players["now_cost"].sum() / 10.0
                pos_points = pos_players["predicted_points"].sum()
                print(
                    f"  {pos}: {len(pos_players)} players, £{pos_cost:.1f}m, {pos_points:.1f} predicted points"
                )

        # Team distribution
        print(f"\nTeam Distribution:")
        team_dist = squad_df.groupby("team_id").size().sort_values(ascending=False)
        for team_id, count in team_dist.head(10).items():
            team_players = squad_df[squad_df["team_id"] == team_id]
            if len(team_players) > 0:
                team_name = team_players.iloc[0].get("team_name", f"Team {team_id}")
                print(f"  {team_name}: {count} players")

        # Best value players
        print(f"\nTop 5 Value Picks (Points per Million):")
        top_value = squad_df.nlargest(5, "predicted_points_per_million")
        for _, player in top_value.iterrows():
            print(
                f"  {player['web_name']:<15} ({player['position']}) - "
                f"£{player['price_display']:.1f}m - "
                f"Value: {player['predicted_points_per_million']:.3f}"
            )

        # Detailed squad list
        print(f"\nFULL SQUAD DETAILS:")
        print("-" * 80)

        for pos in ["GK", "DEF", "MID", "ATT"]:
            pos_players = squad_df[squad_df["position"] == pos].sort_values(
                "predicted_points", ascending=False
            )
            if len(pos_players) > 0:
                print(f"\n{pos} ({len(pos_players)} players):")
                for _, player in pos_players.iterrows():
                    print(
                        f"  {player['web_name']:<18} £{player['price_display']:<5.1f}m  "
                        f"Pred: {player['predicted_points']:<5.2f}pts  "
                        f"Value: {player['predicted_points_per_million']:<6.3f}  "
                        f"Ownership: {player['selected_by_percent']:<5.1f}%"
                    )

    def suggest_formation(self, squad_df):
        """Suggest best formation based on predicted points"""
        if len(squad_df) < 15:
            return

        print(f"\nFORMATION RECOMMENDATIONS:")
        print("-" * 40)

        # Get best 11 players (excluding 1 GK)
        gks = squad_df[squad_df["position"] == "GK"].nlargest(1, "predicted_points")
        outfield = squad_df[squad_df["position"] != "GK"].nlargest(
            10, "predicted_points"
        )

        starting_11 = pd.concat([gks, outfield])

        # Count positions in starting 11
        pos_counts = starting_11["position"].value_counts()

        formation = f"{pos_counts.get('DEF', 0)}-{pos_counts.get('MID', 0)}-{pos_counts.get('ATT', 0)}"

        print(f"Recommended Formation: {formation}")
        print(
            f"Starting XI predicted points: {starting_11['predicted_points'].sum():.1f}"
        )

        print(f"\nStarting XI:")
        for pos in ["GK", "DEF", "MID", "ATT"]:
            pos_players = starting_11[starting_11["position"] == pos].sort_values(
                "predicted_points", ascending=False
            )
            if len(pos_players) > 0:
                for _, player in pos_players.iterrows():
                    print(
                        f"  {pos}: {player['web_name']} ({player['predicted_points']:.2f} pts)"
                    )


def main():
    """Main FPL team building function"""
    print("FPL AI TEAM BUILDER")
    print("Building optimal 15-player squad with £100m budget")
    print("=" * 60)

    # Initialize team builder
    builder = FPLTeamBuilder()

    # Get all players with predictions
    all_players = builder.get_all_players_with_predictions()

    if all_players.empty:
        print("ERROR: Could not load player data")
        return

    # Build optimal squad
    optimal_squad = builder.select_optimal_squad(all_players)

    if optimal_squad.empty:
        print("ERROR: Could not build squad")
        return

    # Analyze the squad
    builder.analyze_squad(optimal_squad)

    # Suggest formation
    builder.suggest_formation(optimal_squad)

    print(f"\n" + "=" * 80)
    print("FPL SQUAD GENERATION COMPLETE!")
    print(f"Your AI-optimized squad is ready for the next gameweek!")
    print("=" * 80)


if __name__ == "__main__":
    main()
