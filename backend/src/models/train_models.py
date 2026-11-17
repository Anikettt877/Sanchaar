"""
Model Training Pipeline for TRANSIT AI.

Trains, evaluates, and persists three ML/DL models on real MTA subway ridership:
1. Random Forest Regressor (Sklearn)
2. XGBoost Regressor (Extreme Gradient Boosting)
3. LSTM Recurrent Neural Network (PyTorch / Deep Learning)

Evaluation metrics: MAE, RMSE, R-squared, Residual analysis.
Saves models, metrics, configuration, and evaluation plots to backend/src/models/saved/.
"""

import os
import sys
import json
import time
import tempfile
import logging
from pathlib import Path

# Fix matplotlib directory before importing matplotlib
os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TrainModels")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURED_DATA_PATH = PROJECT_ROOT / "backend" / "data" / "processed" / "ridership_featured.csv"
SAVED_MODELS_DIR = PROJECT_ROOT / "backend" / "src" / "models" / "saved"


class PyTorchLSTM(nn.Module):
    """
    Two-layer LSTM Neural Network with Dropout and Dense output for demand forecasting.
    """
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
        # x shape: (batch_size, seq_len, input_dim)
        out, _ = self.lstm(x)
        # Use last time-step representation
        last_step = out[:, -1, :]
        h = self.relu(self.fc1(last_step))
        h = self.dropout(h)
        pred = self.fc2(h)
        return pred.squeeze(-1)


def prepare_features(df: pd.DataFrame):
    """
    Prepares feature matrix X and target y using time-based chronological ordering.
    Prevents data leakage.
    """
    logger.info("Preparing feature matrix and encoding categorical variables...")
    
    # Sort chronologically
    df = df.sort_values(by=["transit_timestamp", "station_complex_id"]).reset_index(drop=True)
    
    numeric_features = [
        "hour",
        "day_of_week",
        "month",
        "is_weekend",
        "latitude",
        "longitude",
        "ridership_lag_1h",
        "ridership_lag_24h",
        "ridership_lag_168h",
        "ridership_rolling_mean_24h",
        "ridership_rolling_std_24h"
    ]
    
    # One-hot encode borough and peak_period
    df_encoded = pd.get_dummies(df, columns=["borough", "peak_period"], drop_first=False)
    
    encoded_cols = [c for c in df_encoded.columns if c.startswith("borough_") or c.startswith("peak_period_")]
    all_feature_cols = numeric_features + encoded_cols
    
    X = df_encoded[all_feature_cols].copy()
    y = df_encoded["ridership"].values
    
    # Convert bool to int for one-hot cols
    for col in encoded_cols:
        X[col] = X[col].astype(int)
        
    return X, y, all_feature_cols, df_encoded


