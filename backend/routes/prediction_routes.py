"""
Machine Learning & Forecasting Routes for Sanchaar.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify, request

from ..src.models.predict import predict_demand, forecast_next_hours
from ..src.forecasting.forecast_engine import ForecastEngine
from ..database.db import record_prediction

logger = logging.getLogger("PredictionRoutes")
prediction_bp = Blueprint("predictions", __name__)

SAVED_MODELS_DIR = Path(__file__).resolve().parents[1] / "src" / "models" / "saved"
_forecast_engine = None

def get_forecast_engine():
    global _forecast_engine
    if _forecast_engine is None:
        _forecast_engine = ForecastEngine()
    return _forecast_engine


@prediction_bp.route("/predict", methods=["POST"])
def run_prediction():
    """
    Predicts passenger ridership for a specific station, calendar date, and hour.
    Payload: {"station_id": "229", "date": "2024-06-15", "hour": 8, "model": "xgboost"}
    """
    try:
        data = request.get_json() or {}
        station_id = str(data.get("station_id", "229"))
        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        hour = int(data.get("hour", 8))
        model_name = data.get("model", "xgboost")
        
        result = predict_demand(station_id, date_str, hour, model_name)
        
        # Save to database audit history
        try:
            target_dt_str = f"{date_str} {hour:02d}:00:00"
            record_prediction(
                station_id=station_id,
                station_name=result.get("station_name", f"Station {station_id}"),
                target_datetime=target_dt_str,
                model_used=model_name,
                predicted_ridership=result["predicted_ridership"],
                demand_level=result["demand_level"]
            )
        except Exception as db_err:
            logger.warning(f"Failed to record prediction in DB: {db_err}")
            
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@prediction_bp.route("/forecast", methods=["POST"])
def run_forecast():
    """
    Generates an hourly time-series forecast horizon (e.g. 12h, 24h, 48h).
    Payload: {"station_id": "229", "start_date": "2024-06-15", "start_hour": 0, "hours": 24, "model": "xgboost"}
    """
    try:
        data = request.get_json() or {}
        station_id = str(data.get("station_id", "229"))
        start_date = data.get("start_date", datetime.now().strftime("%Y-%m-%d"))
        start_hour = int(data.get("start_hour", 0))
        hours = int(data.get("hours", 24))
        model_name = data.get("model", "xgboost")
        
        forecast_res = forecast_next_hours(station_id, start_date, start_hour, hours, model_name)
        return jsonify({"success": True, "data": forecast_res}), 200
    except Exception as e:
        logger.error(f"Forecasting failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@prediction_bp.route("/models/performance", methods=["GET"])
def get_model_metrics():
    """
    Returns actual evaluation metrics (MAE, RMSE, R²) computed on genuine test partition.
    Never fabricates metrics.
    """
    try:
        metrics_path = SAVED_MODELS_DIR / "model_metrics.json"
        if not metrics_path.exists():
            return jsonify({"success": False, "error": "Model evaluation metrics file not found. Run model training first."}), 404
            
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
            
        return jsonify({"success": True, "data": metrics}), 200
    except Exception as e:
        logger.error(f"Error fetching model metrics: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@prediction_bp.route("/forecast/daily", methods=["POST"])
def run_daily_forecast():
    """Multi-day aggregated forecast."""
    try:
        data = request.get_json() or {}
        station_id = str(data.get("station_id", "229"))
        start_date = data.get("start_date", datetime.now().strftime("%Y-%m-%d"))
        num_days = int(data.get("days", 7))
        model_name = data.get("model", "xgboost")
        
        engine = get_forecast_engine()
        res = engine.daily_forecast(station_id, start_date, num_days, model_name)
        return jsonify({"success": True, "data": res}), 200
    except Exception as e:
        logger.error(f"Daily forecast failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@prediction_bp.route("/forecast/peaks", methods=["POST"])
def run_peak_forecast():
    """Peak hours forecast for a target date."""
    try:
        data = request.get_json() or {}
        station_id = str(data.get("station_id", "229"))
        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        model_name = data.get("model", "xgboost")
        
        engine = get_forecast_engine()
        res = engine.peak_hour_forecast(station_id, date_str, model_name)
        return jsonify({"success": True, "data": res}), 200
    except Exception as e:
        logger.error(f"Peak forecast failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
