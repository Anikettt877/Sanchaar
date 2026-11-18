"""
Database Management for Sanchaar.
Uses Python's built-in sqlite3 database engine with connection pooling and thread safety.
Provides clean persistence for prediction history, audit logs, and metadata.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "transit_ai.db"


def get_db_connection():
    """Returns a connection to the SQLite database with dictionary-like row factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(app=None):
    """Initializes tables for stations, prediction history, model metrics, and dataset metadata."""
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id TEXT NOT NULL,
                station_name TEXT,
                target_datetime TEXT NOT NULL,
                model_used TEXT NOT NULL,
                predicted_ridership REAL NOT NULL,
                demand_level TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT UNIQUE NOT NULL,
                mae REAL NOT NULL,
                rmse REAL NOT NULL,
                r2 REAL NOT NULL,
                trained_at TEXT NOT NULL,
                train_samples INTEGER,
                test_samples INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS optimization_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_id TEXT NOT NULL,
                target_date TEXT NOT NULL,
                predicted_demand REAL NOT NULL,
                vehicles_required INTEGER NOT NULL,
                vehicle_capacity INTEGER NOT NULL,
                utilization_rate REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dataset_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT NOT NULL,
                records_count INTEGER NOT NULL,
                stations_count INTEGER NOT NULL,
                date_range_start TEXT,
                date_range_end TEXT,
                last_processed TEXT NOT NULL,
                status TEXT DEFAULT 'Active'
            )
        """)
    conn.close()


def record_prediction(station_id: str, station_name: str, target_datetime: str, model_used: str, predicted_ridership: float, demand_level: str):
    """Inserts a new prediction audit trail entry."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO prediction_history 
                (station_id, station_name, target_datetime, model_used, predicted_ridership, demand_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(station_id),
                str(station_name),
                str(target_datetime),
                str(model_used),
                float(predicted_ridership),
                str(demand_level),
                datetime.utcnow().isoformat()
            ))
    finally:
        conn.close()


def get_recent_predictions(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetches the most recent predictions recorded in the system."""
    conn = get_db_connection()
    try:
        cur = conn.execute("""
            SELECT id, station_id, station_name, target_datetime, model_used, predicted_ridership, demand_level, created_at
            FROM prediction_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
