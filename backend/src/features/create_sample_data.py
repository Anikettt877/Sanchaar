# c:\Users\anike\OneDrive\Desktop\transit AI\backend\src\features\create_sample_data.py
"""
Realistic Synthetic Fallback Dataset Generator for TRANSIT AI.

IMPORTANT:
This script is a FALLBACK utility designed for offline environments, API downtime,
or sandbox testing when external network access to https://data.ny.gov is unavailable.
All generated data is explicitly flagged as SYNTHETIC.

Dataset Specifications:
  - 50+ Real NYC Subway Station Complexes with verified MTA complex IDs, coordinates, and boroughs.
  - 6 Months of hourly records: 2024-01-01 00:00:00 to 2024-06-30 23:00:00 (4,368 hours).
  - Exact MTA Socrata Schema:
      transit_timestamp, transit_mode, station_complex_id, station_complex,
      borough, payment_method, fare_class_category, ridership, transfers,
      latitude, longitude, georeference
  - Realistic NYC Transit Dynamics:
      * Morning peak surges (7:00 - 10:00) and evening peak surges (16:00 - 20:00)
      * Weekday vs. weekend differentials (~50% reduction on weekends)
      * Borough hierarchy (Manhattan major hubs vs. outer borough residential stops)
      * OMNY vs. MetroCard adoption distribution (~65% OMNY, ~35% MetroCard in 2024)
      * Natural stochastic noise
  - Output Size: ~450,000 raw rows (within the target ~200,000 - 500,000 rows).

Saves directly to:
  c:/Users/anike/OneDrive/Desktop/transit AI/backend/data/raw/mta_hourly_ridership_raw.csv
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mta_fallback_generator")

# Default Paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RAW_CSV_PATH = BACKEND_DIR / "data" / "raw" / "mta_hourly_ridership_raw.csv"

# 52 Verified Real NYC Subway Stations with official coordinates and MTA complex IDs
NYC_REAL_STATIONS: List[Dict] = [
    # Manhattan Hubs & Core Stations
    {
        "id": "611",
        "name": "Times Sq-42 St / 42 St-Port Authority Bus Terminal",
        "borough": "Manhattan",
        "lat": 40.7553,
        "lon": -73.9875,
        "base_ridership": 4200,
    },
    {
        "id": "610",
        "name": "Grand Central-42 St",
        "borough": "Manhattan",
        "lat": 40.7517,
        "lon": -73.9768,
        "base_ridership": 4000,
    },
    {
        "id": "609",
        "name": "34 St-Penn Station (1,2,3)",
        "borough": "Manhattan",
        "lat": 40.7504,
        "lon": -73.9911,
        "base_ridership": 3600,
    },
    {
        "id": "608",
        "name": "34 St-Penn Station (A,C,E)",
        "borough": "Manhattan",
        "lat": 40.7523,
        "lon": -73.9934,
        "base_ridership": 3400,
    },
    {
        "id": "607",
        "name": "34 St-Herald Sq",
        "borough": "Manhattan",
        "lat": 40.7497,
        "lon": -73.9878,
        "base_ridership": 3300,
    },
    {
        "id": "606",
        "name": "14 St-Union Sq",
        "borough": "Manhattan",
        "lat": 40.7348,
        "lon": -73.9907,
        "base_ridership": 3100,
    },
    {
        "id": "614",
        "name": "Fulton St",
        "borough": "Manhattan",
        "lat": 40.7100,
        "lon": -74.0075,
        "base_ridership": 2800,
    },
    {
        "id": "612",
        "name": "59 St-Columbus Circle",
        "borough": "Manhattan",
        "lat": 40.7683,
        "lon": -73.9819,
        "base_ridership": 2600,
    },
    {
        "id": "616",
        "name": "World Trade Center / Chambers St",
        "borough": "Manhattan",
        "lat": 40.7126,
        "lon": -74.0099,
        "base_ridership": 2500,
    },
    {
        "id": "613",
        "name": "Lexington Av/59 St",
        "borough": "Manhattan",
        "lat": 40.7628,
        "lon": -73.9677,
        "base_ridership": 2400,
    },
    {
        "id": "229",
        "name": "47-50 Sts-Rockefeller Ctr",
        "borough": "Manhattan",
        "lat": 40.7587,
        "lon": -73.9791,
        "base_ridership": 2700,
    },
    {
        "id": "605",
        "name": "W 4 St-Wash Sq",
        "borough": "Manhattan",
        "lat": 40.7323,
        "lon": -74.0005,
        "base_ridership": 2300,
    },
    {
        "id": "617",
        "name": "Canal St",
        "borough": "Manhattan",
        "lat": 40.7188,
        "lon": -74.0008,
        "base_ridership": 2200,
    },
    {
        "id": "615",
        "name": "Lexington Av/53 St",
        "borough": "Manhattan",
        "lat": 40.7576,
        "lon": -73.9719,
        "base_ridership": 2100,
    },
    {
        "id": "275",
        "name": "5 Av/53 St",
        "borough": "Manhattan",
        "lat": 40.7602,
        "lon": -73.9752,
        "base_ridership": 1900,
    },
    {
        "id": "620",
        "name": "Brooklyn Bridge-City Hall",
        "borough": "Manhattan",
        "lat": 40.7131,
        "lon": -74.0041,
        "base_ridership": 1900,
    },
    {
        "id": "397",
        "name": "Wall St (4,5)",
        "borough": "Manhattan",
        "lat": 40.7076,
        "lon": -74.0093,
        "base_ridership": 1800,
    },
    {
        "id": "416",
        "name": "Wall St (2,3)",
        "borough": "Manhattan",
        "lat": 40.7068,
        "lon": -74.0091,
        "base_ridership": 1700,
    },
    {
        "id": "621",
        "name": "Delancey St-Essex St",
        "borough": "Manhattan",
        "lat": 40.7186,
        "lon": -73.9881,
        "base_ridership": 1700,
    },
    {
        "id": "283",
        "name": "72 St (1,2,3)",
        "borough": "Manhattan",
        "lat": 40.7784,
        "lon": -73.9820,
        "base_ridership": 1800,
    },
    {
        "id": "281",
        "name": "96 St (1,2,3)",
        "borough": "Manhattan",
        "lat": 40.7939,
        "lon": -73.9723,
        "base_ridership": 1600,
    },
    {
        "id": "208",
        "name": "125 St (A,B,C,D)",
        "borough": "Manhattan",
        "lat": 40.8111,
        "lon": -73.9523,
        "base_ridership": 1950,
    },
    {
        "id": "383",
        "name": "125 St (4,5,6)",
        "borough": "Manhattan",
        "lat": 40.8041,
        "lon": -73.9376,
        "base_ridership": 1850,
    },
    {
        "id": "399",
        "name": "Bowling Green",
        "borough": "Manhattan",
        "lat": 40.7048,
        "lon": -74.0140,
        "base_ridership": 1500,
    },
    {
        "id": "400",
        "name": "South Ferry",
        "borough": "Manhattan",
        "lat": 40.7021,
        "lon": -74.0130,
        "base_ridership": 1400,
    },
    {
        "id": "168",
        "name": "Spring St (C,E)",
        "borough": "Manhattan",
        "lat": 40.7262,
        "lon": -74.0037,
        "base_ridership": 1300,
    },
    {
        "id": "319",
        "name": "28 St (1)",
        "borough": "Manhattan",
        "lat": 40.7472,
        "lon": -73.9934,
        "base_ridership": 1250,
    },
    {
        "id": "326",
        "name": "Astor Pl (6)",
        "borough": "Manhattan",
        "lat": 40.7301,
        "lon": -73.9911,
        "base_ridership": 1200,
    },
    {
        "id": "298",
        "name": "8 St-NYU (R,W)",
        "borough": "Manhattan",
        "lat": 40.7303,
        "lon": -73.9926,
        "base_ridership": 1150,
    },
    {
        "id": "324",
        "name": "Houston St (1)",
        "borough": "Manhattan",
        "lat": 40.7283,
        "lon": -74.0054,
        "base_ridership": 1100,
    },
    # Brooklyn Hubs & Stations
    {
        "id": "618",
        "name": "Atlantic Av-Barclays Ctr",
        "borough": "Brooklyn",
        "lat": 40.6837,
        "lon": -73.9788,
        "base_ridership": 2900,
    },
    {
        "id": "622",
        "name": "Jay St-MetroTech",
        "borough": "Brooklyn",
        "lat": 40.6923,
        "lon": -73.9873,
        "base_ridership": 2400,
    },
    {
        "id": "619",
        "name": "Court St-Borough Hall",
        "borough": "Brooklyn",
        "lat": 40.6933,
        "lon": -73.9902,
        "base_ridership": 2000,
    },
    {
        "id": "122",
        "name": "Bedford Av (L)",
        "borough": "Brooklyn",
        "lat": 40.7173,
        "lon": -73.9569,
        "base_ridership": 1800,
    },
    {
        "id": "347",
        "name": "Crown Hts-Utica Av",
        "borough": "Brooklyn",
        "lat": 40.6689,
        "lon": -73.9329,
        "base_ridership": 1400,
    },
    {
        "id": "628",
        "name": "Broadway Junction",
        "borough": "Brooklyn",
        "lat": 40.6783,
        "lon": -73.9037,
        "base_ridership": 1350,
    },
    {
        "id": "624",
        "name": "Franklin Av / Botanic Garden",
        "borough": "Brooklyn",
        "lat": 40.6708,
        "lon": -73.9592,
        "base_ridership": 1300,
    },
    {
        "id": "623",
        "name": "Myrtle-Wyckoff Avs",
        "borough": "Brooklyn",
        "lat": 40.6994,
        "lon": -73.9114,
        "base_ridership": 1250,
    },
    {
        "id": "49",
        "name": "Church Av (B,Q)",
        "borough": "Brooklyn",
        "lat": 40.6508,
        "lon": -73.9629,
        "base_ridership": 1150,
    },
    {
        "id": "43",
        "name": "Coney Island-Stillwell Av",
        "borough": "Brooklyn",
        "lat": 40.5771,
        "lon": -73.9812,
        "base_ridership": 1100,
    },
    {
        "id": "45",
        "name": "Kings Highway (B,Q)",
        "borough": "Brooklyn",
        "lat": 40.6087,
        "lon": -73.9578,
        "base_ridership": 1050,
    },
    # Queens Stations
    {
        "id": "467",
        "name": "Flushing-Main St",
        "borough": "Queens",
        "lat": 40.7596,
        "lon": -73.8300,
        "base_ridership": 2600,
    },
    {
        "id": "627",
        "name": "Jackson Hts-Roosevelt Av / 74 St",
        "borough": "Queens",
        "lat": 40.7467,
        "lon": -73.8913,
        "base_ridership": 2500,
    },
    {
        "id": "629",
        "name": "Sutphin Blvd-Archer Av-JFK",
        "borough": "Queens",
        "lat": 40.7005,
        "lon": -73.8078,
        "base_ridership": 1800,
    },
    {
        "id": "269",
        "name": "Forest Hills-71 Av",
        "borough": "Queens",
        "lat": 40.7214,
        "lon": -73.8445,
        "base_ridership": 1750,
    },
    {
        "id": "475",
        "name": "Queensboro Plaza",
        "borough": "Queens",
        "lat": 40.7506,
        "lon": -73.9402,
        "base_ridership": 1600,
    },
    {
        "id": "626",
        "name": "Court Sq-23 St",
        "borough": "Queens",
        "lat": 40.7471,
        "lon": -73.9453,
        "base_ridership": 1500,
    },
    {
        "id": "279",
        "name": "Astoria-Ditmars Blvd",
        "borough": "Queens",
        "lat": 40.7750,
        "lon": -73.9120,
        "base_ridership": 1200,
    },
    # Bronx Stations
    {
        "id": "625",
        "name": "161 St-Yankee Stadium",
        "borough": "Bronx",
        "lat": 40.8279,
        "lon": -73.9257,
        "base_ridership": 1700,
    },
    {
        "id": "380",
        "name": "3 Av-149 St",
        "borough": "Bronx",
        "lat": 40.8161,
        "lon": -73.9178,
        "base_ridership": 1550,
    },
    {
        "id": "370",
        "name": "Fordham Rd (4)",
        "borough": "Bronx",
        "lat": 40.8613,
        "lon": -73.8977,
        "base_ridership": 1400,
    },
    {
        "id": "410",
        "name": "Pelham Bay Park",
        "borough": "Bronx",
        "lat": 40.8525,
        "lon": -73.8281,
        "base_ridership": 1000,
    },
]


def compute_hourly_profile_multiplier(hours: np.ndarray) -> np.ndarray:
    """
    Computes diurnal ridership multiplier for hours 0..23:
      - Morning rush (7-9 AM): ~2.5x to 3.2x
      - Midday plateau (10 AM - 3 PM): ~1.2x to 1.4x
      - Evening rush (4-7 PM): ~2.8x to 3.6x
      - Night taper (8-11 PM): ~0.6x to 1.0x
      - Graveyard hours (12-5 AM): ~0.08x to 0.20x
    """
    multiplier = np.zeros_like(hours, dtype=float)

    # Late night / early morning (0 to 5)
    mask_night = (hours >= 0) & (hours < 6)
    multiplier[mask_night] = 0.08 + 0.02 * hours[mask_night]

    # Morning surge (6 to 9)
    mask_morning = (hours >= 6) & (hours < 10)
    # Peak at 8 AM
    multiplier[mask_morning] = 1.2 + 2.0 * np.sin(
        (hours[mask_morning] - 6) / 3.0 * (np.pi / 2)
    )

    # Midday (10 to 15)
    mask_midday = (hours >= 10) & (hours < 16)
    multiplier[mask_midday] = 1.35 + 0.15 * np.cos(
        (hours[mask_midday] - 10) / 6.0 * np.pi
    )

    # Evening peak (16 to 19)
    mask_evening = (hours >= 16) & (hours < 20)
    multiplier[mask_evening] = 1.5 + 2.0 * np.sin(
        (hours[mask_evening] - 16) / 3.0 * (np.pi / 2)
    )

    # Night taper (20 to 23)
    mask_late = hours >= 20
    multiplier[mask_late] = 1.2 - 0.25 * (hours[mask_late] - 20)

    return np.clip(multiplier, 0.05, 4.0)


def generate_mta_sample_data(
    output_raw_path: Path = DEFAULT_RAW_CSV_PATH,
    num_stations: int = 50,
    months: int = 6,
    random_seed: int = 42,
) -> Tuple[int, Path]:
    """
    Generates a high-fidelity synthetic fallback dataset mirroring the MTA schema.

    Args:
        output_raw_path: Destination path for the raw CSV.
        num_stations: Number of subway stations to include (max 52).
        months: Duration of simulation (1 to 6 months in 2024).
        random_seed: PRNG seed for deterministic simulation.

    Returns:
        Tuple of (total_rows_generated, output_path).
    """
    np.random.seed(random_seed)
    start_time = time.time()
    output_raw_path = Path(output_raw_path)
    output_raw_path.parent.mkdir(parents=True, exist_ok=True)

    stations = NYC_REAL_STATIONS[: min(num_stations, len(NYC_REAL_STATIONS))]
    logger.info("=" * 75)
    logger.info("ENGAGING REALISTIC MTA SYNTHETIC FALLBACK DATA GENERATOR")
    logger.info(f"Target Stations:   {len(stations)} NYC Subway Stations")
    logger.info(f"Simulation Period: {months} Months (2024-01-01 to 2024-06-30)")
    logger.info(f"Target Path:       {output_raw_path}")
    logger.info("=" * 75)

    # Generate complete hourly timestamps for Jan 1 to Jun 30, 2024
    start_date = "2024-01-01 00:00:00"
    end_date = "2024-06-30 23:00:00" if months == 6 else f"2024-0{months}-28 23:00:00"
    timestamps = pd.date_range(start=start_date, end=end_date, freq="h")
    num_hours = len(timestamps)
    logger.info(f"Hourly ticks per station: {num_hours:,} hours")

    hours = timestamps.hour.values
    dows = timestamps.dayofweek.values
    month_arr = timestamps.month.values

    # Diurnal multiplier
    hour_mult = compute_hourly_profile_multiplier(hours)

    # Day-of-week multiplier (weekdays ~1.0, Saturday ~0.55, Sunday ~0.45)
    dow_mult = np.ones(num_hours, dtype=float)
    dow_mult[dows == 4] = 1.05  # Friday evening bump
    dow_mult[dows == 5] = 0.54  # Saturday
    dow_mult[dows == 6] = 0.44  # Sunday

    # Seasonal temperature/activity multiplier (Jan=0.92, Jun=1.06)
    month_mult = 0.92 + 0.028 * (month_arr - 1)

    all_dfs = []

    for i, st in enumerate(stations):
        base = st["base_ridership"]
        # Borough specific boost (Manhattan gets extra midday/evening office crowd)
        borough_boost = 1.15 if st["borough"] == "Manhattan" else 1.0

        # Mean hourly ridership vector
        mean_ridership = (
            base * hour_mult * dow_mult * month_mult * borough_boost
        )

        # Stochastic noise (Poisson or Gamma variance)
        noise = np.random.gamma(shape=30.0, scale=1.0 / 30.0, size=num_hours)
        simulated_hourly_total = np.maximum(5.0, mean_ridership * noise)

        # OMNY Adoption vs. MetroCard in 2024 (~65% OMNY, 35% Metrocard)
        omny_ratio = np.random.uniform(0.62, 0.68, size=num_hours)
        omny_ridership = np.round(simulated_hourly_total * omny_ratio, 1)
        metro_ridership = np.round(
            simulated_hourly_total * (1.0 - omny_ratio), 1
        )

        # Transfers (2% to 6% of entries)
        omny_transfers = np.round(
            omny_ridership * np.random.uniform(0.02, 0.06, size=num_hours), 1
        )
        metro_transfers = np.round(
            metro_ridership * np.random.uniform(0.02, 0.06, size=num_hours), 1
        )

        iso_timestamps = timestamps.strftime("%Y-%m-%dT%H:00:00.000")
        geojson_str = f'{{"type": "Point", "coordinates": [{st["lon"]}, {st["lat"]}]}}'

        # OMNY Records
        df_omny = pd.DataFrame(
            {
                "transit_timestamp": iso_timestamps,
                "transit_mode": "subway",
                "station_complex_id": st["id"],
                "station_complex": st["name"],
                "borough": st["borough"],
                "payment_method": "omny",
                "fare_class_category": "OMNY - Full Fare",
                "ridership": omny_ridership,
                "transfers": omny_transfers,
                "latitude": st["lat"],
                "longitude": st["lon"],
                "georeference": geojson_str,
            }
        )

        # MetroCard Records
        df_metro = pd.DataFrame(
            {
                "transit_timestamp": iso_timestamps,
                "transit_mode": "subway",
                "station_complex_id": st["id"],
                "station_complex": st["name"],
                "borough": st["borough"],
                "payment_method": "metrocard",
                "fare_class_category": "Metrocard - Full Fare",
                "ridership": metro_ridership,
                "transfers": metro_transfers,
                "latitude": st["lat"],
                "longitude": st["lon"],
                "georeference": geojson_str,
            }
        )

        df_station = pd.concat([df_omny, df_metro], ignore_index=True)
        all_dfs.append(df_station)

        if (i + 1) % 10 == 0 or (i + 1) == len(stations):
            logger.info(
                f"Generated synthetic time-series for {i + 1}/{len(stations)} stations..."
            )

    logger.info("Concatenating station records into unified DataFrame...")
    df_raw = pd.concat(all_dfs, ignore_index=True)

    # Sort deterministically
    df_raw = df_raw.sort_values(
        by=["station_complex_id", "transit_timestamp", "payment_method"]
    ).reset_index(drop=True)

    total_rows = len(df_raw)
    logger.info(f"Writing {total_rows:,} synthetic raw rows to {output_raw_path}...")
    df_raw.to_csv(output_raw_path, index=False)

    duration = time.time() - start_time
    logger.info("=" * 75)
    logger.info("FALLBACK SYNTHETIC DATASET GENERATION COMPLETE")
    logger.info(f"Total Rows Generated:     {total_rows:,}")
    logger.info(f"File Size on Disk:        {output_raw_path.stat().st_size / (1024 * 1024):.2f} MB")
    logger.info(f"Total Stations Included:  {len(stations)}")
    logger.info(f"Hourly Date Range:        {timestamps.min()} to {timestamps.max()}")
    logger.info(f"Total Synthetic Entries:  {df_raw['ridership'].sum():,.1f}")
    logger.info(f"Generation Time Elapsed:  {duration:.2f} seconds")
    logger.info("=" * 75)

    return total_rows, output_raw_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate realistic synthetic fallback MTA ridership dataset."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(DEFAULT_RAW_CSV_PATH),
        help="Destination raw CSV file path",
    )
    parser.add_argument(
        "--stations",
        type=int,
        default=50,
        help="Number of real NYC stations to simulate (default: 50)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Number of months in 2024 to simulate (default: 6)",
    )

    args = parser.parse_args()

    try:
        generate_mta_sample_data(
            output_raw_path=Path(args.output_path),
            num_stations=args.stations,
            months=args.months,
        )
    except Exception as exc:
        logger.critical(f"Sample data generation failed: {exc}", exc_info=True)
        sys.exit(1)
