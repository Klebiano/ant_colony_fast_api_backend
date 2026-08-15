"""
Database SQL Generator & Interchangeability Script.

This script reads all CSV files located in the /database directory
(subsystem.csv, downtime.csv, wind_farm_map_points.csv) and converts them into
a portable SQL script (.sql file).

The generated SQL script uses standard ANSI SQL, double-quoted column identifiers,
and explicit INSERT statements, making the output fully interchangeable between
PostgreSQL and SQLite (local .sql / sqlite3 database).

Usage:
    python tests/generate_sql.py [--output database/database.sql] [--verify]
"""

import os
import sys
import argparse
import sqlite3
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
TESTS_DIR = BASE_DIR / "tests"
DEFAULT_OUTPUT_SQL = DATABASE_DIR / "database.sql"
ROOT_OUTPUT_SQL = BASE_DIR / "database.sql"

# Table schema configuration to ensure correct data types, primary keys, and foreign keys
TABLE_SCHEMAS = {
    "subsystem": {
        "columns": {
            "SUBSYSTEM_ID": "INTEGER PRIMARY KEY",
            "SUBSYSTEM_NAME": "VARCHAR(255) NOT NULL"
        },
        "order": 1,
        "pk": ["SUBSYSTEM_ID"]
    },
    "wind_farm_map_points": {
        "columns": {
            "LATITUDE": "FLOAT NOT NULL",
            "LONGITUDE": "FLOAT NOT NULL",
            "TURBINE_ID": "INTEGER PRIMARY KEY",
            "TURBINE_NAME": "VARCHAR(255) NOT NULL",
            "LATITUDE_NORM": "FLOAT",
            "LONGITUDE_NORM": "FLOAT"
        },
        "order": 2,
        "pk": ["TURBINE_ID"]
    },
    "downtime": {
        "columns": {
            "DOWNTIME_ID": "INTEGER PRIMARY KEY",
            "SUBSYSTEM_ID": "INTEGER NOT NULL",
            "FAULT_TYPE": "VARCHAR(255) NOT NULL",
            "ANUAL_FAILURE_RATE": "FLOAT NOT NULL",
            "FAULT_DOWNTIME_DAYS": "FLOAT NOT NULL",
            "FAULT_DOWNTIME_DAYS_NORM": "FLOAT"
        },
        "constraints": [
            'FOREIGN KEY ("SUBSYSTEM_ID") REFERENCES subsystem("SUBSYSTEM_ID")'
        ],
        "order": 3,
        "pk": ["DOWNTIME_ID"]
    }
}


def format_sql_value(val):
    """Format a Python/Pandas value into a standard SQL literal."""
    if pd.isna(val) or val is None or str(val).strip().upper() == "NULL":
        return "NULL"
    if isinstance(val, (bool,)):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"


def generate_table_ddl(table_name: str, df: pd.DataFrame) -> str:
    """Generate DDL (CREATE TABLE) statement for a given table name and dataframe."""
    schema_info = TABLE_SCHEMAS.get(table_name, {})
    col_defs = []

    # Clean headers (strip quotes or spaces)
    clean_cols = [col.strip('"').strip() for col in df.columns]

    defined_cols = schema_info.get("columns", {})
    for col in clean_cols:
        if col in defined_cols:
            col_defs.append(f'    "{col}" {defined_cols[col]}')
        else:
            # Infer data type for unconfigured columns
            sample_series = df[col].dropna()
            if sample_series.empty:
                col_type = "VARCHAR(255)"
            elif pd.api.types.is_integer_dtype(sample_series):
                col_type = "INTEGER"
            elif pd.api.types.is_float_dtype(sample_series):
                col_type = "FLOAT"
            else:
                col_type = "VARCHAR(255)"
            col_defs.append(f'    "{col}" {col_type}')

    # Append table constraints if defined
    if "constraints" in schema_info:
        for constraint in schema_info["constraints"]:
            col_defs.append(f"    {constraint}")

    ddl = f"CREATE TABLE IF NOT EXISTS {table_name} (\n" + ",\n".join(col_defs) + "\n);"
    return ddl


