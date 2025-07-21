import sqlite3
import os
import argparse
import pandas as pd

def export_all_tables(db_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    for table_name in tables:
        if table_name == "gpu_info":
            continue

        try:
            df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
            csv_filename = os.path.join(output_dir, f"{table_name}.csv")
            df.to_csv(csv_filename, index=False)
            print(f"✅ Exported {table_name} to {csv_filename}")
        except Exception as e:
            print(f"⚠️ Failed to export {table_name}: {e}")

    conn.close()
    print("🎉 All exports complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export GPU UUID tables to CSVs.")
    parser.add_argument("db_path", type=str, help="Path to SQLite database (e.g., gpu_monitor.db)")
    parser.add_argument("output_dir", type=str, help="Folder to save CSV files (e.g., output/)")

    args = parser.parse_args()
    export_all_tables(args.db_path, args.output_dir)
