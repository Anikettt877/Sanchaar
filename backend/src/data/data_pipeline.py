# c:\Users\anike\OneDrive\Desktop\transit AI\backend\src\data\data_pipeline.py
"""
Master Data Pipeline Orchestrator for TRANSIT AI.

Coordinates the end-to-end data engineering lifecycle:
  Step 1: Download raw MTA subway ridership from NY Open Data API (download_data.py)
  Step 2: Clean, validate, and aggregate fare classes to hourly station ridership (preprocess_data.py)
  Step 3: Engineer temporal, anti-leakage lag, rolling, and demand quartile features (feature_engineering.py)

Can be executed as:
  python -m src.data.data_pipeline
  python backend/src/data/data_pipeline.py

Features:
  - Precise execution timing and profiling per stage
  - Comprehensive logging and progress reporting
  - Automatic fallback to high-fidelity synthetic generator (create_sample_data.py)
    when network access is blocked, API is offline, or explicitly requested via --use-sample.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# Ensure the backend directory is in sys.path for direct and module execution
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import pipeline steps
from src.data.download_data import download_mta_data
from src.data.preprocess_data import preprocess_mta_data
from src.features.feature_engineering import generate_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("data_pipeline")

# File Paths
DEFAULT_RAW_CSV_PATH = BACKEND_DIR / "data" / "raw" / "mta_hourly_ridership_raw.csv"
DEFAULT_AGGREGATED_CSV_PATH = (
    BACKEND_DIR / "data" / "processed" / "ridership_aggregated.csv"
)
DEFAULT_FEATURED_CSV_PATH = (
    BACKEND_DIR / "data" / "processed" / "ridership_featured.csv"
)
DEFAULT_STATION_INFO_CSV_PATH = (
    BACKEND_DIR / "data" / "processed" / "station_info.csv"
)


def run_pipeline(
    target_rows: int = 300000,
    batch_size: int = 50000,
    skip_download: bool = False,
    use_sample: bool = False,
    app_token: Optional[str] = None,
    raw_path: Path = DEFAULT_RAW_CSV_PATH,
    agg_path: Path = DEFAULT_AGGREGATED_CSV_PATH,
    featured_path: Path = DEFAULT_FEATURED_CSV_PATH,
    station_info_path: Path = DEFAULT_STATION_INFO_CSV_PATH,
) -> Dict[str, float]:
    """
    Executes the full Transit AI Data Pipeline sequentially with timing benchmarks.

    Args:
        target_rows: Number of raw records to fetch from MTA API (~200,000-400,000).
        batch_size: Socrata API page size (max 50,000).
        skip_download: Skip download step if raw data already exists.
        use_sample: Force generation of realistic synthetic fallback data.
        app_token: Optional Socrata App Token for MTA API.
        raw_path: Output path for raw CSV.
        agg_path: Output path for aggregated CSV.
        featured_path: Output path for featured CSV.
        station_info_path: Output path for station metadata CSV.

    Returns:
        Dictionary mapping pipeline stage names to their duration in seconds.
    """
    pipeline_start = time.time()
    timing_report: Dict[str, float] = {}

    logger.info("=" * 80)
    logger.info("TRANSIT AI DATA PIPELINE EXECUTION STARTED")
    logger.info(f"Target Raw Rows:     {target_rows:,}")
    logger.info(f"Skip Download:       {skip_download}")
    logger.info(f"Use Sample Fallback: {use_sample}")
    logger.info(f"Backend Directory:   {BACKEND_DIR}")
    logger.info("=" * 80)

    # -------------------------------------------------------------------------
    # STEP 1: INGESTION / DOWNLOAD
    # -------------------------------------------------------------------------
    step1_start = time.time()
    logger.info("\n>>> STEP 1 / 3: DATA INGESTION <<<")

    if use_sample:
        logger.info("Flag --use-sample detected. Invoking synthetic fallback generator...")
        from src.features.create_sample_data import generate_mta_sample_data

        generate_mta_sample_data(
            output_raw_path=raw_path,
            num_stations=50,
            months=6,
        )
        timing_report["Step 1: Data Ingestion (Synthetic Fallback)"] = (
            time.time() - step1_start
        )

    elif skip_download:
        if not raw_path.exists():
            raise FileNotFoundError(
                f"--skip-download was specified, but raw data file does not exist: {raw_path}"
            )
        logger.info(f"Skipping download as requested. Using existing raw file: {raw_path}")
        timing_report["Step 1: Data Ingestion (Skipped)"] = time.time() - step1_start

    else:
        try:
            download_mta_data(
                output_path=raw_path,
                target_rows=target_rows,
                batch_size=batch_size,
                app_token=app_token,
            )
            timing_report["Step 1: Data Ingestion (API Download)"] = (
                time.time() - step1_start
            )
        except Exception as err:
            logger.warning(
                f"Direct API download failed due to network / connectivity issues: {err}"
            )
            logger.info("Engaging automatic fallback to realistic synthetic MTA generator...")
            from src.features.create_sample_data import generate_mta_sample_data

            generate_mta_sample_data(
                output_raw_path=raw_path,
                num_stations=50,
                months=6,
            )
            timing_report["Step 1: Data Ingestion (Fallback Synthetic)"] = (
                time.time() - step1_start
            )

    # -------------------------------------------------------------------------
    # STEP 2: PREPROCESSING AND AGGREGATION
    # -------------------------------------------------------------------------
    step2_start = time.time()
    logger.info("\n>>> STEP 2 / 3: PREPROCESSING & HOURLY AGGREGATION <<<")

    df_agg, _ = preprocess_mta_data(
        input_path=raw_path,
        output_path=agg_path,
    )
    timing_report["Step 2: Preprocessing & Aggregation"] = time.time() - step2_start

    # -------------------------------------------------------------------------
    # STEP 3: FEATURE ENGINEERING
    # -------------------------------------------------------------------------
    step3_start = time.time()
    logger.info("\n>>> STEP 3 / 3: FEATURE ENGINEERING & METADATA EXTRACTION <<<")

    df_featured, df_stations = generate_features(
        input_path=agg_path,
        output_featured_path=featured_path,
        output_station_info_path=station_info_path,
    )
    timing_report["Step 3: Feature Engineering"] = time.time() - step3_start

    # -------------------------------------------------------------------------
    # PIPELINE BENCHMARK REPORT
    # -------------------------------------------------------------------------
    total_elapsed = time.time() - pipeline_start
    timing_report["Total Pipeline Duration"] = total_elapsed

    logger.info("\n" + "=" * 80)
    logger.info("TRANSIT AI DATA PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 80)
    for stage, duration in timing_report.items():
        pct = (duration / total_elapsed) * 100 if total_elapsed > 0 else 0
        if stage == "Total Pipeline Duration":
            logger.info("-" * 80)
            logger.info(f"{stage:<48} : {duration:>7.2f}s (100.0%)")
        else:
            logger.info(f"  - {stage:<44} : {duration:>7.2f}s ({pct:>5.1f}%)")

    logger.info("-" * 80)
    logger.info("GENERATED ARTIFACTS:")
    logger.info(
        f"  1. Raw MTA Data:        {raw_path} ({os.path.getsize(raw_path) / (1024 * 1024):.2f} MB)"
    )
    logger.info(
        f"  2. Aggregated Data:     {agg_path} ({len(df_agg):,} rows, {os.path.getsize(agg_path) / (1024 * 1024):.2f} MB)"
    )
    logger.info(
        f"  3. Featured Data:       {featured_path} ({len(df_featured):,} rows, {os.path.getsize(featured_path) / (1024 * 1024):.2f} MB)"
    )
    logger.info(
        f"  4. Station Info:        {station_info_path} ({len(df_stations):,} stations)"
    )
    logger.info("=" * 80)
    logger.info("ALL PIPELINE STAGES COMPLETED SUCCESSFULLY.")
    logger.info("=" * 80)

    return timing_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Transit AI master data engineering pipeline."
    )
    parser.add_argument(
        "--target-rows",
        type=int,
        default=300000,
        help="Target number of rows to download from MTA API (default: 300000)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50000,
        help="Batch size per Socrata API query (default: 50000)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip the API download step and use existing raw CSV",
    )
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Use realistic synthetic fallback data instead of calling the live API",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Optional MTA / Socrata App Token",
    )

    args = parser.parse_args()

    try:
        run_pipeline(
            target_rows=args.target_rows,
            batch_size=args.batch_size,
            skip_download=args.skip_download,
            use_sample=args.use_sample,
            app_token=args.token,
        )
    except Exception as exc:
        logger.critical(f"Master pipeline run aborted: {exc}", exc_info=True)
        sys.exit(1)
