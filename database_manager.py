#!/usr/bin/env python3
"""
Database Management Utility
Easy access to all database operations from the main project directory
"""

import os
import sys
import subprocess


def run_database_script(script_name):
    """Run a database script from the main project directory"""
    script_path = os.path.join("src", "database", script_name)

    if not os.path.exists(script_path):
        print(f"ERROR: Script {script_name} not found in src/database/")
        return False

    try:
        # Run the script from the src directory to maintain proper imports
        result = subprocess.run(
            [sys.executable, os.path.join("database", script_name)],
            cwd="src",
            capture_output=False,
        )

        return result.returncode == 0
    except Exception as e:
        print(f"ERROR running {script_name}: {e}")
        return False


def main():
    """Main menu for database operations"""
    print("FPL Database Management Utility")
    print("=" * 40)
    print("1. Refresh player performance data")
    print("2. Update player prices")
    print("3. Check database health")
    print("4. Export complete data")
    print("5. Analyze performance gaps")
    print("6. Complete database refresh")
    print("7. Verify database fixes")
    print("8. Exit")

    while True:
        try:
            choice = input("\nSelect option (1-8): ").strip()

            if choice == "1":
                print("Refreshing player performance data...")
                run_database_script("fast_performance_refresh.py")
            elif choice == "2":
                print("Updating player prices...")
                run_database_script("update_player_prices.py")
            elif choice == "3":
                print("Checking database health...")
                run_database_script("check_database.py")
            elif choice == "4":
                print("Exporting complete data...")
                run_database_script("export_complete_data.py")
            elif choice == "5":
                print("Analyzing performance gaps...")
                run_database_script("analyze_performance_gaps.py")
            elif choice == "6":
                print("Running complete database refresh...")
                run_database_script("database_refresh.py")
            elif choice == "7":
                print("Verifying database fixes...")
                run_database_script("verify_fix.py")
            elif choice == "8":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please select 1-8.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
