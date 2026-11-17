"""
Inference & Prediction Service Module for TRANSIT AI.

Loads trained Machine Learning (Random Forest, XGBoost) and Deep Learning (LSTM) models,
constructs runtime feature vectors for any target station, date, and hour,
and computes expected passenger ridership and demand level classifications.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd
import joblib

import torch
import torch.nn as nn

logger = logging.getLogger("PredictService")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAVED_MODELS_DIR = PROJECT_ROOT / "backend" / "src" / "models" / "saved"
PROCESSED_DATA_DIR = PROJECT_ROOT / "backend" / "data" / "processed"
FEATURED_DATA_PATH = PROCESSED_DATA_DIR / "ridership_featured.csv"
STATION_INFO_PATH = PROCESSED_DATA_DIR / "station_info.csv"


class PyTorchLSTM(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super(PyTorchLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc1 = nn.Linear(hidden_dim, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(32, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        last_step = out[:, -1, :]
        h = self.relu(self.fc1(last_step))
        h = self.dropout(h)
        pred = self.fc2(h)
        return pred.squeeze(-1)


# Global model cache
_MODELS_CACHE = {}
_CONFIG_CACHE = None
_DATA_CACHE = None
_STATION_CACHE = None


def load_model_config() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        cfg_path = SAVED_MODELS_DIR / "model_config.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Model config not found at {cfg_path}. Train models first.")
        with open(cfg_path, "r") as f:
            _CONFIG_CACHE = json.load(f)
    return _CONFIG_CACHE


def load_models() -> Dict[str, Any]:
    global _MODELS_CACHE
    if not _MODELS_CACHE:
        config = load_model_config()
        
        # Load RF
        rf_path = SAVED_MODELS_DIR / "random_forest_model.joblib"
        if rf_path.exists():
            _MODELS_CACHE["random_forest"] = joblib.load(rf_path)
            
        # Load XGBoost
        xgb_path = SAVED_MODELS_DIR / "xgboost_model.joblib"
        if xgb_path.exists():
            _MODELS_CACHE["xgboost"] = joblib.load(xgb_path)
            
        # Load LSTM
        lstm_pt_path = SAVED_MODELS_DIR / "lstm_model.pt"
        if lstm_pt_path.exists():
            input_dim = config["num_features"]
            model = PyTorchLSTM(input_dim=input_dim, hidden_dim=64, num_layers=2, dropout=0.2)
            model.load_state_dict(torch.load(lstm_pt_path, map_location=torch.device("cpu")))
            model.eval()
            _MODELS_CACHE["lstm"] = model
            
            # Scalers
            scaler_x_path = SAVED_MODELS_DIR / "lstm_scaler_x.joblib"
            scaler_y_path = SAVED_MODELS_DIR / "lstm_scaler_y.joblib"
            if scaler_x_path.exists() and scaler_y_path.exists():
                _MODELS_CACHE["lstm_scaler_x"] = joblib.load(scaler_x_path)
                _MODELS_CACHE["lstm_scaler_y"] = joblib.load(scaler_y_path)
                
    return _MODELS_CACHE


def load_featured_data() -> pd.DataFrame:
    global _DATA_CACHE
    if _DATA_CACHE is None:
        if not FEATURED_DATA_PATH.exists():
            raise FileNotFoundError(f"Featured dataset not found at {FEATURED_DATA_PATH}")
        _DATA_CACHE = pd.read_csv(FEATURED_DATA_PATH)
        _DATA_CACHE["transit_timestamp"] = pd.to_datetime(_DATA_CACHE["transit_timestamp"])
    return _DATA_CACHE


def load_station_metadata() -> pd.DataFrame:
    global _STATION_CACHE
    if _STATION_CACHE is None:
        if not STATION_INFO_PATH.exists():
            raise FileNotFoundError(f"Station info not found at {STATION_INFO_PATH}")
        _STATION_CACHE = pd.read_csv(STATION_INFO_PATH)
        _STATION_CACHE["id"] = _STATION_CACHE["id"].astype(str)
    return _STATION_CACHE


def classify_demand(ridership: float) -> str:
    """
    Classifies ridership using the empirical quartiles:
    Q1 = 417.6, Q2 = 1628.6, Q3 = 2953.2
    """
    if ridership < 417.6:
        return "Low"
    elif ridership < 1628.6:
        return "Moderate"
    elif ridership < 2953.2:
        return "High"
    else:
        return "Very High"


def build_feature_row(station_id: str, dt: datetime, station_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Constructs a single feature vector matching the model's exact expected column schema.
    """
    feature_cols = config["feature_columns"]
    hour = dt.hour
    day_of_week = dt.weekday()
    month = dt.month
    year = dt.year
    is_weekend = 1 if day_of_week in [5, 6] else 0
    
    # Peak period categorization
    if 7 <= hour <= 10:
        peak_period = "morning_peak"
    elif 16 <= hour <= 19:
        peak_period = "evening_peak"
    elif 10 < hour < 16:
        peak_period = "midday"
    else:
        peak_period = "night"
        
    station_meta = station_df[station_df["id"] == str(station_id)]
    if station_meta.empty:
        # Default fallback to first station
        station_meta = station_df.iloc[[0]]
        
    borough = station_meta.iloc[0]["borough"]
    lat = float(station_meta.iloc[0]["lat"])
    lon = float(station_meta.iloc[0]["lon"])
    
    # Query historical dataset for empirical lag & rolling stats
    data = load_featured_data()
    station_data = data[data["station_complex_id"].astype(str) == str(station_id)]
    
    if not station_data.empty:
        # Match nearest hour/day_of_week for representative lag baseline
        same_hour = station_data[station_data["hour"] == hour]
        if not same_hour.empty:
            lag_1h = float(same_hour["ridership_lag_1h"].mean())
            lag_24h = float(same_hour["ridership_lag_24h"].mean())
            lag_168h = float(same_hour["ridership_lag_168h"].mean())
            roll_mean = float(same_hour["ridership_rolling_mean_24h"].mean())
            roll_std = float(same_hour["ridership_rolling_std_24h"].mean())
        else:
            lag_1h = float(station_data["ridership"].mean())
            lag_24h = lag_1h
            lag_168h = lag_1h
            roll_mean = lag_1h
            roll_std = float(station_data["ridership"].std())
    else:
        lag_1h, lag_24h, lag_168h, roll_mean, roll_std = 1500.0, 1500.0, 1500.0, 1500.0, 400.0
        
    row_dict = {
        "hour": hour,
        "day_of_week": day_of_week,
        "month": month,
        "is_weekend": is_weekend,
        "latitude": lat,
        "longitude": lon,
        "ridership_lag_1h": lag_1h,
        "ridership_lag_24h": lag_24h,
        "ridership_lag_168h": lag_168h,
        "ridership_rolling_mean_24h": roll_mean,
        "ridership_rolling_std_24h": roll_std,
    }
    
    # Populate one-hot columns with exact zeros/ones
    for col in feature_cols:
        if col.startswith("borough_"):
            target_b = col.replace("borough_", "")
            row_dict[col] = 1 if borough.lower() == target_b.lower() else 0
        elif col.startswith("peak_period_"):
            target_p = col.replace("peak_period_", "")
            row_dict[col] = 1 if peak_period.lower() == target_p.lower() else 0
            
    # Ensure all columns present
    df_row = pd.DataFrame([row_dict])
    for col in feature_cols:
        if col not in df_row.columns:
            df_row[col] = 0
            
    return df_row[feature_cols]