def train_and_evaluate_all():
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not FEATURED_DATA_PATH.exists():
        raise FileNotFoundError(f"Featured dataset not found at {FEATURED_DATA_PATH}. Run preprocessing first.")
        
    logger.info(f"Loading featured dataset from {FEATURED_DATA_PATH}...")
    df = pd.read_csv(FEATURED_DATA_PATH)
    logger.info(f"Loaded {len(df):,} records with {len(df.columns)} columns.")
    
    X, y, feature_cols, df_encoded = prepare_features(df)
    
    # Time-based Train-Test Split (80% train, 20% test chronologically)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    logger.info(f"Time-based split: {len(X_train):,} Train samples, {len(X_test):,} Test samples.")
    
    metrics_summary = {}
    
    # -------------------------------------------------------------
    # 1. RANDOM FOREST REGRESSOR
    # -------------------------------------------------------------
    logger.info("Training Random Forest Regressor (n_estimators=100, max_depth=16)...")
    t0 = time.time()
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=16,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_train_time = round(time.time() - t0, 2)
    
    y_pred_rf = rf.predict(X_test)
    y_pred_rf = np.maximum(y_pred_rf, 0)  # Demand cannot be negative
    
    rf_mae = float(mean_absolute_error(y_test, y_pred_rf))
    rf_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_rf)))
    rf_r2 = float(r2_score(y_test, y_pred_rf))
    
    logger.info(f"Random Forest evaluated - MAE: {rf_mae:.2f}, RMSE: {rf_rmse:.2f}, R2: {rf_r2:.4f} (took {rf_train_time}s)")
    
    metrics_summary["random_forest"] = {
        "model_name": "Random Forest Regressor",
        "mae": round(rf_mae, 2),
        "rmse": round(rf_rmse, 2),
        "r2": round(rf_r2, 4),
        "train_time_sec": rf_train_time,
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test)
    }
    joblib.dump(rf, SAVED_MODELS_DIR / "random_forest_model.joblib")
    
    # -------------------------------------------------------------
    # 2. XGBOOST REGRESSOR
    # -------------------------------------------------------------
    logger.info("Training XGBoost Regressor (n_estimators=150, max_depth=7, lr=0.08)...")
    t0 = time.time()
    xgb = XGBRegressor(
        n_estimators=150,
        max_depth=7,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1
    )
    xgb.fit(X_train, y_train)
    xgb_train_time = round(time.time() - t0, 2)
    
    y_pred_xgb = xgb.predict(X_test)
    y_pred_xgb = np.maximum(y_pred_xgb, 0)
    
    xgb_mae = float(mean_absolute_error(y_test, y_pred_xgb))
    xgb_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_xgb)))
    xgb_r2 = float(r2_score(y_test, y_pred_xgb))
    
    logger.info(f"XGBoost evaluated - MAE: {xgb_mae:.2f}, RMSE: {xgb_rmse:.2f}, R2: {xgb_r2:.4f} (took {xgb_train_time}s)")
    
    metrics_summary["xgboost"] = {
        "model_name": "XGBoost Regressor",
        "mae": round(xgb_mae, 2),
        "rmse": round(xgb_rmse, 2),
        "r2": round(xgb_r2, 4),
        "train_time_sec": xgb_train_time,
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test)
    }
    joblib.dump(xgb, SAVED_MODELS_DIR / "xgboost_model.joblib")
    
    # -------------------------------------------------------------
    # 3. LSTM DEEP LEARNING MODEL (PyTorch)
    # -------------------------------------------------------------
    logger.info("Training LSTM Neural Network for sequence forecasting...")
    t0 = time.time()
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X_train_scaled = scaler_X.fit_transform(X_train)
    X_test_scaled = scaler_X.transform(X_test)
    y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()
    y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1)).flatten()
    
    # Save scalers
    joblib.dump(scaler_X, SAVED_MODELS_DIR / "lstm_scaler_x.joblib")
    joblib.dump(scaler_y, SAVED_MODELS_DIR / "lstm_scaler_y.joblib")
    
    # Sequence creation for LSTM (seq_len = 12 hours lookback sequence)
    seq_len = 12
    def create_sequences(X_arr, y_arr, seq_length):
        xs, ys = [], []
        for i in range(len(X_arr) - seq_length):
            xs.append(X_arr[i:(i + seq_length)])
            ys.append(y_arr[i + seq_length])
        return np.array(xs), np.array(ys)
        
    X_train_seq, y_train_seq = create_sequences(X_train_scaled, y_train_scaled, seq_len)
    X_test_seq, y_test_seq = create_sequences(X_test_scaled, y_test_scaled, seq_len)
    
    # Subsample sequence batches for fast training while retaining high accuracy
    train_dataset = TensorDataset(torch.tensor(X_train_seq, dtype=torch.float32), torch.tensor(y_train_seq, dtype=torch.float32))
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    
    lstm_model = PyTorchLSTM(input_dim=len(feature_cols), hidden_dim=64, num_layers=2, dropout=0.2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(lstm_model.parameters(), lr=0.003)
    
    lstm_model.train()
    epochs = 12
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            preds = lstm_model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
    lstm_train_time = round(time.time() - t0, 2)
    
    # Evaluation of LSTM
    lstm_model.eval()
    with torch.no_grad():
        test_inputs = torch.tensor(X_test_seq, dtype=torch.float32)
        lstm_preds_scaled = lstm_model(test_inputs).numpy()
        
    y_pred_lstm = scaler_y.inverse_transform(lstm_preds_scaled.reshape(-1, 1)).flatten()
    y_pred_lstm = np.maximum(y_pred_lstm, 0)
    actual_lstm_y = y_test[seq_len:]
    
    lstm_mae = float(mean_absolute_error(actual_lstm_y, y_pred_lstm))
    lstm_rmse = float(np.sqrt(mean_squared_error(actual_lstm_y, y_pred_lstm)))
    lstm_r2 = float(r2_score(actual_lstm_y, y_pred_lstm))
    
    logger.info(f"LSTM evaluated - MAE: {lstm_mae:.2f}, RMSE: {lstm_rmse:.2f}, R2: {lstm_r2:.4f} (took {lstm_train_time}s)")
    
    metrics_summary["lstm"] = {
        "model_name": "LSTM Recurrent Neural Network",
        "mae": round(lstm_mae, 2),
        "rmse": round(lstm_rmse, 2),
        "r2": round(lstm_r2, 4),
        "train_time_sec": lstm_train_time,
        "sequence_length": seq_len,
        "n_samples_train": len(X_train_seq),
        "n_samples_test": len(X_test_seq)
    }
    
    # Save PyTorch LSTM weights & architecture info
    torch.save(lstm_model.state_dict(), SAVED_MODELS_DIR / "lstm_model.pt")
    
    # -------------------------------------------------------------
    # 4. SAVE CONFIG & METRICS
    # -------------------------------------------------------------
    config_data = {
        "feature_columns": feature_cols,
        "target": "ridership",
        "seq_len": seq_len,
        "num_features": len(feature_cols),
        "timestamp_saved": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(SAVED_MODELS_DIR / "model_config.json", "w") as f:
        json.dump(config_data, f, indent=2)
        
    with open(SAVED_MODELS_DIR / "model_metrics.json", "w") as f:
        json.dump(metrics_summary, f, indent=2)
        
    logger.info("Saved model_config.json and model_metrics.json.")
    
    # -------------------------------------------------------------
    # 5. GENERATE EVALUATION CHARTS
    # -------------------------------------------------------------
    logger.info("Generating evaluation comparison visualizations...")
    sample_size = min(200, len(y_test))
    indices = np.arange(sample_size)
    
    # Plot 1: Model Predictions vs Actual
    plt.figure(figsize=(14, 6))
    plt.plot(indices, y_test[:sample_size], label="Actual Ridership", color="#1e293b", linewidth=2.5)
    plt.plot(indices, y_pred_rf[:sample_size], label=f"Random Forest (R²={rf_r2:.3f})", color="#2563eb", linestyle="--", alpha=0.85)
    plt.plot(indices, y_pred_xgb[:sample_size], label=f"XGBoost (R²={xgb_r2:.3f})", color="#059669", linestyle="-.", alpha=0.85)
    plt.plot(indices, y_pred_lstm[:sample_size], label=f"LSTM (R²={lstm_r2:.3f})", color="#d97706", linestyle=":", alpha=0.85)
    plt.title("Actual vs Predicted Ridership Across Test Sequence (First 200 Hours)", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Test Sequence Hourly Index", fontsize=11)
    plt.ylabel("Hourly Ridership (Entries)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(frameon=True, facecolor="white", edgecolor="none")
    plt.tight_layout()
    plt.savefig(SAVED_MODELS_DIR / "model_comparison.png", dpi=180)
    plt.close()
    
    # Plot 2: Bar chart comparison of MAE, RMSE, R²
    models = ["Random Forest", "XGBoost", "LSTM"]
    maes = [rf_mae, xgb_mae, lstm_mae]
    rmses = [rf_rmse, xgb_rmse, lstm_rmse]
    r2s = [rf_r2, xgb_r2, lstm_r2]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    colors = ["#3b82f6", "#10b981", "#f59e0b"]
    
    axes[0].bar(models, maes, color=colors, width=0.5)
    axes[0].set_title("Mean Absolute Error (MAE - Lower is Better)", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("MAE (Passengers)")
    for i, v in enumerate(maes):
        axes[0].text(i, v + 5, f"{v:.1f}", ha="center", fontweight="bold")
        
    axes[1].bar(models, rmses, color=colors, width=0.5)
    axes[1].set_title("Root Mean Squared Error (RMSE - Lower is Better)", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("RMSE (Passengers)")
    for i, v in enumerate(rmses):
        axes[1].text(i, v + 10, f"{v:.1f}", ha="center", fontweight="bold")
        
    axes[2].bar(models, r2s, color=colors, width=0.5)
    axes[2].set_title("R-Squared Score (R² - Closer to 1 is Better)", fontsize=12, fontweight="bold")
    axes[2].set_ylabel("R²")
    axes[2].set_ylim([0, 1.05])
    for i, v in enumerate(r2s):
        axes[2].text(i, v + 0.02, f"{v:.4f}", ha="center", fontweight="bold")
        
    plt.tight_layout()
    plt.savefig(SAVED_MODELS_DIR / "metrics_comparison_bar.png", dpi=180)
    plt.close()
    
    logger.info("All models trained, evaluated, and saved successfully!")
    return metrics_summary


if __name__ == "__main__":
    train_and_evaluate_all()
