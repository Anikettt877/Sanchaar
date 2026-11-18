"""
Advanced Forecasting Engine for Sanchaar.

Provides multi-horizon temporal demand predictions:
- Hourly Forecasting (6, 12, 24, 48 hours)
- Multi-Day Forecasting (1 to 14 days)
- Peak Window Identification (Morning vs Evening Peak demand)
- Weekday vs Weekend Behavioral Pattern Forecasting
- Empirical Distribution-based Demand Level Thresholds
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from ..models.predict import predict_demand, forecast_next_hours, load_station_metadata, classify_demand

logger = logging.getLogger("ForecastEngine")


class ForecastEngine:
    """
    Dedicated forecasting engine supporting station-wise, horizon-wise,
    and temporal pattern predictions using trained models.
    """
    
    # Empirical quartiles computed from the 50,400 MTA ridership records
    THRESHOLDS = {
        "Q1_Low_Ceiling": 417.6,
        "Q2_Moderate_Ceiling": 1628.6,
        "Q3_High_Ceiling": 2953.2
    }

    def __init__(self):
        self.station_df = load_station_metadata()

    def get_demand_thresholds(self) -> Dict[str, float]:
        """Returns the empirical data quartiles used for demand classification."""
        return self.THRESHOLDS

    def classify_demand(self, predicted_value: float) -> str:
        """Categorize demand into Low, Moderate, High, or Very High."""
        return classify_demand(predicted_value)

    def hourly_forecast(self, station_id: str, date: str, num_hours: int = 24, model: str = "xgboost") -> Dict[str, Any]:
        """
        Generates consecutive hourly predictions starting from 00:00 on the selected date.
        """
        return forecast_next_hours(
            station_id=str(station_id),
            start_date=date,
            start_hour=0,
            hours=num_hours,
            model_name=model
        )

    def daily_forecast(self, station_id: str, start_date: str, num_days: int = 7, model: str = "xgboost") -> Dict[str, Any]:
        """
        Forecasts daily aggregated demand across the upcoming N days.
        """
        station_id = str(station_id)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        
        station_meta = self.station_df[self.station_df["id"] == station_id]
        station_name = station_meta.iloc[0]["name"] if not station_meta.empty else f"Station {station_id}"
        
        daily_results = []
        overall_total = 0.0
        
        for d in range(num_days):
            current_date_dt = start_dt + timedelta(days=d)
            date_str = current_date_dt.strftime("%Y-%m-%d")
            day_name = current_date_dt.strftime("%A")
            is_weekend = current_date_dt.weekday() in [5, 6]
            
            # Predict sample hours across the day to aggregate daily demand
            day_total = 0.0
            peak_val = 0.0
            peak_h = 0
            
            for h in range(24):
                pred = predict_demand(station_id, date_str, h, model)["predicted_ridership"]
                day_total += pred
                if pred > peak_val:
                    peak_val = pred
                    peak_h = h
                    
            daily_avg_hourly = round(day_total / 24, 1)
            overall_total += day_total
            
            daily_results.append({
                "date": date_str,
                "day_name": day_name,
                "is_weekend": is_weekend,
                "total_predicted_ridership": round(day_total, 1),
                "avg_hourly_ridership": daily_avg_hourly,
                "peak_hour": peak_h,
                "peak_ridership": round(peak_val, 1),
                "demand_level": self.classify_demand(daily_avg_hourly)
            })
            
        return {
            "station_id": station_id,
            "station_name": station_name,
            "start_date": start_date,
            "num_days": num_days,
            "model_used": model,
            "daily_forecasts": daily_results,
            "summary": {
                "total_period_demand": round(overall_total, 1),
                "daily_average": round(overall_total / num_days, 1) if num_days > 0 else 0.0
            }
        }

    def peak_hour_forecast(self, station_id: str, date: str, model: str = "xgboost") -> Dict[str, Any]:
        """
        Identifies expected morning and evening peak windows and compares against off-peak.
        """
        hourly_data = self.hourly_forecast(station_id, date, num_hours=24, model=model)["forecasts"]
        
        morning_hours = [h for h in hourly_data if 7 <= h["hour"] <= 10]
        evening_hours = [h for h in hourly_data if 16 <= h["hour"] <= 19]
        off_peak_hours = [h for h in hourly_data if h["hour"] < 7 or 10 < h["hour"] < 16 or h["hour"] > 19]
        
        m_avg = round(np.mean([h["predicted_ridership"] for h in morning_hours]), 1) if morning_hours else 0.0
        e_avg = round(np.mean([h["predicted_ridership"] for h in evening_hours]), 1) if evening_hours else 0.0
        op_avg = round(np.mean([h["predicted_ridership"] for h in off_peak_hours]), 1) if off_peak_hours else 0.0
        
        # Find absolute lowest and highest
        sorted_hours = sorted(hourly_data, key=lambda x: x["predicted_ridership"])
        lowest = sorted_hours[0]
        highest = sorted_hours[-1]
        
        return {
            "station_id": str(station_id),
            "date": date,
            "model_used": model,
            "morning_peak": {
                "window": "07:00 AM - 10:00 AM",
                "average_ridership": m_avg,
                "demand_level": self.classify_demand(m_avg)
            },
            "evening_peak": {
                "window": "04:00 PM - 07:00 PM",
                "average_ridership": e_avg,
                "demand_level": self.classify_demand(e_avg)
            },
            "off_peak": {
                "average_ridership": op_avg,
                "demand_level": self.classify_demand(op_avg)
            },
            "highest_demand": {
                "hour": highest["hour"],
                "formatted_time": highest["formatted_time"],
                "ridership": highest["predicted_ridership"],
                "demand_level": highest["demand_level"]
            },
            "lowest_demand": {
                "hour": lowest["hour"],
                "formatted_time": lowest["formatted_time"],
                "ridership": lowest["predicted_ridership"],
                "demand_level": lowest["demand_level"]
            },
            "hourly_breakdown": hourly_data
        }

    def weekday_weekend_comparison(self, station_id: str, base_date: str = "2024-06-12", model: str = "xgboost") -> Dict[str, Any]:
        """
        Compares expected travel profiles between a standard Wednesday (weekday) and Saturday (weekend).
        """
        # Choose Wednesday (2024-06-12) and Saturday (2024-06-15)
        weekday_forecast = self.hourly_forecast(station_id, "2024-06-12", num_hours=24, model=model)
        weekend_forecast = self.hourly_forecast(station_id, "2024-06-15", num_hours=24, model=model)
        
        wd_avg = weekday_forecast["summary"]["average_ridership"]
        we_avg = weekend_forecast["summary"]["average_ridership"]
        
        pct_diff = round(((wd_avg - we_avg) / we_avg) * 100, 1) if we_avg > 0 else 0.0
        
        hourly_comparison = []
        for i in range(24):
            wd_val = weekday_forecast["forecasts"][i]["predicted_ridership"]
            we_val = weekend_forecast["forecasts"][i]["predicted_ridership"]
            hourly_comparison.append({
                "hour": i,
                "formatted_time": f"{i:02d}:00",
                "weekday_ridership": wd_val,
                "weekend_ridership": we_val,
                "difference": round(wd_val - we_val, 1)
            })
            
        return {
            "station_id": str(station_id),
            "station_name": weekday_forecast["station_name"],
            "weekday_avg": wd_avg,
            "weekend_avg": we_avg,
            "difference_percentage": pct_diff,
            "higher_traffic_pattern": "Weekday" if wd_avg > we_avg else "Weekend",
            "hourly_comparison": hourly_comparison
        }
