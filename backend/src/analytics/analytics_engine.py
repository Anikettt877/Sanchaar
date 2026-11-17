"""
Analytics Engine Module for TRANSIT AI.

Provides comprehensive descriptive and diagnostic analytics on MTA subway ridership,
including summary statistics, temporal distributions, station rankings, borough analytics,
peak hour profiling, heatmap matrices, and recent trend forecasting data.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import pandas as pd
import numpy as np

# Configure logging for analytics engine
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AnalyticsEngine")

# Standard project directory paths
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
DEFAULT_FEATURED_DATA_PATH = os.path.join(
    PROJECT_ROOT, "backend", "data", "processed", "ridership_featured.csv"
)
DEFAULT_STATION_INFO_PATH = os.path.join(
    PROJECT_ROOT, "backend", "data", "processed", "station_info.csv"
)

# Standard borough name mapping for MTA codes
BOROUGH_NAME_MAP = {
    "M": "Manhattan",
    "BK": "Brooklyn",
    "BX": "Bronx",
    "Q": "Queens",
    "QN": "Queens",
    "SI": "Staten Island",
    "MN": "Manhattan",
    "MAN": "Manhattan",
    "BRONX": "Bronx",
    "BROOKLYN": "Brooklyn",
    "QUEENS": "Queens",
    "STATEN ISLAND": "Staten Island",
    "MANHATTAN": "Manhattan",
}

# Standard day names
DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Standard month names
MONTH_NAMES = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _safe_float(val: Any, decimals: int = 2) -> float:
    """Safely convert value to standard python float with rounding."""
    try:
        if pd.isna(val) or val is None:
            return 0.0
        return round(float(val), decimals)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(val: Any) -> int:
    """Safely convert value to standard python int."""
    try:
        if pd.isna(val) or val is None:
            return 0
        return int(round(float(val)))
    except (ValueError, TypeError):
        return 0


def _safe_str(val: Any, default: str = "") -> str:
    """Safely convert value to string without 'nan' or 'None'."""
    if pd.isna(val) or val is None:
        return default
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "null") else s


class AnalyticsEngine:
    """
    Analytics engine providing operational insights, temporal aggregations,
    demand heatmaps, and station/borough level performance metrics for MTA ridership.
    """

    def __init__(self, data_path: Optional[str] = None, station_info_path: Optional[str] = None):
        """
        Load the featured dataset and optional station reference metadata.
        Uses default paths if not explicitly provided.

        Args:
            data_path: Path to the featured ridership CSV.
            station_info_path: Path to station metadata CSV.
        """
        self.data_path = data_path or DEFAULT_FEATURED_DATA_PATH
        self.station_info_path = station_info_path or DEFAULT_STATION_INFO_PATH
        self.df: pd.DataFrame = pd.DataFrame()
        self.station_info_df: pd.DataFrame = pd.DataFrame()
        self.is_loaded: bool = False

        self._load_data()

    def reload(self, data_path: Optional[str] = None, station_info_path: Optional[str] = None) -> bool:
        """
        Reload datasets from disk or updated paths.

        Args:
            data_path: Optional new ridership CSV path.
            station_info_path: Optional new station info CSV path.

        Returns:
            bool: True if ridership data was successfully loaded, False otherwise.
        """
        if data_path:
            self.data_path = data_path
        if station_info_path:
            self.station_info_path = station_info_path
        self._load_data()
        return self.is_loaded

    def _load_data(self) -> None:
        """Load and preprocess datasets with robust error handling."""
        # 1. Attempt to load station info metadata
        try:
            if os.path.exists(self.station_info_path):
                self.station_info_df = pd.read_csv(self.station_info_path)
                self._normalize_station_info()
                logger.info("Loaded station metadata: %d stations from %s", len(self.station_info_df), self.station_info_path)
            else:
                logger.warning("Station info file not found at: %s", self.station_info_path)
                self.station_info_df = pd.DataFrame()
        except Exception as e:
            logger.error("Failed to load station info from %s: %s", self.station_info_path, str(e))
            self.station_info_df = pd.DataFrame()

        # 2. Attempt to load featured ridership dataset
        try:
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path)
                if not self.df.empty:
                    self._normalize_featured_data()
                    self.is_loaded = True
                    logger.info("Loaded ridership featured data: %d records from %s", len(self.df), self.data_path)
                else:
                    logger.warning("Featured dataset at %s is empty.", self.data_path)
                    self.is_loaded = False
            else:
                logger.warning("Featured dataset not found at: %s", self.data_path)
                self.is_loaded = False
        except Exception as e:
            logger.error("Failed to load featured dataset from %s: %s", self.data_path, str(e))
            self.df = pd.DataFrame()
            self.is_loaded = False

    def _normalize_station_info(self) -> None:
        """Normalize station reference metadata column names and borough definitions."""
        if self.station_info_df.empty:
            return

        try:
            cols = {c.lower(): c for c in self.station_info_df.columns}

            # Map Station ID
            for candidate in ["station_complex_id", "station_id", "stop_id", "complex_id"]:
                if candidate in cols:
                    self.station_info_df["station_id"] = self.station_info_df[cols[candidate]].astype(str).str.strip()
                    break

            # Map Station Name
            for candidate in ["station_name", "station_complex", "stop_name", "name"]:
                if candidate in cols:
                    self.station_info_df["station_name"] = self.station_info_df[cols[candidate]].astype(str).str.strip()
                    break

            # Map Borough
            for candidate in ["borough", "borough_name", "county"]:
                if candidate in cols:
                    b_raw = self.station_info_df[cols[candidate]].astype(str).str.strip().str.upper()
                    self.station_info_df["borough"] = b_raw.map(lambda x: BOROUGH_NAME_MAP.get(x, x.title()))
                    break

            # Map Routes / Lines
            for candidate in ["daytime_routes", "routes", "lines", "trains", "line"]:
                if candidate in cols:
                    self.station_info_df["routes"] = self.station_info_df[cols[candidate]].astype(str).str.strip()
                    break

            # Map Coordinates
            for lat_cand in ["latitude", "gtfs_latitude", "lat"]:
                if lat_cand in cols:
                    self.station_info_df["latitude"] = pd.to_numeric(self.station_info_df[cols[lat_cand]], errors="coerce")
                    break
            for lon_cand in ["longitude", "gtfs_longitude", "lon", "long"]:
                if lon_cand in cols:
                    self.station_info_df["longitude"] = pd.to_numeric(self.station_info_df[cols[lon_cand]], errors="coerce")
                    break

        except Exception as e:
            logger.error("Error normalizing station info: %s", str(e))

    def _normalize_featured_data(self) -> None:
        """Normalize columns, datetimes, station names, boroughs, and temporal features."""
        if self.df.empty:
            return

        try:
            cols = {c.lower(): c for c in self.df.columns}

            # 1. Normalize Timestamp
            ts_candidate = None
            for candidate in ["transit_timestamp", "timestamp", "datetime", "date_time", "date"]:
                if candidate in cols:
                    ts_candidate = cols[candidate]
                    break

            if ts_candidate:
                self.df["timestamp"] = pd.to_datetime(self.df[ts_candidate], errors="coerce")
            else:
                # If separate date and hour exist
                if "date" in cols and "hour" in cols:
                    self.df["timestamp"] = pd.to_datetime(
                        self.df[cols["date"]].astype(str) + " " + self.df[cols["hour"]].astype(str) + ":00:00",
                        errors="coerce"
                    )
                else:
                    self.df["timestamp"] = pd.NaT

            # 2. Normalize Ridership Target Column
            ridership_candidate = None
            for candidate in ["ridership", "hourly_ridership", "ridership_count", "entries", "transit_ridership", "entry_count"]:
                if candidate in cols:
                    ridership_candidate = cols[candidate]
                    break

            if ridership_candidate and ridership_candidate != "ridership":
                self.df["ridership"] = pd.to_numeric(self.df[ridership_candidate], errors="coerce").fillna(0.0)
            elif "ridership" in self.df.columns:
                self.df["ridership"] = pd.to_numeric(self.df["ridership"], errors="coerce").fillna(0.0)
            else:
                self.df["ridership"] = 0.0

            # 3. Normalize Station ID
            sid_candidate = None
            for candidate in ["station_complex_id", "station_id", "stop_id", "unit", "station"]:
                if candidate in cols:
                    sid_candidate = cols[candidate]
                    break

            if sid_candidate:
                self.df["station_id"] = self.df[sid_candidate].astype(str).str.strip()
            else:
                self.df["station_id"] = "UNKNOWN"

            # 4. Normalize Station Name
            sname_candidate = None
            for candidate in ["station_name", "station_complex", "stop_name"]:
                if candidate in cols:
                    sname_candidate = cols[candidate]
                    break

            if sname_candidate:
                self.df["station_name"] = self.df[sname_candidate].astype(str).str.strip()
            else:
                # Attempt lookup from station_info_df
                if not self.station_info_df.empty and "station_id" in self.station_info_df.columns and "station_name" in self.station_info_df.columns:
                    station_map = dict(zip(self.station_info_df["station_id"], self.station_info_df["station_name"]))
                    self.df["station_name"] = self.df["station_id"].map(station_map).fillna(self.df["station_id"])
                else:
                    self.df["station_name"] = self.df["station_id"]

            # 5. Normalize Borough
            borough_candidate = None
            for candidate in ["borough", "borough_name", "county"]:
                if candidate in cols:
                    borough_candidate = cols[candidate]
                    break

            if borough_candidate:
                b_raw = self.df[borough_candidate].astype(str).str.strip().str.upper()
                self.df["borough"] = b_raw.map(lambda x: BOROUGH_NAME_MAP.get(x, x.title()))
            else:
                # Lookup from station_info_df
                if not self.station_info_df.empty and "station_id" in self.station_info_df.columns and "borough" in self.station_info_df.columns:
                    borough_map = dict(zip(self.station_info_df["station_id"], self.station_info_df["borough"]))
                    self.df["borough"] = self.df["station_id"].map(borough_map).fillna("Unknown")
                else:
                    self.df["borough"] = "Unknown"

            # 6. Ensure Temporal Features: hour, day_of_week, day_name, month, year, is_weekend
            if "hour" in cols and pd.api.types.is_numeric_dtype(self.df[cols["hour"]]):
                self.df["hour"] = self.df[cols["hour"]].astype(int)
            elif pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                self.df["hour"] = self.df["timestamp"].dt.hour.fillna(0).astype(int)
            else:
                self.df["hour"] = 0

            if "day_of_week" in cols and pd.api.types.is_numeric_dtype(self.df[cols["day_of_week"]]):
                self.df["day_of_week"] = self.df[cols["day_of_week"]].astype(int)
            elif pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                self.df["day_of_week"] = self.df["timestamp"].dt.dayofweek.fillna(0).astype(int)
            else:
                self.df["day_of_week"] = 0

            # Day name
            if "day_name" in cols:
                self.df["day_name"] = self.df[cols["day_name"]].astype(str)
            else:
                self.df["day_name"] = self.df["day_of_week"].map(lambda d: DAY_NAMES[d] if 0 <= d <= 6 else "Unknown")

            # Month
            if "month" in cols and pd.api.types.is_numeric_dtype(self.df[cols["month"]]):
                self.df["month"] = self.df[cols["month"]].astype(int)
            elif pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                self.df["month"] = self.df["timestamp"].dt.month.fillna(1).astype(int)
            else:
                self.df["month"] = 1

            # Year
            if "year" in cols and pd.api.types.is_numeric_dtype(self.df[cols["year"]]):
                self.df["year"] = self.df[cols["year"]].astype(int)
            elif pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                self.df["year"] = self.df["timestamp"].dt.year.fillna(2023).astype(int)
            else:
                self.df["year"] = 2023

            # Is weekend
            if "is_weekend" in cols:
                self.df["is_weekend"] = self.df[cols["is_weekend"]].astype(int)
            else:
                self.df["is_weekend"] = self.df["day_of_week"].isin([5, 6]).astype(int)

            # 7. Merge optional route metadata from station info if available
            if not self.station_info_df.empty and "routes" in self.station_info_df.columns:
                if "routes" not in self.df.columns:
                    route_map = dict(zip(self.station_info_df["station_id"], self.station_info_df["routes"]))
                    self.df["routes"] = self.df["station_id"].map(route_map).fillna("")

        except Exception as e:
            logger.error("Error normalizing featured dataset: %s", str(e))

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Returns dashboard summary:
        - total_records, total_stations, total_boroughs
        - avg_hourly_ridership, max_hourly_ridership
        - busiest_station (name and avg ridership)
        - peak_hour (hour with highest avg ridership)
        - date_range (start, end)
        - total_ridership
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {
                    "total_records": 0,
                    "total_stations": 0,
                    "total_boroughs": 0,
                    "avg_hourly_ridership": 0.0,
                    "max_hourly_ridership": 0.0,
                    "busiest_station": {
                        "name": "N/A",
                        "station_id": "N/A",
                        "avg_ridership": 0.0,
                        "total_ridership": 0.0
                    },
                    "peak_hour": 0,
                    "date_range": {
                        "start": "N/A",
                        "end": "N/A"
                    },
                    "total_ridership": 0.0
                }

            total_records = int(len(self.df))
            total_stations = int(self.df["station_id"].nunique())
            total_boroughs = int(self.df["borough"].nunique())
            avg_hourly_ridership = _safe_float(self.df["ridership"].mean(), 2)
            max_hourly_ridership = _safe_float(self.df["ridership"].max(), 2)
            total_ridership = _safe_float(self.df["ridership"].sum(), 2)

            # Busiest station by average hourly ridership
            station_agg = self.df.groupby(["station_id", "station_name"])["ridership"].agg(["mean", "sum"]).reset_index()
            if not station_agg.empty:
                station_agg = station_agg.sort_values(by="mean", ascending=False)
                top_row = station_agg.iloc[0]
                busiest_station = {
                    "name": str(top_row["station_name"]),
                    "station_id": str(top_row["station_id"]),
                    "avg_ridership": _safe_float(top_row["mean"], 2),
                    "total_ridership": _safe_float(top_row["sum"], 2)
                }
            else:
                busiest_station = {
                    "name": "N/A",
                    "station_id": "N/A",
                    "avg_ridership": 0.0,
                    "total_ridership": 0.0
                }

            # Peak hour calculation across all stations
            hourly_means = self.df.groupby("hour")["ridership"].mean()
            peak_hour = int(hourly_means.idxmax()) if not hourly_means.empty else 0

            # Date range
            if "timestamp" in self.df.columns and pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                valid_ts = self.df["timestamp"].dropna()
                if not valid_ts.empty:
                    date_start = valid_ts.min().strftime("%Y-%m-%d %H:%M:%S")
                    date_end = valid_ts.max().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date_start, date_end = "N/A", "N/A"
            else:
                date_start, date_end = "N/A", "N/A"

            return {
                "total_records": total_records,
                "total_stations": total_stations,
                "total_boroughs": total_boroughs,
                "avg_hourly_ridership": avg_hourly_ridership,
                "max_hourly_ridership": max_hourly_ridership,
                "busiest_station": busiest_station,
                "peak_hour": peak_hour,
                "date_range": {
                    "start": date_start,
                    "end": date_end
                },
                "total_ridership": total_ridership
            }

        except Exception as e:
            logger.error("Error computing summary stats: %s", str(e))
            return {
                "total_records": 0,
                "total_stations": 0,
                "total_boroughs": 0,
                "avg_hourly_ridership": 0.0,
                "max_hourly_ridership": 0.0,
                "busiest_station": {"name": "Error", "avg_ridership": 0.0},
                "peak_hour": 0,
                "date_range": {"start": "Error", "end": "Error"},
                "total_ridership": 0.0
            }

    def get_hourly_distribution(self) -> List[Dict[str, Any]]:
        """
        Average ridership by hour of day. Returns list of 24 entries (hours 0 to 23).
        """
        try:
            if not self.is_loaded or self.df.empty:
                return [
                    {
                        "hour": h,
                        "hour_label": f"{h:02d}:00",
                        "formatted_hour": f"{12 if h % 12 == 0 else h % 12} {'AM' if h < 12 else 'PM'}",
                        "avg_ridership": 0.0,
                        "total_ridership": 0.0,
                        "record_count": 0
                    }
                    for h in range(24)
                ]

            hourly_stats = (
                self.df.groupby("hour")["ridership"]
                .agg(["mean", "sum", "count"])
                .reindex(range(24), fill_value=0)
            )

            results = []
            for h in range(24):
                avg_val = _safe_float(hourly_stats.loc[h, "mean"], 2)
                sum_val = _safe_float(hourly_stats.loc[h, "sum"], 2)
                cnt_val = _safe_int(hourly_stats.loc[h, "count"])
                formatted_hour = f"{12 if h % 12 == 0 else h % 12} {'AM' if h < 12 else 'PM'}"

                results.append({
                    "hour": h,
                    "hour_label": f"{h:02d}:00",
                    "formatted_hour": formatted_hour,
                    "avg_ridership": avg_val,
                    "total_ridership": sum_val,
                    "record_count": cnt_val
                })

            return results

        except Exception as e:
            logger.error("Error computing hourly distribution: %s", str(e))
            return []

    def get_daily_distribution(self) -> List[Dict[str, Any]]:
        """
        Average ridership by day of week. Returns list of 7 entries (Monday through Sunday).
        """
        try:
            if not self.is_loaded or self.df.empty:
                return [
                    {
                        "day_of_week": d,
                        "day_name": DAY_NAMES[d],
                        "is_weekend": d >= 5,
                        "avg_ridership": 0.0,
                        "total_ridership": 0.0,
                        "record_count": 0
                    }
                    for d in range(7)
                ]

            daily_stats = (
                self.df.groupby("day_of_week")["ridership"]
                .agg(["mean", "sum", "count"])
                .reindex(range(7), fill_value=0)
            )

            results = []
            for d in range(7):
                avg_val = _safe_float(daily_stats.loc[d, "mean"], 2)
                sum_val = _safe_float(daily_stats.loc[d, "sum"], 2)
                cnt_val = _safe_int(daily_stats.loc[d, "count"])

                results.append({
                    "day_of_week": d,
                    "day_name": DAY_NAMES[d],
                    "is_weekend": bool(d >= 5),
                    "avg_ridership": avg_val,
                    "total_ridership": sum_val,
                    "record_count": cnt_val
                })

            return results

        except Exception as e:
            logger.error("Error computing daily distribution: %s", str(e))
            return []

    def get_monthly_trend(self) -> List[Dict[str, Any]]:
        """
        Total ridership by month. Returns list of chronological month entries.
        """
        try:
            if not self.is_loaded or self.df.empty:
                return []

            monthly_stats = (
                self.df.groupby(["year", "month"])["ridership"]
                .agg(["sum", "mean", "count"])
                .reset_index()
                .sort_values(by=["year", "month"])
            )

            results = []
            for _, row in monthly_stats.iterrows():
                y = int(row["year"])
                m = int(row["month"])
                m_name = MONTH_NAMES[m] if 1 <= m <= 12 else f"Month {m}"

                results.append({
                    "year": y,
                    "month": m,
                    "month_name": m_name,
                    "year_month": f"{y}-{m:02d}",
                    "total_ridership": _safe_float(row["sum"], 2),
                    "avg_hourly_ridership": _safe_float(row["mean"], 2),
                    "record_count": _safe_int(row["count"])
                })

            return results

        except Exception as e:
            logger.error("Error computing monthly trend: %s", str(e))
            return []

    def get_station_rankings(self, top_n: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Top N and bottom N stations by total ridership.
        Returns: {"top_stations": [...], "bottom_stations": [...]}
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {"top_stations": [], "bottom_stations": []}

            station_agg = (
                self.df.groupby(["station_id", "station_name", "borough"])["ridership"]
                .agg(["sum", "mean", "count"])
                .reset_index()
            )

            # Sort descending for top stations
            top_sorted = station_agg.sort_values(by="sum", ascending=False).reset_index(drop=True)
            top_stations = []
            for rank, row in enumerate(top_sorted.head(top_n).itertuples(), start=1):
                top_stations.append({
                    "rank": rank,
                    "station_id": str(row.station_id),
                    "station_name": str(row.station_name),
                    "borough": str(row.borough),
                    "total_ridership": _safe_float(row.sum, 2),
                    "avg_hourly_ridership": _safe_float(row.mean, 2),
                    "record_count": _safe_int(row.count)
                })

            # Sort ascending for bottom stations (lowest non-zero or lowest ridership)
            bottom_sorted = station_agg.sort_values(by="sum", ascending=True).reset_index(drop=True)
            total_stations_count = len(station_agg)
            bottom_stations = []
            for idx, row in enumerate(bottom_sorted.head(top_n).itertuples(), start=0):
                bottom_stations.append({
                    "rank": total_stations_count - idx,
                    "station_id": str(row.station_id),
                    "station_name": str(row.station_name),
                    "borough": str(row.borough),
                    "total_ridership": _safe_float(row.sum, 2),
                    "avg_hourly_ridership": _safe_float(row.mean, 2),
                    "record_count": _safe_int(row.count)
                })

            return {
                "top_stations": top_stations,
                "bottom_stations": bottom_stations
            }

        except Exception as e:
            logger.error("Error computing station rankings: %s", str(e))
            return {"top_stations": [], "bottom_stations": []}

    def get_borough_stats(self) -> List[Dict[str, Any]]:
        """
        Ridership statistics by borough.
        Returns list of borough entries with total, avg, station_count.
        """
        try:
            if not self.is_loaded or self.df.empty:
                return []

            total_system_ridership = float(self.df["ridership"].sum())

            borough_agg = (
                self.df.groupby("borough")
                .agg(
                    total_ridership=("ridership", "sum"),
                    avg_hourly_ridership=("ridership", "mean"),
                    station_count=("station_id", "nunique"),
                    record_count=("ridership", "count")
                )
                .reset_index()
                .sort_values(by="total_ridership", ascending=False)
            )

            results = []
            for _, row in borough_agg.iterrows():
                tot = _safe_float(row["total_ridership"], 2)
                share = (
                    round((tot / total_system_ridership * 100), 2)
                    if total_system_ridership > 0
                    else 0.0
                )

                results.append({
                    "borough": str(row["borough"]),
                    "total_ridership": tot,
                    "avg_hourly_ridership": _safe_float(row["avg_hourly_ridership"], 2),
                    "station_count": _safe_int(row["station_count"]),
                    "record_count": _safe_int(row["record_count"]),
                    "share_percentage": share
                })

            return results

        except Exception as e:
            logger.error("Error computing borough stats: %s", str(e))
            return []

    def get_peak_analysis(self) -> Dict[str, Any]:
        """
        Detailed peak hour analysis.
        Returns: {
            "morning_peak": {"hours": "7-10 AM", "avg_ridership": ...},
            "evening_peak": {"hours": "4-7 PM", "avg_ridership": ...},
            "off_peak": {"hours": "...", "avg_ridership": ...},
            "lowest_demand_hour": ...,
            "highest_demand_hour": ...,
            "hourly_data": [...]
        }
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {
                    "morning_peak": {"hours": "7-10 AM", "avg_ridership": 0.0},
                    "evening_peak": {"hours": "4-7 PM", "avg_ridership": 0.0},
                    "off_peak": {"hours": "10 PM - 7 AM, 10 AM - 4 PM, 7 PM - 10 PM", "avg_ridership": 0.0},
                    "lowest_demand_hour": 0,
                    "highest_demand_hour": 0,
                    "hourly_data": []
                }

            # Morning peak: 7 AM to 10 AM (hours 7, 8, 9)
            morning_mask = self.df["hour"].isin([7, 8, 9])
            # Evening peak: 4 PM to 7 PM (hours 16, 17, 18)
            evening_mask = self.df["hour"].isin([16, 17, 18])
            # Off-peak: remaining hours
            off_peak_mask = ~(morning_mask | evening_mask)

            morning_avg = _safe_float(self.df.loc[morning_mask, "ridership"].mean(), 2) if morning_mask.any() else 0.0
            evening_avg = _safe_float(self.df.loc[evening_mask, "ridership"].mean(), 2) if evening_mask.any() else 0.0
            off_peak_avg = _safe_float(self.df.loc[off_peak_mask, "ridership"].mean(), 2) if off_peak_mask.any() else 0.0

            hourly_means = (
                self.df.groupby("hour")["ridership"]
                .mean()
                .reindex(range(24), fill_value=0.0)
            )

            lowest_hour = int(hourly_means.idxmin())
            highest_hour = int(hourly_means.idxmax())

            hourly_data = self.get_hourly_distribution()

            return {
                "morning_peak": {
                    "hours": "7-10 AM",
                    "avg_ridership": morning_avg,
                    "total_ridership": _safe_float(self.df.loc[morning_mask, "ridership"].sum(), 2) if morning_mask.any() else 0.0
                },
                "evening_peak": {
                    "hours": "4-7 PM",
                    "avg_ridership": evening_avg,
                    "total_ridership": _safe_float(self.df.loc[evening_mask, "ridership"].sum(), 2) if evening_mask.any() else 0.0
                },
                "off_peak": {
                    "hours": "10 PM - 7 AM, 10 AM - 4 PM, 7 PM - 10 PM",
                    "avg_ridership": off_peak_avg,
                    "total_ridership": _safe_float(self.df.loc[off_peak_mask, "ridership"].sum(), 2) if off_peak_mask.any() else 0.0
                },
                "lowest_demand_hour": lowest_hour,
                "highest_demand_hour": highest_hour,
                "hourly_data": hourly_data
            }

        except Exception as e:
            logger.error("Error computing peak analysis: %s", str(e))
            return {
                "morning_peak": {"hours": "7-10 AM", "avg_ridership": 0.0},
                "evening_peak": {"hours": "4-7 PM", "avg_ridership": 0.0},
                "off_peak": {"hours": "N/A", "avg_ridership": 0.0},
                "lowest_demand_hour": 0,
                "highest_demand_hour": 0,
                "hourly_data": []
            }

    def get_weekday_weekend_comparison(self) -> Dict[str, Any]:
        """
        Compare weekday vs weekend patterns.
        Returns: {
            "weekday_avg": ..., "weekend_avg": ..., "difference_pct": ...,
            "weekday_hourly": [...], "weekend_hourly": [...],
            "weekday_daily": [...], "weekend_daily": [...]
        }
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {
                    "weekday_avg": 0.0,
                    "weekend_avg": 0.0,
                    "difference_pct": 0.0,
                    "weekday_hourly": [],
                    "weekend_hourly": [],
                    "weekday_daily": [],
                    "weekend_daily": []
                }

            weekday_mask = self.df["day_of_week"] < 5
            weekend_mask = self.df["day_of_week"] >= 5

            weekday_df = self.df[weekday_mask]
            weekend_df = self.df[weekend_mask]

            weekday_avg = _safe_float(weekday_df["ridership"].mean(), 2) if not weekday_df.empty else 0.0
            weekend_avg = _safe_float(weekend_df["ridership"].mean(), 2) if not weekend_df.empty else 0.0

            difference_pct = (
                round(((weekend_avg - weekday_avg) / weekday_avg) * 100, 2)
                if weekday_avg > 0
                else 0.0
            )

            # Weekday hourly profile (0 to 23)
            wd_hourly_agg = (
                weekday_df.groupby("hour")["ridership"]
                .agg(["mean", "sum", "count"])
                .reindex(range(24), fill_value=0)
            ) if not weekday_df.empty else pd.DataFrame(0, index=range(24), columns=["mean", "sum", "count"])

            weekday_hourly = []
            for h in range(24):
                weekday_hourly.append({
                    "hour": h,
                    "hour_label": f"{h:02d}:00",
                    "avg_ridership": _safe_float(wd_hourly_agg.loc[h, "mean"], 2),
                    "total_ridership": _safe_float(wd_hourly_agg.loc[h, "sum"], 2),
                    "record_count": _safe_int(wd_hourly_agg.loc[h, "count"])
                })

            # Weekend hourly profile (0 to 23)
            we_hourly_agg = (
                weekend_df.groupby("hour")["ridership"]
                .agg(["mean", "sum", "count"])
                .reindex(range(24), fill_value=0)
            ) if not weekend_df.empty else pd.DataFrame(0, index=range(24), columns=["mean", "sum", "count"])

            weekend_hourly = []
            for h in range(24):
                weekend_hourly.append({
                    "hour": h,
                    "hour_label": f"{h:02d}:00",
                    "avg_ridership": _safe_float(we_hourly_agg.loc[h, "mean"], 2),
                    "total_ridership": _safe_float(we_hourly_agg.loc[h, "sum"], 2),
                    "record_count": _safe_int(we_hourly_agg.loc[h, "count"])
                })

            # Daily breakdown: Weekday (Monday=0 to Friday=4)
            daily_all = (
                self.df.groupby("day_of_week")["ridership"]
                .agg(["mean", "sum", "count"])
                .reindex(range(7), fill_value=0)
            )

            weekday_daily = []
            for d in range(5):
                weekday_daily.append({
                    "day_of_week": d,
                    "day_name": DAY_NAMES[d],
                    "avg_ridership": _safe_float(daily_all.loc[d, "mean"], 2),
                    "total_ridership": _safe_float(daily_all.loc[d, "sum"], 2),
                    "record_count": _safe_int(daily_all.loc[d, "count"])
                })

            # Daily breakdown: Weekend (Saturday=5, Sunday=6)
            weekend_daily = []
            for d in range(5, 7):
                weekend_daily.append({
                    "day_of_week": d,
                    "day_name": DAY_NAMES[d],
                    "avg_ridership": _safe_float(daily_all.loc[d, "mean"], 2),
                    "total_ridership": _safe_float(daily_all.loc[d, "sum"], 2),
                    "record_count": _safe_int(daily_all.loc[d, "count"])
                })

            return {
                "weekday_avg": weekday_avg,
                "weekend_avg": weekend_avg,
                "difference_pct": difference_pct,
                "weekday_hourly": weekday_hourly,
                "weekend_hourly": weekend_hourly,
                "weekday_daily": weekday_daily,
                "weekend_daily": weekend_daily
            }

        except Exception as e:
            logger.error("Error computing weekday vs weekend comparison: %s", str(e))
            return {
                "weekday_avg": 0.0,
                "weekend_avg": 0.0,
                "difference_pct": 0.0,
                "weekday_hourly": [],
                "weekend_hourly": [],
                "weekday_daily": [],
                "weekend_daily": []
            }

    def get_station_details(self, station_id: Union[str, int]) -> Dict[str, Any]:
        """
        Detailed analytics for a specific station by Station ID or Station Name.
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {
                    "error": "Dataset is not loaded",
                    "station_id": str(station_id)
                }

            sid_str = str(station_id).strip()
            # Match by ID or Name
            st_mask = self.df["station_id"].astype(str) == sid_str
            if not st_mask.any():
                st_mask = self.df["station_name"].astype(str).str.lower() == sid_str.lower()

            if not st_mask.any():
                return {
                    "error": f"Station '{station_id}' not found in dataset",
                    "station_id": str(station_id)
                }

            station_df = self.df[st_mask]

            st_id = str(station_df["station_id"].iloc[0])
            st_name = str(station_df["station_name"].iloc[0])
            borough = str(station_df["borough"].iloc[0])

            total_ridership = _safe_float(station_df["ridership"].sum(), 2)
            avg_hourly_ridership = _safe_float(station_df["ridership"].mean(), 2)
            max_hourly_ridership = _safe_float(station_df["ridership"].max(), 2)
            min_hourly_ridership = _safe_float(station_df["ridership"].min(), 2)
            total_records = int(len(station_df))

            # Peak hour
            hourly_means = station_df.groupby("hour")["ridership"].mean().reindex(range(24), fill_value=0)
            peak_hour = int(hourly_means.idxmax())

            # Busiest day
            daily_means = station_df.groupby("day_of_week")["ridership"].mean().reindex(range(7), fill_value=0)
            busiest_day_idx = int(daily_means.idxmax())
            busiest_day = DAY_NAMES[busiest_day_idx]

            # Weekday vs Weekend average
            wd_mask = station_df["day_of_week"] < 5
            we_mask = station_df["day_of_week"] >= 5
            weekday_avg = _safe_float(station_df.loc[wd_mask, "ridership"].mean(), 2) if wd_mask.any() else 0.0
            weekend_avg = _safe_float(station_df.loc[we_mask, "ridership"].mean(), 2) if we_mask.any() else 0.0

            # 24-hour distribution
            hourly_distribution = []
            for h in range(24):
                hourly_distribution.append({
                    "hour": h,
                    "hour_label": f"{h:02d}:00",
                    "avg_ridership": _safe_float(hourly_means.loc[h], 2)
                })

            # 7-day distribution
            daily_distribution = []
            for d in range(7):
                daily_distribution.append({
                    "day_of_week": d,
                    "day_name": DAY_NAMES[d],
                    "avg_ridership": _safe_float(daily_means.loc[d], 2)
                })

            # Calculate station rank within the entire system
            station_totals = self.df.groupby("station_id")["ridership"].sum().sort_values(ascending=False)
            try:
                rank = int(station_totals.index.get_loc(st_id)) + 1
            except KeyError:
                rank = 0

            # Station metadata lookup from station_info_df
            routes: List[str] = []
            latitude: Optional[float] = None
            longitude: Optional[float] = None

            if not self.station_info_df.empty:
                info_match = self.station_info_df[self.station_info_df["station_id"] == st_id]
                if not info_match.empty:
                    info_row = info_match.iloc[0]
                    if "routes" in info_match.columns and pd.notna(info_row["routes"]):
                        raw_routes = str(info_row["routes"])
                        routes = [r.strip() for r in raw_routes.replace(",", " ").split() if r.strip()]
                    if "latitude" in info_match.columns and pd.notna(info_row["latitude"]):
                        latitude = _safe_float(info_row["latitude"], 6)
                    if "longitude" in info_match.columns and pd.notna(info_row["longitude"]):
                        longitude = _safe_float(info_row["longitude"], 6)

            # If routes still empty, check df
            if not routes and "routes" in station_df.columns:
                val = station_df["routes"].dropna().iloc[0] if not station_df["routes"].dropna().empty else ""
                if val:
                    routes = [r.strip() for r in str(val).replace(",", " ").split() if r.strip()]

            return {
                "station_id": st_id,
                "station_name": st_name,
                "borough": borough,
                "rank": rank,
                "total_stations": int(self.df["station_id"].nunique()),
                "total_ridership": total_ridership,
                "avg_hourly_ridership": avg_hourly_ridership,
                "max_hourly_ridership": max_hourly_ridership,
                "min_hourly_ridership": min_hourly_ridership,
                "total_records": total_records,
                "peak_hour": peak_hour,
                "busiest_day": busiest_day,
                "weekday_avg": weekday_avg,
                "weekend_avg": weekend_avg,
                "routes": routes,
                "latitude": latitude,
                "longitude": longitude,
                "hourly_distribution": hourly_distribution,
                "daily_distribution": daily_distribution
            }

        except Exception as e:
            logger.error("Error computing station details for %s: %s", str(station_id), str(e))
            return {
                "error": str(e),
                "station_id": str(station_id)
            }

    def get_demand_heatmap_data(self) -> Dict[str, Any]:
        """
        Returns data for a heatmap: hour x day_of_week avg ridership matrix.
        Output contains matrix, days, hours, and flat cell coordinates.
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {
                    "days": DAY_NAMES,
                    "hours": list(range(24)),
                    "matrix": [[0.0 for _ in range(24)] for _ in range(7)],
                    "heatmap_points": []
                }

            heatmap_pivot = (
                self.df.groupby(["day_of_week", "hour"])["ridership"]
                .mean()
                .unstack(level="hour")
                .reindex(index=range(7), columns=range(24), fill_value=0.0)
            )

            matrix: List[List[float]] = []
            heatmap_points: List[Dict[str, Any]] = []

            for d in range(7):
                row_vals: List[float] = []
                day_name = DAY_NAMES[d]
                for h in range(24):
                    val = _safe_float(heatmap_pivot.loc[d, h], 2)
                    row_vals.append(val)
                    heatmap_points.append({
                        "day_of_week": d,
                        "day_name": day_name,
                        "hour": h,
                        "hour_label": f"{h:02d}:00",
                        "avg_ridership": val
                    })
                matrix.append(row_vals)

            return {
                "days": DAY_NAMES,
                "hours": list(range(24)),
                "matrix": matrix,
                "heatmap_points": heatmap_points
            }

        except Exception as e:
            logger.error("Error computing demand heatmap data: %s", str(e))
            return {
                "days": DAY_NAMES,
                "hours": list(range(24)),
                "matrix": [[0.0 for _ in range(24)] for _ in range(7)],
                "heatmap_points": []
            }

    def get_route_analytics(self) -> Dict[str, Any]:
        """
        Since the dataset doesn't have explicit route info, analyze by borough/station groups.
        Returns borough-based route analytics, transit corridors, and route breakdown if available.
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {
                    "borough_corridors": [],
                    "route_summaries": [],
                    "summary": {
                        "total_boroughs_analyzed": 0,
                        "total_system_ridership": 0.0,
                        "busiest_borough": "N/A"
                    }
                }

            borough_corridors = []
            for borough_name, b_df in self.df.groupby("borough"):
                b_total = _safe_float(b_df["ridership"].sum(), 2)
                b_avg = _safe_float(b_df["ridership"].mean(), 2)
                b_stations = int(b_df["station_id"].nunique())

                # Peak hour in this borough
                b_hourly = b_df.groupby("hour")["ridership"].mean().reindex(range(24), fill_value=0)
                b_peak_hour = int(b_hourly.idxmax())

                # Weekday vs Weekend
                b_wd_mask = b_df["day_of_week"] < 5
                b_we_mask = b_df["day_of_week"] >= 5
                b_wd_avg = _safe_float(b_df.loc[b_wd_mask, "ridership"].mean(), 2) if b_wd_mask.any() else 0.0
                b_we_avg = _safe_float(b_df.loc[b_we_mask, "ridership"].mean(), 2) if b_we_mask.any() else 0.0

                # Morning and Evening Peak averages
                b_morn = b_df["hour"].isin([7, 8, 9])
                b_eve = b_df["hour"].isin([16, 17, 18])
                morn_avg = _safe_float(b_df.loc[b_morn, "ridership"].mean(), 2) if b_morn.any() else 0.0
                eve_avg = _safe_float(b_df.loc[b_eve, "ridership"].mean(), 2) if b_eve.any() else 0.0

                # Top stations in this borough
                top_b_stations = (
                    b_df.groupby(["station_id", "station_name"])["ridership"]
                    .agg(["sum", "mean"])
                    .reset_index()
                    .sort_values(by="sum", ascending=False)
                    .head(5)
                )

                top_station_list = []
                for _, s_row in top_b_stations.iterrows():
                    top_station_list.append({
                        "station_id": str(s_row["station_id"]),
                        "station_name": str(s_row["station_name"]),
                        "total_ridership": _safe_float(s_row["sum"], 2),
                        "avg_hourly_ridership": _safe_float(s_row["mean"], 2)
                    })

                borough_corridors.append({
                    "borough": str(borough_name),
                    "total_ridership": b_total,
                    "avg_hourly_ridership": b_avg,
                    "station_count": b_stations,
                    "peak_hour": b_peak_hour,
                    "morning_peak_avg": morn_avg,
                    "evening_peak_avg": eve_avg,
                    "weekday_avg": b_wd_avg,
                    "weekend_avg": b_we_avg,
                    "top_stations": top_station_list
                })

            # Sort corridors by total ridership descending
            borough_corridors.sort(key=lambda x: x["total_ridership"], reverse=True)

            # Analyze subway route/line indicators if available in dataframe or station_info
            route_summaries = []
            has_routes = "routes" in self.df.columns and not self.df["routes"].dropna().empty

            if has_routes:
                try:
                    # Explode comma/space delimited routes
                    exploded_df = self.df.copy()
                    exploded_df["route_list"] = (
                        exploded_df["routes"]
                        .astype(str)
                        .str.replace(",", " ")
                        .str.split()
                    )
                    exploded_df = exploded_df.explode("route_list")
                    exploded_df = exploded_df[exploded_df["route_list"].notna() & (exploded_df["route_list"] != "")]

                    route_agg = (
                        exploded_df.groupby("route_list")
                        .agg(
                            total_ridership=("ridership", "sum"),
                            avg_hourly_ridership=("ridership", "mean"),
                            station_count=("station_id", "nunique"),
                            boroughs_served=("borough", lambda b: sorted(list(set(b.dropna()))))
                        )
                        .reset_index()
                        .sort_values(by="total_ridership", ascending=False)
                    )

                    for _, r_row in route_agg.iterrows():
                        route_summaries.append({
                            "route": str(r_row["route_list"]).upper(),
                            "total_ridership": _safe_float(r_row["total_ridership"], 2),
                            "avg_hourly_ridership": _safe_float(r_row["avg_hourly_ridership"], 2),
                            "station_count": int(r_row["station_count"]),
                            "boroughs_served": list(r_row["boroughs_served"])
                        })
                except Exception as route_err:
                    logger.warning("Could not explode routes: %s", str(route_err))

            busiest_b = borough_corridors[0]["borough"] if borough_corridors else "N/A"
            total_ridership_all = _safe_float(self.df["ridership"].sum(), 2)

            return {
                "borough_corridors": borough_corridors,
                "route_summaries": route_summaries,
                "summary": {
                    "total_boroughs_analyzed": len(borough_corridors),
                    "total_system_ridership": total_ridership_all,
                    "busiest_borough": busiest_b,
                    "has_route_breakdown": bool(len(route_summaries) > 0)
                }
            }

        except Exception as e:
            logger.error("Error computing route analytics: %s", str(e))
            return {
                "borough_corridors": [],
                "route_summaries": [],
                "summary": {
                    "total_boroughs_analyzed": 0,
                    "total_system_ridership": 0.0,
                    "busiest_borough": "Error"
                }
            }

    def get_recent_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Recent ridership trends for the last N days available in the dataset.
        Aggregates daily ridership, calculates 7-day moving average and station activity.
        """
        try:
            if not self.is_loaded or self.df.empty:
                return []

            if "timestamp" not in self.df.columns or not pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                return []

            valid_dates = self.df["timestamp"].dropna()
            if valid_dates.empty:
                return []

            max_date = valid_dates.max()
            start_date = max_date - pd.Timedelta(days=days)

            recent_df = self.df[self.df["timestamp"] >= start_date].copy()
            if recent_df.empty:
                recent_df = self.df.copy()

            recent_df["date"] = recent_df["timestamp"].dt.strftime("%Y-%m-%d")

            daily_agg = (
                recent_df.groupby("date")
                .agg(
                    total_ridership=("ridership", "sum"),
                    avg_hourly_ridership=("ridership", "mean"),
                    station_count=("station_id", "nunique"),
                    record_count=("ridership", "count")
                )
                .reset_index()
                .sort_values(by="date")
            )

            # 7-day rolling average of daily total ridership
            daily_agg["rolling_7d_avg"] = (
                daily_agg["total_ridership"]
                .rolling(window=7, min_periods=1)
                .mean()
                .round(2)
            )

            results = []
            for _, row in daily_agg.iterrows():
                d_str = str(row["date"])
                try:
                    dt_obj = datetime.strptime(d_str, "%Y-%m-%d")
                    day_name = DAY_NAMES[dt_obj.weekday()]
                    is_weekend = dt_obj.weekday() >= 5
                except Exception:
                    day_name = "Unknown"
                    is_weekend = False

                results.append({
                    "date": d_str,
                    "day_name": day_name,
                    "is_weekend": is_weekend,
                    "total_ridership": _safe_float(row["total_ridership"], 2),
                    "avg_hourly_ridership": _safe_float(row["avg_hourly_ridership"], 2),
                    "rolling_7d_avg": _safe_float(row["rolling_7d_avg"], 2),
                    "station_count": _safe_int(row["station_count"]),
                    "record_count": _safe_int(row["record_count"])
                })

            return results

        except Exception as e:
            logger.error("Error computing recent trends: %s", str(e))
            return []

    def get_dataset_info(self) -> Dict[str, Any]:
        """
        Return dataset metadata: shape, columns, dtypes, missing values, date range, memory usage.
        """
        try:
            if not self.is_loaded or self.df.empty:
                return {
                    "shape": [0, 0],
                    "columns": [],
                    "dtypes": {},
                    "missing_values": {},
                    "missing_percentages": {},
                    "date_range": {
                        "start": None,
                        "end": None,
                        "total_days": 0
                    },
                    "memory_usage_bytes": 0,
                    "memory_usage_mb": 0.0,
                    "is_loaded": False,
                    "file_path": str(self.data_path),
                    "station_info_loaded": not self.station_info_df.empty,
                    "station_info_path": str(self.station_info_path)
                }

            shape = [int(self.df.shape[0]), int(self.df.shape[1])]
            columns = [str(c) for c in self.df.columns]
            dtypes = {str(col): str(dtype) for col, dtype in self.df.dtypes.items()}
            missing_values = {str(col): int(self.df[col].isna().sum()) for col in self.df.columns}
            missing_percentages = {
                str(col): round(float(self.df[col].isna().mean() * 100), 2)
                for col in self.df.columns
            }

            date_start, date_end, total_days = None, None, 0
            if "timestamp" in self.df.columns and pd.api.types.is_datetime64_any_dtype(self.df["timestamp"]):
                valid_ts = self.df["timestamp"].dropna()
                if not valid_ts.empty:
                    d_min = valid_ts.min()
                    d_max = valid_ts.max()
                    date_start = d_min.strftime("%Y-%m-%d %H:%M:%S")
                    date_end = d_max.strftime("%Y-%m-%d %H:%M:%S")
                    total_days = max(1, (d_max - d_min).days + 1)

            mem_bytes = int(self.df.memory_usage(deep=True).sum())
            mem_mb = round(mem_bytes / (1024 * 1024), 2)

            return {
                "shape": shape,
                "columns": columns,
                "dtypes": dtypes,
                "missing_values": missing_values,
                "missing_percentages": missing_percentages,
                "date_range": {
                    "start": date_start,
                    "end": date_end,
                    "total_days": total_days
                },
                "memory_usage_bytes": mem_bytes,
                "memory_usage_mb": mem_mb,
                "is_loaded": True,
                "file_path": str(self.data_path),
                "station_info_loaded": not self.station_info_df.empty,
                "station_info_path": str(self.station_info_path)
            }

        except Exception as e:
            logger.error("Error retrieving dataset info: %s", str(e))
            return {
                "shape": [0, 0],
                "columns": [],
                "dtypes": {},
                "missing_values": {},
                "memory_usage_bytes": 0,
                "memory_usage_mb": 0.0,
                "is_loaded": False,
                "error": str(e)
            }
