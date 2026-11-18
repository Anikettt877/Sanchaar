"""
Configuration Settings for Sanchaar Backend.
Supports development SQLite and production PostgreSQL databases.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sanchaar-secret-key-2024-secure")
    
    # SQLite by default with zero configuration, easily overridden via DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'transit_ai.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Data Paths
    DATA_RAW_DIR = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
    MODELS_DIR = BASE_DIR / "src" / "models" / "saved"
    
    # Defaults
    DEFAULT_VEHICLE_CAPACITY = int(os.environ.get("DEFAULT_VEHICLE_CAPACITY", 50))
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "*"]
