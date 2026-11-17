# c:\Users\anike\OneDrive\Desktop\transit AI\backend\src\features\feature_engineering.py
"""
Feature Engineering Module for TRANSIT AI.

Transforms aggregated hourly subway ridership into machine-learning-ready features:
1. Temporal Features:
   - hour (0-23), day_of_week (0-6), day_name (Monday..Sunday)
   - month (1-12), year (2024), is_weekend (0 or 1), quarter (1-4)
   - peak_period: 'morning_peak' (7-10), 'evening_peak' (16-19), 'midday' (10-16), 'night' (others)
2. Lag Features (strictly strictly shifted to avoid data leakage):
   - ridership_lag_1h: ridership 1 hour prior
   - ridership_lag_24h: ridership 24 hours prior (same hour previous day)
   - ridership_lag_168h: ridership 168 hours prior (same hour previous week)
3. Rolling Features (strictly shifted prior to computing window):
   - ridership_rolling_mean_24h: 24-hour moving average of historical ridership
   - ridership_rolling_std_24h: 24-hour moving standard deviation of historical ridership
4. Target Demand Classification:
   - demand_level: quartile-based categorizations (Low, Moderate, High, Very High)
5. Station Metadata Persistence:
   - station_info.csv: unique station identifiers, names, borough, and coordinates.

Outputs:
   - c:/Users/anike/OneDrive/Desktop/transit AI/backend/data/processed/ridership_featured.csv
   - c:/Users/anike/OneDrive/Desktop/transit AI/backend/data/processed/station_info.csv
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("feature_engineering")

# Default Paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_AGGREGATED_CSV_PATH = (
    BACKEND_DIR / "data" / "processed" / "ridership_aggregated.csv"
)
DEFAULT_FEATURED_CSV_PATH = (
    BACKEND_DIR / "data" / "processed" / "ridership_featured.csv"
)
DEFAULT_STATION_INFO_CSV_PATH = (
    BACKEND_DIR / "data" / "processed" / "station_info.csv"
)


def extract_station_info(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Extracts unique station complex details and saves them as a reference table.

    Columns:
        - id: station_complex_id
        - name: station_complex
        - borough: borough
        - lat: latitude
        - lon: longitude

    Args:
        df: Aggregated DataFrame containing station attributes.
        output_path: Path to write station_info.csv.

    Returns:
        Deduplicated station metadata DataFrame.
    """
    logger.info("Extracting unique station metadata...")
    station_cols = [
        "station_complex_id",
        "station_complex",
        "borough",
        "latitude",
        "longitude",
    ]

    # Deduplicate on station_complex_id
    station_info = (
        df[station_cols]
        .drop_duplicates(subset=["station_complex_id"])
        .rename(
            columns={
                "station_complex_id": "id",
                "station_complex": "name",
                "borough": "borough",
                "latitude": "lat",
                "longitude": "lon",
            }
        )
        .sort_values(by="id")
        .reset_index(drop=True)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    station_info.to_csv(output_path, index=False)
    logger.info(
        f"Saved {len(station_info):,} unique stations to reference file: {output_path}"
    )
    return station_info


def classify_peak_period(hour: int) -> str:
    """
    Classifies hour of day into operational peak periods:
        - morning_peak: 7 to 9:59 (7 <= hour < 10)
        - midday: 10 to 15:59 (10 <= hour < 16)
        - evening_peak: 16 to 19:59 (16 <= hour < 20)
        - night: all remaining hours (20-23, 0-6)
    """
    if 7 <= hour < 10:
        return "morning_peak"
    elif 10 <= hour < 16:
        return "midday"
    elif 16 <= hour < 20:
        return "evening_peak"
    else:
        return "night"


def compute_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives calendar and cyclical temporal attributes from transit_timestamp.

    Features generated:
        - hour, day_of_week, day_name, month, year, is_weekend, quarter, peak_period
    """
    logger.info("Computing temporal calendar features...")
    ts = df["transit_timestamp"]

    df["hour"] = ts.dt.hour
    df["day_of_week"] = ts.dt.dayofweek
    df["day_name"] = ts.dt.day_name()
    df["month"] = ts.dt.month
    df["year"] = ts.dt.year
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["quarter"] = ts.dt.quarter
    df["peak_period"] = df["hour"].apply(classify_peak_period)

    return df


def compute_lag_and_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates historical lag and rolling statistics per station.

    CRITICAL ANTI-LEAKAGE DESIGN:
    All lag and rolling features are strictly computed using .shift() so that
    at any given timestamp t, only observations prior to t (<= t-1) are used.
    Current-hour ridership is never included in the historical window.

    Features generated:
        - ridership_lag_1h: shift(1)
        - ridership_lag_24h: shift(24)
        - ridership_lag_168h: shift(168) (1 week prior)
        - ridership_rolling_mean_24h: shift(1).rolling(24).mean()
        - ridership_rolling_std_24h: shift(1).rolling(24).std()
    """
    logger.info("Sorting data by station and timestamp prior to lag computation...")
    # Sorting is essential for shift() to reflect exact chronological order
    df = df.sort_values(by=["station_complex_id", "transit_timestamp"]).reset_index(
        drop=True
    )

    logger.info("Computing lag features (1h, 24h, 168h) per station...")
    grouped = df.groupby("station_complex_id")["ridership"]

    # Compute lags strictly shifting past values
    df["ridership_lag_1h"] = grouped.shift(1)
    df["ridership_lag_24h"] = grouped.shift(24)
    df["ridership_lag_168h"] = grouped.shift(168)

    logger.info("Computing rolling 24h statistics (mean and std) with shift(1)...")
    # shift(1) ensures the current observation is excluded from the rolling window
    df["ridership_rolling_mean_24h"] = grouped.transform(
        lambda s: s.shift(1).rolling(window=24, min_periods=1).mean()
    ).round(2)

    df["ridership_rolling_std_24h"] = grouped.transform(
        lambda s: s.shift(1).rolling(window=24, min_periods=2).std()
    ).fillna(0.0).round(2)

    # Drop initial rows where lag features are NaN (e.g. first 168 hours per station)
    lag_cols = ["ridership_lag_1h", "ridership_lag_24h", "ridership_lag_168h"]
    initial_count = len(df)
    df = df.dropna(subset=lag_cols).reset_index(drop=True)
    dropped_count = initial_count - len(df)

    logger.info(
        f"Dropped {dropped_count:,} initial burn-in rows with NaN lag values. "
        f"Remaining rows: {len(df):,}"
    )

    return df


def compute_demand_levels(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Categorizes hourly ridership into quartile demand tiers:
        - Low:       ridership < Q1
        - Moderate:  Q1 <= ridership <= Q2
        - High:      Q2 < ridership <= Q3
        - Very High: ridership > Q3

    Args:
        df: DataFrame containing the 'ridership' column.

    Returns:
        Tuple of (df_with_demand_level, quartile_thresholds_dict).
    """
    logger.info("Computing empirical ridership quartiles for demand categorization...")
    q1 = float(df["ridership"].quantile(0.25))
    q2 = float(df["ridership"].quantile(0.50))
    q3 = float(df["ridership"].quantile(0.75))

    logger.info(
        f"Quartiles: Q1 (25%) = {q1:.2f} | Q2 (Median) = {q2:.2f} | Q3 (75%) = {q3:.2f}"
    )

    def assign_level(val: float) -> str:
        if val < q1:
            return "Low"
        elif val <= q2:
            return "Moderate"
        elif val <= q3:
            return "High"
        else:
            return "Very High"

    df["demand_level"] = df["ridership"].apply(assign_level)

    # Print distribution
    dist = df["demand_level"].value_counts(normalize=True) * 100
    for level in ["Low", "Moderate", "High", "Very High"]:
        pct = dist.get(level, 0.0)
        count = (df["demand_level"] == level).sum()
        logger.info(f"Demand Tier '{level:<9}': {count:>8,} rows ({pct:>5.1f}%)")

    thresholds = {"q1": q1, "q2": q2, "q3": q3}
    return df, thresholds


def generate_features(
    input_path: Path = DEFAULT_AGGREGATED_CSV_PATH,
    output_featured_path: Path = DEFAULT_FEATURED_CSV_PATH,
    output_station_info_path: Path = DEFAULT_STATION_INFO_CSV_PATH,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full feature engineering pipeline: loads aggregated ridership data, creates
    temporal features, computes anti-leakage lag and rolling features, bins demand levels,
    and extracts station metadata.

    Args:
        input_path: Path to ridership_aggregated.csv.
        output_featured_path: Path for output featured CSV.
        output_station_info_path: Path for output station_info.csv.

    Returns:
        Tuple of (featured_dataframe, station_info_dataframe).
    """
    input_path = Path(input_path)
    output_featured_path = Path(output_featured_path)
    output_station_info_path = Path(output_station_info_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Aggregated ridership data file not found at: {input_path}. "
            "Please run preprocess_data.py first."
        )

    logger.info(f"Loading aggregated dataset from: {input_path}")
    start_time = time.time()
    df = pd.read_csv(input_path, parse_dates=["transit_timestamp"])
    logger.info(f"Loaded {len(df):,} aggregated records.")

    # 1. Save station metadata
    station_info = extract_station_info(df, output_station_info_path)

    # 2. Derive calendar and peak period features
    df = compute_time_features(df)

    # 3. Compute lag and rolling features with strict leakage prevention
    df = compute_lag_and_rolling_features(df)

    # 4. Compute quartile-based demand levels
    df, _ = compute_demand_levels(df)

    # 5. Save final featured dataset
    output_featured_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing engineered dataset to: {output_featured_path}")
    df.to_csv(output_featured_path, index=False)

    duration = time.time() - start_time
    logger.info("=" * 70)
    logger.info("FEATURE ENGINEERING COMPLETE")
    logger.info(f"Final Featured Dataset Rows:    {len(df):,}")
    logger.info(f"Total Columns:                  {len(df.columns)}")
    logger.info(f"Columns List:                   {list(df.columns)}")
    logger.info(f"Feature Engineering Duration:   {duration:.2f} seconds")
    logger.info(f"Featured CSV Output:            {output_featured_path}")
    logger.info(f"Station Info CSV Output:        {output_station_info_path}")
    logger.info("=" * 70)

    return df, station_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Engineer features on aggregated MTA subway ridership data."
    )
    parser.add_argument(
        "--input-path",
        type=str,
        default=str(DEFAULT_AGGREGATED_CSV_PATH),
        help="Input aggregated CSV path",
    )
    parser.add_argument(
        "--output-featured",
        type=str,
        default=str(DEFAULT_FEATURED_CSV_PATH),
        help="Output featured CSV path",
    )
    parser.add_argument(
        "--output-station-info",
        type=str,
        default=str(DEFAULT_STATION_INFO_CSV_PATH),
        help="Output station info CSV path",
    )

    args = parser.parse_args()

    try:
        generate_features(
            input_path=Path(args.input_path),
            output_featured_path=Path(args.output_featured),
            output_station_info_path=Path(args.output_station_info),
        )
    except Exception as exc:
        logger.critical(f"Feature engineering failed: {exc}", exc_info=True)
        sys.exit(1)
