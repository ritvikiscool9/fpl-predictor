#!/usr/bin/env python3
"""
Complete Data Export Script
Exports all player_performances data handling Supabase pagination limits
"""
import sys
import os
import pandas as pd
from datetime import datetime

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
if config_path not in sys.path:
    sys.path.append(config_path)

from supabase_client import get_supabase_client


class CompleteDataExporter:
    def __init__(self):
        self.supabase = get_supabase_client()

    def export_player_performances(self, output_path=None):
        """Export complete player_performances data with pagination"""
        print("Exporting complete player_performances data...")

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"complete_player_performances_{timestamp}.csv"

        all_records = []
        batch_size = 1000
        offset = 0

        print(f"Using pagination (batches of {batch_size})...")

        while True:
            try:
                # Get batch of records
                result = (
                    self.supabase.table("player_performances")
                    .select("*")
                    .range(offset, offset + batch_size - 1)
                    .order("gameweek_id", desc=False)
                    .order("player_id", desc=False)
                    .execute()
                )

                if not result.data or len(result.data) == 0:
                    print(f"   No more data at offset {offset}")
                    break

                batch_count = len(result.data)
                all_records.extend(result.data)

                # Check gameweek range in this batch
                gameweeks = set(record["gameweek_id"] for record in result.data)
                min_gw = min(gameweeks)
                max_gw = max(gameweeks)

                print(
                    f"   Batch {offset//batch_size + 1}: {batch_count} records (GW {min_gw}-{max_gw})"
                )

                # Move to next batch
                offset += batch_size

                # Safety break to avoid infinite loops
                if offset > 20000:
                    print("   SAFETY LIMIT reached (20k records)")
                    break

            except Exception as e:
                print(f"   ERROR at offset {offset}: {e}")
                break

        print(f"\nExport Summary:")
        print(f"   Total records collected: {len(all_records)}")

        if all_records:
            # Analyze the data
            gameweeks = [record["gameweek_id"] for record in all_records]
            unique_gameweeks = sorted(set(gameweeks))

            print(f"   Gameweeks present: {unique_gameweeks}")

            # Count per gameweek
            from collections import Counter

            gw_counts = Counter(gameweeks)
            for gw in sorted(gw_counts.keys()):
                print(f"   GW {gw}: {gw_counts[gw]} records")

            # Convert to DataFrame and save
            df = pd.DataFrame(all_records)
            df.to_csv(output_path, index=False)

            print(f"\nData exported to: {output_path}")
            print(f"File contains {len(df)} rows × {len(df.columns)} columns")
            print(f"Columns: {', '.join(df.columns.tolist())}")

            return output_path, len(all_records), unique_gameweeks
        else:
            print("   No data to export")
            return None, 0, []

    def export_by_gameweek(self, output_dir=None):
        """Export data gameweek by gameweek (alternative method)"""
        print("Exporting by individual gameweeks...")

        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"gameweek_exports_{timestamp}"

        os.makedirs(output_dir, exist_ok=True)

        all_data = []
        gameweek_files = []

        for gw in range(1, 11):
            try:
                print(f"   Exporting Gameweek {gw}...")

                result = (
                    self.supabase.table("player_performances")
                    .select("*")
                    .eq("gameweek_id", gw)
                    .execute()
                )

                if result.data:
                    count = len(result.data)
                    print(f"      {count} records")

                    # Save individual gameweek file
                    gw_df = pd.DataFrame(result.data)
                    gw_file = os.path.join(output_dir, f"gameweek_{gw:02d}.csv")
                    gw_df.to_csv(gw_file, index=False)
                    gameweek_files.append(gw_file)

                    # Add to combined data
                    all_data.extend(result.data)
                else:
                    print(f"      No data for GW {gw}")

            except Exception as e:
                print(f"      ERROR exporting GW {gw}: {e}")

        # Create combined file
        if all_data:
            combined_df = pd.DataFrame(all_data)
            combined_file = os.path.join(output_dir, "all_gameweeks_combined.csv")
            combined_df.to_csv(combined_file, index=False)

            print(f"\nGameweek exports complete")
            print(f"Directory: {output_dir}")
            print(f"Combined file: {combined_file}")
            print(f"Total records: {len(combined_df)}")
            print(f"Individual files: {len(gameweek_files)}")

            return output_dir, combined_file, len(all_data)
        else:
            print("No data exported")
            return None, None, 0

    def verify_export_vs_database(self, export_file):
        """Verify exported data matches database counts"""
        print(f"Verifying export: {export_file}")

        # Read export file
        try:
            df = pd.read_csv(export_file)
            export_total = len(df)
            export_gameweeks = sorted(df["gameweek_id"].unique())

            print(f"Export file: {export_total} records, GWs {export_gameweeks}")
        except Exception as e:
            print(f"❌ Error reading export: {e}")
            return False

        # Check database
        try:
            db_result = (
                self.supabase.table("player_performances")
                .select("*", count="exact")
                .execute()
            )
            db_total = db_result.count

            print(f"Database: {db_total} records")

            # Check individual gameweeks
            db_gameweeks = []
            for gw in range(1, 11):
                gw_result = (
                    self.supabase.table("player_performances")
                    .select("id", count="exact")
                    .eq("gameweek_id", gw)
                    .execute()
                )
                if gw_result.count > 0:
                    db_gameweeks.append(gw)

            print(f"Database gameweeks: {db_gameweeks}")

            # Compare
            if export_total == db_total and export_gameweeks == db_gameweeks:
                print("Export matches database perfectly")
                return True
            else:
                print("Export doesn't match database:")
                print(f"   Records: Export {export_total} vs DB {db_total}")
                print(f"   Gameweeks: Export {export_gameweeks} vs DB {db_gameweeks}")
                return False

        except Exception as e:
            print(f"ERROR checking database: {e}")
            return False


def main():
    """Main export function"""
    print("Complete FPL Data Exporter")
    print("============================================================")

    exporter = CompleteDataExporter()

    # Method 1: Paginated export (recommended)
    print("\nMethod 1: Paginated Export")
    try:
        export_file, record_count, gameweeks = exporter.export_player_performances()
        if export_file:
            print(f"Successfully exported {record_count} records")

            # Verify the export
            print(f"\nVerifying export quality...")
            exporter.verify_export_vs_database(export_file)
        else:
            print("Paginated export failed")
    except Exception as e:
        print(f"Paginated export error: {e}")

    # Method 2: Gameweek-by-gameweek export (backup)
    print(f"\nMethod 2: Gameweek-by-Gameweek Export")
    try:
        output_dir, combined_file, total_records = exporter.export_by_gameweek()
        if combined_file:
            print(f"Successfully exported {total_records} records by gameweek")
        else:
            print("Gameweek export failed")
    except Exception as e:
        print(f"Gameweek export error: {e}")

    print(f"\nExport complete. Check the generated CSV files.")


if __name__ == "__main__":
    main()