def predict_demand(station_id: str, date_str: str, hour: int, model_name: str = "xgboost") -> Dict[str, Any]:
    """
    Main prediction endpoint logic. Predicts demand for a station at a given datetime.
    """
    models = load_models()
    config = load_model_config()
    station_df = load_station_metadata()
    
    dt = datetime.strptime(f"{date_str} {hour:02d}:00:00", "%Y-%m-%d %H:%M:%S")
    X_row = build_feature_row(str(station_id), dt, station_df, config)
    
    model_key = model_name.lower().replace(" ", "_")
    
    if model_key == "random_forest" and "random_forest" in models:
        pred = float(models["random_forest"].predict(X_row)[0])
    elif model_key == "lstm" and "lstm" in models:
        scaler_x = models["lstm_scaler_x"]
        scaler_y = models["lstm_scaler_y"]
        # Repeat row seq_len times for LSTM sequence input
        seq_len = config.get("seq_len", 12)
        X_scaled = scaler_x.transform(X_row)
        X_seq = np.repeat(X_scaled[np.newaxis, :, :], seq_len, axis=1)
        with torch.no_grad():
            t_in = torch.tensor(X_seq, dtype=torch.float32)
            lstm_scaled_pred = models["lstm"](t_in).item()
        pred = float(scaler_y.inverse_transform([[lstm_scaled_pred]])[0][0])
    else:
        # Default to XGBoost
        xgb_model = models.get("xgboost")
        if xgb_model is None:
            raise RuntimeError("XGBoost model not loaded.")
        pred = float(xgb_model.predict(X_row)[0])
        model_key = "xgboost"
        
    pred = max(0.0, round(pred, 1))
    
    # Station name lookup
    station_meta = station_df[station_df["id"] == str(station_id)]
    station_name = station_meta.iloc[0]["name"] if not station_meta.empty else f"Station {station_id}"
    borough = station_meta.iloc[0]["borough"] if not station_meta.empty else "Manhattan"
    
    return {
        "station_id": str(station_id),
        "station_name": station_name,
        "borough": borough,
        "date": date_str,
        "hour": hour,
        "datetime": dt.isoformat(),
        "model_used": model_key,
        "predicted_ridership": pred,
        "demand_level": classify_demand(pred)
    }