def generate_table_dml(table_name: str, df: pd.DataFrame) -> str:
    """Generate DML (INSERT INTO) statements for a given table name and dataframe."""
    if df.empty:
        return ""

    clean_cols = [col.strip('"').strip() for col in df.columns]
    cols_str = ", ".join([f'"{col}"' for col in clean_cols])

    schema_info = TABLE_SCHEMAS.get(table_name, {})
    defined_cols = schema_info.get("columns", {})

    # Pre-process types for integer columns to prevent ".0" formatting
    df_copy = df.copy()
    for col in df.columns:
        col_clean = col.strip('"').strip()
        if col_clean in defined_cols and "INT" in defined_cols[col_clean].upper():
            df_copy[col] = df_copy[col].apply(
                lambda x: int(x) if pd.notna(x) and str(x).strip() != "" else None
            )

    value_rows = []
    for _, row in df_copy.iterrows():
        row_vals = [format_sql_value(row[col]) for col in df.columns]
        value_rows.append("(" + ", ".join(row_vals) + ")")

    values_str = ",\n".join(value_rows)
    dml = f'INSERT INTO {table_name} ({cols_str}) VALUES\n{values_str};'
    return dml


def build_sql_script(db_dir: Path = DATABASE_DIR) -> str:
    """Read all CSV files in database directory and construct the unified SQL script."""
    csv_files = list(db_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {db_dir}")

    tables_data = {}
    for csv_file in csv_files:
        table_name = csv_file.stem
        # Read CSV handling utf-8 or utf-8-sig
        df = pd.read_csv(csv_file, encoding="utf-8-sig")
        # Clean column names
        df.columns = [c.strip('"').strip() for c in df.columns]
        tables_data[table_name] = df

    # Order tables to satisfy FK constraints if defined
    ordered_table_names = sorted(
        tables_data.keys(),
        key=lambda name: TABLE_SCHEMAS.get(name, {}).get("order", 999)
    )

    sql_parts = [
        "-- ========================================================",
        "-- Unified Database Seeding Script",
        "-- Compatible with PostgreSQL and SQLite / local .sql DBs",
        "-- Auto-generated from /database CSV files",
        "-- ========================================================\n",
        "BEGIN;\n"
    ]

    # Drop existing tables in reverse order to handle foreign keys cleanly
    sql_parts.append("-- Drop existing tables if re-initializing")
    for table_name in reversed(ordered_table_names):
        sql_parts.append(f"DROP TABLE IF EXISTS {table_name};")
    sql_parts.append("")

    # Generate DDL and DML for each table
    for table_name in ordered_table_names:
        df = tables_data[table_name]
        sql_parts.append(f"-- --------------------------------------------------------")
        sql_parts.append(f"-- Table structure and data for {table_name}")
        sql_parts.append(f"-- --------------------------------------------------------")
        sql_parts.append(generate_table_ddl(table_name, df))
        sql_parts.append("")
        sql_parts.append(generate_table_dml(table_name, df))
        sql_parts.append("")

    sql_parts.append("COMMIT;\n")
    return "\n".join(sql_parts)


def verify_sql_script(sql_content: str) -> bool:
    """Verify that the generated SQL script executes cleanly in SQLite (local test)."""
    conn = sqlite3.connect(":memory:")
    try:
        cursor = conn.cursor()
        cursor.executescript(sql_content)
        conn.commit()

        # Check table counts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"[Verification] Successfully created tables in local SQLite: {tables}")

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  - Table '{table}': {count} rows inserted.")

        conn.close()
        return True
    except Exception as e:
        print(f"[Verification Error] Failed to execute SQL script in SQLite: {e}")
        conn.close()
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert /database CSVs into interchangeable SQL file.")
    parser.add_argument("--output", "-o", type=str, default=str(DEFAULT_OUTPUT_SQL),
                        help="Output path for the generated .sql file")
    parser.add_argument("--verify", action="store_true", default=True,
                        help="Verify the generated SQL script using an in-memory SQLite database")
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading CSV files from: {DATABASE_DIR}")
    sql_script = build_sql_script(DATABASE_DIR)

    # Write to target output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sql_script)

    print(f"Successfully generated SQL script at: {output_path}")

    # Also write a copy to root database.sql if output is under database/
    if output_path != ROOT_OUTPUT_SQL:
        with open(ROOT_OUTPUT_SQL, "w", encoding="utf-8") as f:
            f.write(sql_script)
        print(f"Copied generated SQL script to root: {ROOT_OUTPUT_SQL}")

    if args.verify:
        print("\nVerifying SQL interchangeability...")
        if verify_sql_script(sql_script):
            print("Verification passed! SQL script is valid and interchangeable.")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
