"""
Dataset Management & Inspection Routes for Sanchaar.
"""

import logging
from flask import Blueprint, jsonify, request

from ..src.analytics.analytics_engine import AnalyticsEngine
from ..src.models.predict import load_station_metadata

logger = logging.getLogger("DataRoutes")
data_bp = Blueprint("datasets", __name__)

_analytics_engine = None

def get_engine():
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


@data_bp.route("", methods=["GET"])
def get_dataset_info():
    """Returns dataset summary metrics, column schema, and ingestion metadata."""
    try:
        info = get_engine().get_dataset_info()
        return jsonify({"success": True, "data": info}), 200
    except Exception as e:
        logger.error(f"Error getting dataset info: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@data_bp.route("/preview", methods=["GET"])
def get_preview():
    """Returns first 50 records of engineered ridership dataset."""
    try:
        engine = get_engine()
        df = engine.df
        if df is None:
            return jsonify({"success": False, "error": "Dataset not loaded"}), 404
            
        limit = min(100, int(request.args.get("limit", 50)))
        sample_df = df.head(limit).copy()
        
        # Format datetime column to string for JSON serialization
        if "transit_timestamp" in sample_df.columns:
            sample_df["transit_timestamp"] = sample_df["transit_timestamp"].astype(str)
            
        records = sample_df.to_dict(orient="records")
        return jsonify({
            "success": True,
            "total_available": len(df),
            "returned_count": len(records),
            "columns": list(df.columns),
            "data": records
        }), 200
    except Exception as e:
        logger.error(f"Error previewing dataset: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@data_bp.route("/stations", methods=["GET"])
def get_stations():
    """Returns unique station names, boroughs, IDs, and geographic coordinates."""
    try:
        st_df = load_station_metadata()
        stations = st_df.to_dict(orient="records")
        return jsonify({"success": True, "count": len(stations), "data": stations}), 200
    except Exception as e:
        logger.error(f"Error listing stations: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