def forecast_next_hours(station_id: str, start_date: str, start_hour: int = 0, hours: int = 24, model_name: str = "xgboost") -> Dict[str, Any]:
    """
    Generates a consecutive hourly forecast for the requested horizon (e.g. 12, 24, 48 hours).
    """
    models = load_models()
    config = load_model_config()
    station_df = load_station_metadata()
    
    start_dt = datetime.strptime(f"{start_date} {start_hour:02d}:00:00", "%Y-%m-%d %H:%M:%S")
    station_meta = station_df[station_df["id"] == str(station_id)]
    station_name = station_meta.iloc[0]["name"] if not station_meta.empty else f"Station {station_id}"
    borough = station_meta.iloc[0]["borough"] if not station_meta.empty else "Manhattan"
    
    forecasts = []
    total_demand = 0.0
    peak_pred = 0.0
    peak_hour = 0
    
    for h in range(hours):
        current_dt = start_dt + timedelta(hours=h)
        pred_res = predict_demand(station_id, current_dt.strftime("%Y-%m-%d"), current_dt.hour, model_name)
        val = pred_res["predicted_ridership"]
        total_demand += val
        if val > peak_pred:
            peak_pred = val
            peak_hour = current_dt.hour
            
        forecasts.append({
            "hour": current_dt.hour,
            "date": current_dt.strftime("%Y-%m-%d"),
            "formatted_time": current_dt.strftime("%I:%M %p"),
            "timestamp": current_dt.isoformat(),
            "predicted_ridership": val,
            "demand_level": pred_res["demand_level"]
        })
        
    avg_demand = round(total_demand / hours, 1) if hours > 0 else 0.0
    
    return {
        "station_id": str(station_id),
        "station_name": station_name,
        "borough": borough,
        "start_date": start_date,
        "start_hour": start_hour,
        "hours_ahead": hours,
        "model_used": model_name,
        "forecasts": forecasts,
        "summary": {
            "average_ridership": avg_demand,
            "peak_ridership": peak_pred,
            "peak_hour": peak_hour,
            "total_predicted_passengers": round(total_demand, 1),
            "overall_demand_level": classify_demand(avg_demand)
        }
    }
