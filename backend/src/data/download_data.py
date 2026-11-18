# c:\Users\anike\OneDrive\Desktop\transit AI\backend\src\data\download_data.py
"""
MTA Hourly Ridership Data Downloader for Sanchaar.

Downloads subway ridership data from the NY Open Data Socrata API:
Endpoint: https://data.ny.gov/resource/wujg-7c2s.json
Filters:
    - transit_mode = 'subway'
    - transit_timestamp >= '2024-01-01' AND transit_timestamp < '2024-07-01'
Pagination:
    - $limit: up to 50,000 records per request
    - $offset: incremental offset for pagination
    - Target: ~200,000 - 400,000 rows
Features:
    - Exponential backoff retry logic for resilient downloads
    - Chunked streaming write to CSV to conserve memory
    - Real-time progress monitoring and throughput tracking
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mta_downloader")

# Socrata API Endpoint & Configuration
MTA_API_ENDPOINT = "https://data.ny.gov/resource/wujg-7c2s.json"
DEFAULT_LIMIT = 50000
DEFAULT_TARGET_ROWS = 300000
DEFAULT_TIMEOUT_SECONDS = 90
DEFAULT_MAX_RETRIES = 5
DEFAULT_BACKOFF_FACTOR = 2.0

# Base Paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RAW_CSV_PATH = BACKEND_DIR / "data" / "raw" / "mta_hourly_ridership_raw.csv"

# SoQL Filter for Subway 2024 H1 (Jan 1, 2024 to Jun 30, 2024)
DEFAULT_WHERE_FILTER = (
    "transit_mode='subway' AND "
    "transit_timestamp >= '2024-01-01' AND "
    "transit_timestamp < '2024-07-01'"
)


def create_resilient_session(
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> requests.Session:
    """
    Creates and configures a requests.Session with automated retry logic
    for handling transient connection drops, rate-limiting, and server errors.

    Args:
        max_retries: Maximum number of retry attempts for failed requests.
        backoff_factor: Multiplier for exponential backoff delay.

    Returns:
        Configured requests.Session object.
    """
    session = requests.Session()
    status_forcelist = [429, 500, 502, 503, 504]

    retry_strategy = Retry(
        total=max_retries,
        read=max_retries,
        connect=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_batch_with_retry(
    session: requests.Session,
    endpoint: str,
    params: Dict[str, str],
    headers: Dict[str, str],
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> List[Dict]:
    """
    Fetches a single batch from the Socrata API with manual retry fallback
    and detailed error diagnostics.

    Args:
        session: Active requests session.
        endpoint: Socrata API URL.
        params: Query parameters including $limit, $offset, and $where.
        headers: Request headers (e.g. app tokens).
        timeout: Request timeout in seconds.
        max_retries: Maximum retries on network exception.
        backoff_factor: Multiplicative backoff factor.

    Returns:
        List of JSON dictionaries representing rows.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                f"Requesting batch at offset {params.get('$offset')} "
                f"(limit={params.get('$limit')}, attempt {attempt}/{max_retries})..."
            )
            response = session.get(
                endpoint,
                params=params,
                headers=headers,
                timeout=timeout,
            )

            # Check HTTP status codes
            if response.status_code == 200:
                data = response.json()
                if not isinstance(data, list):
                    logger.warning(f"Unexpected API response payload: {data}")
                    return []
                return data

            elif response.status_code == 429:
                wait_time = backoff_factor * (2 ** (attempt - 1)) + 5.0
                logger.warning(
                    f"Rate limited (HTTP 429). Backing off for {wait_time:.1f}s before retry..."
                )
                time.sleep(wait_time)

            elif 500 <= response.status_code < 600:
                wait_time = backoff_factor * (2 ** (attempt - 1))
                logger.warning(
                    f"Server error (HTTP {response.status_code}). Backing off for {wait_time:.1f}s..."
                )
                time.sleep(wait_time)

            else:
                logger.error(
                    f"HTTP error {response.status_code}: {response.text[:200]}"
                )
                response.raise_for_status()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            wait_time = backoff_factor * (2 ** (attempt - 1))
            logger.warning(
                f"Network issue encountered ({type(e).__name__}): {e}. "
                f"Retrying in {wait_time:.1f}s (attempt {attempt}/{max_retries})..."
            )
            time.sleep(wait_time)

        except requests.exceptions.RequestException as e:
            wait_time = backoff_factor * (2 ** (attempt - 1))
            logger.error(f"Request exception: {e}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

    raise ConnectionError(
        f"Failed to fetch batch at offset {params.get('$offset')} after {max_retries} attempts."
    )


def download_mta_data(
    output_path: Path = DEFAULT_RAW_CSV_PATH,
    target_rows: int = DEFAULT_TARGET_ROWS,
    batch_size: int = DEFAULT_LIMIT,
    where_filter: str = DEFAULT_WHERE_FILTER,
    app_token: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Tuple[int, Path]:
    """
    Downloads MTA hourly ridership data and streams records to a CSV file.

    Args:
        output_path: Destination path for the raw CSV dataset.
        target_rows: Desired number of rows to download (~200,000 - 400,000).
        batch_size: Number of records to request per page (max 50,000).
        where_filter: SoQL $where clause for filtering.
        app_token: Optional Socrata App Token for higher rate limits.
        timeout: HTTP request timeout in seconds.

    Returns:
        Tuple of (total_rows_downloaded, output_file_path).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "Accept": "application/json",
        "User-Agent": "Sanchaar-DataPipeline/1.0",
    }
    token = app_token or os.getenv("MTA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token
        logger.info("Using authenticated Socrata App Token.")
    else:
        logger.info("No MTA_APP_TOKEN provided. Proceeding with public rate limits.")

    session = create_resilient_session()
    offset = 0
    total_downloaded = 0
    start_time = time.time()
    batch_index = 0

    logger.info("=" * 70)
    logger.info("STARTING MTA HOURLY RIDERSHIP DATA INGESTION")
    logger.info(f"Endpoint: {MTA_API_ENDPOINT}")
    logger.info(f"Target Rows: {target_rows:,}")
    logger.info(f"Batch Size: {batch_size:,}")
    logger.info(f"Filter ($where): {where_filter}")
    logger.info(f"Target Output Path: {output_path}")
    logger.info("=" * 70)

    try:
        while total_downloaded < target_rows:
            batch_limit = min(batch_size, target_rows - total_downloaded)
            params = {
                "$limit": str(batch_limit),
                "$offset": str(offset),
                "$where": where_filter,
                "$order": "transit_timestamp ASC, station_complex_id ASC",
            }

            batch_data = fetch_batch_with_retry(
                session=session,
                endpoint=MTA_API_ENDPOINT,
                params=params,
                headers=headers,
                timeout=timeout,
            )

            batch_count = len(batch_data)
            if batch_count == 0:
                logger.info("Received empty response from API; end of data stream reached.")
                break

            # Convert batch to DataFrame for standardized CSV writing
            df_batch = pd.DataFrame(batch_data)

            # Flatten georeference if present as dict for CSV cleanliness
            if "georeference" in df_batch.columns:
                df_batch["georeference"] = df_batch["georeference"].astype(str)

            # Append to CSV: write header on first batch only
            is_first_batch = (batch_index == 0)
            df_batch.to_csv(
                output_path,
                mode="w" if is_first_batch else "a",
                header=is_first_batch,
                index=False,
            )

            total_downloaded += batch_count
            offset += batch_count
            batch_index += 1

            elapsed = time.time() - start_time
            rate = total_downloaded / elapsed if elapsed > 0 else 0
            progress_pct = (total_downloaded / target_rows) * 100

            logger.info(
                f"Batch {batch_index:02d} written: +{batch_count:,} rows | "
                f"Total: {total_downloaded:,}/{target_rows:,} ({progress_pct:.1f}%) | "
                f"Elapsed: {elapsed:.1f}s | Speed: {rate:.0f} rows/s"
            )

            # If the API returned fewer rows than requested, there is no more data
            if batch_count < batch_limit:
                logger.info("Batch count less than limit; all available records collected.")
                break

            # Short polite pause between batches to prevent 429
            time.sleep(0.5)

    except Exception as e:
        logger.error(f"Download pipeline aborted due to error: {e}", exc_info=True)
        if total_downloaded > 0:
            logger.info(
                f"Partial dataset preserved at {output_path} ({total_downloaded:,} rows)."
            )
        raise

    total_duration = time.time() - start_time
    logger.info("=" * 70)
    logger.info("DOWNLOAD COMPLETE")
    logger.info(f"Total Rows Downloaded: {total_downloaded:,}")
    logger.info(f"Total Time Elapsed: {total_duration:.2f} seconds")
    logger.info(f"Average Download Rate: {total_downloaded / total_duration:.1f} rows/second")
    logger.info(f"Raw CSV File: {output_path}")
    logger.info("=" * 70)

    return total_downloaded, output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download NYC MTA Hourly Subway Ridership data."
    )
    parser.add_argument(
        "--target-rows",
        type=int,
        default=DEFAULT_TARGET_ROWS,
        help="Target number of rows to download (default: 300000)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_LIMIT,
        help="Batch limit per API call (default: 50000)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(DEFAULT_RAW_CSV_PATH),
        help="Output CSV path",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="MTA / Socrata API token",
    )

    args = parser.parse_args()

    try:
        download_mta_data(
            output_path=Path(args.output_path),
            target_rows=args.target_rows,
            batch_size=args.batch_size,
            app_token=args.token,
        )
    except Exception as exc:
        logger.critical(f"Execution failed: {exc}")
        sys.exit(1)
