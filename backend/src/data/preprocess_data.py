# c:\Users\anike\OneDrive\Desktop\transit AI\backend\src\data\preprocess_data.py
"""
MTA Hourly Ridership Data Preprocessing for TRANSIT AI.

Performs data cleaning, validation, and station-level hourly aggregation:
1. Loads raw MTA CSV dataset.
2. Inspects column structures, types, and missingness.
3. Converts timestamps to UTC/local datetime.
4. Converts numerical fields (ridership, transfers, coordinates) to float.
5. Cleans invalid records (negative ridership, unparseable timestamps, duplicates).
6. Aggregates fare classes and payment methods (MetroCard & OMNY) into total
   hourly ridership per station:
   GROUP BY: (station_complex_id, station_complex, borough, latitude, longitude, transit_timestamp)
   AGG: SUM(ridership), SUM(transfers)
7. Saves aggregated dataset to:
   c:/Users/anike/OneDrive/Desktop/transit AI/backend/data/processed/ridership_aggregated.csv
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mta_preprocessor")

# Default paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RAW_CSV_PATH = BACKEND_DIR / "data" / "raw" / "mta_hourly_ridership_raw.csv"
DEFAULT_PROCESSED_CSV_PATH = (
    BACKEND_DIR / "data" / "processed" / "ridership_aggregated.csv"
)

# Core aggregation grouping columns
AGGREGATION_GROUP_COLS = [
    "station_complex_id",
    "station_complex",
    "borough",
    "latitude",
    "longitude",
    "transit_timestamp",
]


def inspect_raw_dataframe(df: pd.DataFrame) -> None:
    """
    Prints diagnostic information about columns, missing values, and memory usage.

    Args:
        df: Raw DataFrame loaded from CSV.
    """
    logger.info("=" * 70)
    logger.info("RAW DATASET DIAGNOSTIC INSPECTION")
    logger.info(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    logger.info(f"Memory Usage: {df.memory_usage(deep=True).sum() / (1024 ** 2):.2f} MB")
    logger.info("-" * 70)
    logger.info(f"{'Column Name':<25} {'Dtype':<15} {'Null Count':<12} {'Null %':<10}")
    logger.info("-" * 70)
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        logger.info(
            f"{col:<25} {str(df[col].dtype):<15} {null_count:<12,} {null_pct:>6.2f}%"
        )
    logger.info("=" * 70)


def preprocess_mta_data(
    input_path: Path = DEFAULT_RAW_CSV_PATH,
    output_path: Path = DEFAULT_PROCESSED_CSV_PATH,
) -> Tuple[pd.DataFrame, Path]:
    """
    Loads raw MTA ridership records, validates values, removes invalid/duplicate
    entries, aggregates over fare classes for each station-hour pair, and saves
    the processed dataset.

    Args:
        input_path: Path to the raw MTA ridership CSV.
        output_path: Path where the aggregated CSV will be written.

    Returns:
        Tuple of (aggregated_dataframe, output_path).
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Raw input data file not found at: {input_path}. "
            "Please run download_data.py or create_sample_data.py first."
        )

    logger.info(f"Loading raw data from: {input_path}")
    start_time = time.time()

    # Read raw CSV
    df = pd.read_csv(input_path, low_memory=False)
    initial_rows = len(df)
    logger.info(f"Successfully loaded {initial_rows:,} raw rows.")

    # Inspect schema and columns
    inspect_raw_dataframe(df)

    # 1. Standardize column names (lowercase, stripped)
    df.columns = [c.strip().lower() for c in df.columns]

    # Verify essential columns exist
    required_cols = [
        "transit_timestamp",
        "station_complex_id",
        "station_complex",
        "borough",
        "ridership",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Raw dataset missing mandatory columns: {missing}")

    # 2. Parse transit_timestamp to datetime
    logger.info("Converting 'transit_timestamp' to datetime...")
    df["transit_timestamp"] = pd.to_datetime(df["transit_timestamp"], errors="coerce")
    invalid_dates = df["transit_timestamp"].isnull().sum()
    if invalid_dates > 0:
        logger.warning(f"Dropping {invalid_dates:,} rows with invalid timestamps.")
        df = df.dropna(subset=["transit_timestamp"])

    # 3. Convert numeric columns (ridership, transfers, coordinates)
    logger.info("Converting numeric columns (ridership, transfers, latitude, longitude)...")
    df["ridership"] = pd.to_numeric(df["ridership"], errors="coerce")
    if "transfers" in df.columns:
        df["transfers"] = pd.to_numeric(df["transfers"], errors="coerce").fillna(0.0)
    else:
        df["transfers"] = 0.0

    if "latitude" in df.columns:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce").round(6)
    else:
        df["latitude"] = np.nan

    if "longitude" in df.columns:
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce").round(6)
    else:
        df["longitude"] = np.nan

    # 4. Clean station complex ID and strings
    df["station_complex_id"] = df["station_complex_id"].astype(str).str.strip()
    df["station_complex"] = df["station_complex"].astype(str).str.strip()
    df["borough"] = df["borough"].astype(str).str.strip()

    # 5. Filter out invalid/negative ridership and NaN ridership
    valid_mask = df["ridership"].notnull() & (df["ridership"] >= 0)
    invalid_ridership_count = (~valid_mask).sum()
    if invalid_ridership_count > 0:
        logger.warning(
            f"Filtering out {invalid_ridership_count:,} rows with negative/NaN ridership."
        )
        df = df[valid_mask]

    # 6. Remove duplicate rows across the raw dataset
    duplicates_count = df.duplicated().sum()
    if duplicates_count > 0:
        logger.info(f"Removing {duplicates_count:,} duplicate rows...")
        df = df.drop_duplicates()

    rows_before_agg = len(df)
    logger.info(f"Cleaned records ready for aggregation: {rows_before_agg:,} rows.")

    # 7. AGGREGATE: Group by station-hour and sum across fare classes and payment methods
    logger.info("Aggregating ridership and transfers across fare classes per station-hour...")
    df_agg = (
        df.groupby(AGGREGATION_GROUP_COLS, as_index=False)
        .agg(
            {
                "ridership": "sum",
                "transfers": "sum",
            }
        )
    )

    # Round aggregated values to 2 decimal places for clean floating point storage
    df_agg["ridership"] = df_agg["ridership"].round(2)
    df_agg["transfers"] = df_agg["transfers"].round(2)

    # 8. Sort chronologically per station
    df_agg = df_agg.sort_values(
        by=["station_complex_id", "transit_timestamp"]
    ).reset_index(drop=True)

    # 9. Save aggregated dataset
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing aggregated dataset to: {output_path}")
    df_agg.to_csv(output_path, index=False)

    duration = time.time() - start_time
    logger.info("=" * 70)
    logger.info("PREPROCESSING AND AGGREGATION SUMMARY")
    logger.info(f"Raw Input Rows:            {initial_rows:,}")
    logger.info(f"Aggregated Hourly Rows:    {len(df_agg):,}")
    logger.info(
        f"Row Reduction Ratio:       {((1 - len(df_agg) / initial_rows) * 100):.1f}% reduction"
    )
    logger.info(f"Unique Station Complexes:  {df_agg['station_complex_id'].nunique():,}")
    logger.info(f"Unique Boroughs:           {df_agg['borough'].unique().tolist()}")
    logger.info(
        f"Date Range:                {df_agg['transit_timestamp'].min()} to {df_agg['transit_timestamp'].max()}"
    )
    logger.info(f"Total Cumulative Ridership: {df_agg['ridership'].sum():,.1f}")
    logger.info(f"Hourly Ridership Mean:      {df_agg['ridership'].mean():.2f}")
    logger.info(f"Hourly Ridership Median:    {df_agg['ridership'].median():.2f}")
    logger.info(f"Hourly Ridership Min / Max: {df_agg['ridership'].min():.1f} / {df_agg['ridership'].max():.1f}")
    logger.info(f"Processing Time Elapsed:   {duration:.2f} seconds")
    logger.info(f"Output File:               {output_path}")
    logger.info("=" * 70)

    return df_agg, output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Preprocess and aggregate raw MTA ridership data."
    )
    parser.add_argument(
        "--input-path",
        type=str,
        default=str(DEFAULT_RAW_CSV_PATH),
        help="Path to raw CSV file",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(DEFAULT_PROCESSED_CSV_PATH),
        help="Path to output aggregated CSV file",
    )

    args = parser.parse_args()

    try:
        preprocess_mta_data(
            input_path=Path(args.input_path),
            output_path=Path(args.output_path),
        )
    except Exception as exc:
        logger.critical(f"Preprocessing failed: {exc}", exc_info=True)
        sys.exit(1)
