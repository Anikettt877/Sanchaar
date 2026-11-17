"""
Database Models for TRANSIT AI.

Defines relational entities for stations, historical ridership, prediction audit trails,
model performance metrics, capacity optimization logs, and dataset metadata.
Compatible with SQLite and PostgreSQL.
"""

from datetime import datetime
from .db import db


class Station(db.Model):
    __tablename__ = "stations"
    
    id = db.Column(db.Integer, primary_key=True)
    complex_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    borough = db.Column(db.String(100), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.complex_id,
            "complex_id": self.complex_id,
            "name": self.name,
            "borough": self.borough,
            "latitude": self.latitude,
            "longitude": self.longitude
        }


class RidershipRecord(db.Model):
    __tablename__ = "ridership_records"
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.String(50), db.ForeignKey("stations.complex_id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    ridership = db.Column(db.Float, nullable=False)
    transfers = db.Column(db.Float, default=0.0)
    hour = db.Column(db.Integer, nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    is_weekend = db.Column(db.Boolean, default=False)


class PredictionHistory(db.Model):
    __tablename__ = "prediction_history"
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.String(50), nullable=False, index=True)
    station_name = db.Column(db.String(255))
    target_datetime = db.Column(db.DateTime, nullable=False)
    model_used = db.Column(db.String(50), nullable=False)
    predicted_ridership = db.Column(db.Float, nullable=False)
    demand_level = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "station_id": self.station_id,
            "station_name": self.station_name,
            "target_datetime": self.target_datetime.isoformat() if self.target_datetime else None,
            "model_used": self.model_used,
            "predicted_ridership": self.predicted_ridership,
            "demand_level": self.demand_level,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ModelMetrics(db.Model):
    __tablename__ = "model_metrics"
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), unique=True, nullable=False)
    mae = db.Column(db.Float, nullable=False)
    rmse = db.Column(db.Float, nullable=False)
    r2 = db.Column(db.Float, nullable=False)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow)
    train_samples = db.Column(db.Integer)
    test_samples = db.Column(db.Integer)

    def to_dict(self):
        return {
            "model_name": self.model_name,
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "train_samples": self.train_samples,
            "test_samples": self.test_samples
        }


class OptimizationResult(db.Model):
    __tablename__ = "optimization_results"
    
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.String(50), nullable=False)
    target_date = db.Column(db.String(20), nullable=False)
    predicted_demand = db.Column(db.Float, nullable=False)
    vehicles_required = db.Column(db.Integer, nullable=False)
    vehicle_capacity = db.Column(db.Integer, nullable=False)
    utilization_rate = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DatasetMetadata(db.Model):
    __tablename__ = "dataset_metadata"
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_name = db.Column(db.String(255), nullable=False)
    records_count = db.Column(db.Integer, nullable=False)
    stations_count = db.Column(db.Integer, nullable=False)
    date_range_start = db.Column(db.String(50))
    date_range_end = db.Column(db.String(50))
    last_processed = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Active")


def init_db(app):
    """Initializes tables and seeds initial station metadata if needed."""
    with app.app_context():
        db.create_all()
