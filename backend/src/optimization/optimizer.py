"""
Transport Capacity Optimization Engine for TRANSIT AI.

Calculates required transport capacity, analyzes fleet utilization, identifies bottlenecks,
and generates actionable resource allocation recommendations based on predicted demand.

NOTE: All outputs represent strategic transport planning estimates and resource sizing models,
not real-time operational safety signaling or automated train dispatch commands.
"""

import math
import logging
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from ..models.predict import predict_demand, forecast_next_hours, load_station_metadata

logger = logging.getLogger("TransportOptimizer")


class TransportOptimizer:
    """
    Intelligent fleet sizing and capacity recommendation engine.
    """

    def __init__(self, default_vehicle_capacity: int = 50):
        """
        Args:
            default_vehicle_capacity: Assumed nominal planning passenger capacity per transport vehicle unit.
        """
        self.default_capacity = max(1, default_vehicle_capacity)
        self.station_df = load_station_metadata()

    def estimate_vehicles_required(self, predicted_demand: float, vehicle_capacity: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates whole-number required vehicle units to accommodate forecasted demand:
        vehicles_required = ceil(demand / vehicle_capacity)
        """
        capacity = max(1, vehicle_capacity or self.default_capacity)
        demand = max(0.0, float(predicted_demand))
        
        vehicles_required = math.ceil(demand / capacity)
        total_capacity = vehicles_required * capacity
        excess_capacity = total_capacity - demand
        utilization_rate = round((demand / total_capacity) * 100, 1) if total_capacity > 0 else 0.0
        
        return {
            "predicted_demand": round(demand, 1),
            "vehicle_capacity": capacity,
            "vehicles_required": vehicles_required,
            "total_capacity_provided": total_capacity,
            "excess_capacity": round(excess_capacity, 1),
            "utilization_rate_pct": min(100.0, utilization_rate)
        }

    def analyze_station_demand(self, station_predictions: List[Dict[str, Any]], vehicle_capacity: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Evaluates demand across multiple stations and ranks by vehicle requirement intensity.
        """
        capacity = vehicle_capacity or self.default_capacity
        results = []
        
        for item in station_predictions:
            station_id = str(item.get("station_id", ""))
            station_name = item.get("station_name", f"Station {station_id}")
            demand = float(item.get("predicted_demand", item.get("ridership", 0.0)))
            
            sizing = self.estimate_vehicles_required(demand, capacity)
            results.append({
                "station_id": station_id,
                "station_name": station_name,
                "borough": item.get("borough", "Unknown"),
                "predicted_demand": round(demand, 1),
                "vehicles_required": sizing["vehicles_required"],
                "total_capacity": sizing["total_capacity_provided"],
                "utilization_pct": sizing["utilization_rate_pct"],
                "shortage_risk": "High" if sizing["utilization_rate_pct"] > 90 else ("Medium" if sizing["utilization_rate_pct"] > 75 else "Low")
            })
            
        results.sort(key=lambda x: x["predicted_demand"], reverse=True)
        return results

    def identify_capacity_shortages(self, station_predictions: List[Dict[str, Any]], current_allocation: Dict[str, int], vehicle_capacity: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Compares model-derived demand requirements against existing vehicle allocations.
        Identifies deficit (shortage) and surplus (over-provisioning) locations.
        """
        capacity = vehicle_capacity or self.default_capacity
        audit_results = []
        
        for item in station_predictions:
            s_id = str(item.get("station_id", ""))
            s_name = item.get("station_name", f"Station {s_id}")
            demand = float(item.get("predicted_demand", 0.0))
            allocated_vehicles = current_allocation.get(s_id, 0)
            
            sizing = self.estimate_vehicles_required(demand, capacity)
            needed_vehicles = sizing["vehicles_required"]
            
            diff = allocated_vehicles - needed_vehicles
            current_cap = allocated_vehicles * capacity
            
            if diff < 0:
                status = "Deficit (Shortage)"
                urgency = "High" if abs(diff) >= 5 else "Medium"
            elif diff > 3:
                status = "Surplus (Underutilized)"
                urgency = "Low"
            else:
                status = "Balanced"
                urgency = "None"
                
            audit_results.append({
                "station_id": s_id,
                "station_name": s_name,
                "predicted_demand": round(demand, 1),
                "current_vehicles_allocated": allocated_vehicles,
                "recommended_vehicles": needed_vehicles,
                "vehicle_discrepancy": diff,
                "current_capacity": current_cap,
                "capacity_gap": round(demand - current_cap, 1),
                "status": status,
                "action_priority": urgency
            })
            
        return audit_results

    def generate_recommendations(self, hourly_forecasts: List[Dict[str, Any]], vehicle_capacity: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Synthesizes operational recommendations based on 24-hour demand curve.
        """
        capacity = vehicle_capacity or self.default_capacity
        recommendations = []
        
        demands = [h["predicted_ridership"] for h in hourly_forecasts]
        avg_demand = np.mean(demands)
        peak_demand = max(demands)
        peak_hour = hourly_forecasts[np.argmax(demands)]["hour"]
        
        # 1. Peak hour surge sizing
        peak_sizing = self.estimate_vehicles_required(peak_demand, capacity)
        recommendations.append({
            "category": "Surge Capacity Planning",
            "priority": "High",
            "time_window": f"{peak_hour:02d}:00 - {(peak_hour+1)%24:02d}:00",
            "recommendation": f"Deploy maximum surge capacity of {peak_sizing['vehicles_required']} transport units at peak hour.",
            "rationale": f"Anticipated peak load of {peak_demand:,.0f} passengers requires {peak_sizing['total_capacity_provided']} seats/spaces to maintain utilization at {peak_sizing['utilization_rate_pct']}%.",
            "suggested_action": f"Stage {max(1, peak_sizing['vehicles_required'] // 3)} standby reserve units in nearby depot 30 minutes before {peak_hour:02d}:00."
        })
        
        # 2. Night / Early Morning Low Demand Optimization
        night_hours = [h for h in hourly_forecasts if h["hour"] in [1, 2, 3, 4]]
        if night_hours:
            night_demand = np.mean([h["predicted_ridership"] for h in night_hours])
            night_sizing = self.estimate_vehicles_required(night_demand, capacity)
            recommendations.append({
                "category": "Fleet Conservation",
                "priority": "Low",
                "time_window": "01:00 AM - 04:00 AM",
                "recommendation": f"Scale back night operations to {max(2, night_sizing['vehicles_required'])} active units.",
                "rationale": f"Average nighttime passenger volume drops to {night_demand:,.0f} riders, allowing scheduled maintenance intervals.",
                "suggested_action": "Schedule rolling train depot inspections and energy-efficient headways."
            })
            
        # 3. Morning vs Evening Balance
        morning_peak = [h for h in hourly_forecasts if 7 <= h["hour"] <= 9]
        evening_peak = [h for h in hourly_forecasts if 17 <= h["hour"] <= 19]
        if morning_peak and evening_peak:
            m_avg = np.mean([h["predicted_ridership"] for h in morning_peak])
            e_avg = np.mean([h["predicted_ridership"] for h in evening_peak])
            if e_avg > m_avg * 1.15:
                recommendations.append({
                    "category": "Asymmetric Peak Hedging",
                    "priority": "Medium",
                    "time_window": "05:00 PM - 07:00 PM",
                    "recommendation": "Evening commute generates 15%+ higher concentrated outbound boarding than morning intake.",
                    "rationale": f"Evening peak average ({e_avg:.0f}) exceeds morning peak ({m_avg:.0f}).",
                    "suggested_action": "Position auxiliary units near central business district terminals before 16:30."
                })
                
        return recommendations

    def optimize_allocation(self, station_predictions: List[Dict[str, Any]], total_fleet_vehicles: int, vehicle_capacity: Optional[int] = None) -> Dict[str, Any]:
        """
        Applies mathematical proportional demand allocation across a network given a fixed total fleet constraint.
        """
        capacity = vehicle_capacity or self.default_capacity
        total_fleet = max(1, total_fleet_vehicles)
        
        total_demand = sum(float(item.get("predicted_demand", 0.0)) for item in station_predictions)
        if total_demand <= 0:
            total_demand = 1.0
            
        allocations = []
        assigned_count = 0
        
        for item in station_predictions:
            s_id = str(item.get("station_id", ""))
            s_name = item.get("station_name", f"Station {s_id}")
            demand = float(item.get("predicted_demand", 0.0))
            
            # Proportional allocation share
            share = demand / total_demand
            allocated_units = max(1, math.floor(share * total_fleet))
            assigned_count += allocated_units
            
            provided_cap = allocated_units * capacity
            allocations.append({
                "station_id": s_id,
                "station_name": s_name,
                "predicted_demand": round(demand, 1),
                "demand_share_pct": round(share * 100, 2),
                "allocated_vehicles": allocated_units,
                "capacity_provided": provided_cap,
                "unmet_demand": max(0.0, round(demand - provided_cap, 1)),
                "utilization_pct": round((demand / provided_cap) * 100, 1) if provided_cap > 0 else 0.0
            })
            
        # Distribute remaining unallocated vehicles to highest unsatisfied demand
        remaining_units = max(0, total_fleet - assigned_count)
        allocations.sort(key=lambda x: x["unmet_demand"], reverse=True)
        
        for i in range(min(remaining_units, len(allocations))):
            allocations[i]["allocated_vehicles"] += 1
            allocations[i]["capacity_provided"] += capacity
            allocations[i]["unmet_demand"] = max(0.0, round(allocations[i]["predicted_demand"] - allocations[i]["capacity_provided"], 1))
            allocations[i]["utilization_pct"] = round((allocations[i]["predicted_demand"] / allocations[i]["capacity_provided"]) * 100, 1)
            remaining_units -= 1
            
        allocations.sort(key=lambda x: x["predicted_demand"], reverse=True)
        
        return {
            "total_fleet_size": total_fleet,
            "vehicle_capacity": capacity,
            "total_system_demand": round(total_demand, 1),
            "unallocated_vehicles": remaining_units,
            "station_allocations": allocations,
            "planning_disclaimer": "These estimates provide proportional resource sizing based on statistical demand distributions."
        }

    def generate_daily_plan(self, station_id: str, date: str, vehicle_capacity: Optional[int] = None) -> Dict[str, Any]:
        """
        Creates a complete 24-hour capacity sizing and scheduling plan for a target station.
        """
        capacity = vehicle_capacity or self.default_capacity
        forecast = forecast_next_hours(station_id, date, start_hour=0, hours=24, model_name="xgboost")
        
        hourly_schedule = []
        for item in forecast["forecasts"]:
            sizing = self.estimate_vehicles_required(item["predicted_ridership"], capacity)
            hourly_schedule.append({
                "hour": item["hour"],
                "formatted_time": item["formatted_time"],
                "predicted_demand": item["predicted_ridership"],
                "demand_level": item["demand_level"],
                "vehicles_required": sizing["vehicles_required"],
                "capacity_provided": sizing["total_capacity_provided"],
                "excess_capacity": sizing["excess_capacity"],
                "utilization_pct": sizing["utilization_rate_pct"]
            })
            
        recs = self.generate_recommendations(forecast["forecasts"], capacity)
        
        return {
            "station_id": str(station_id),
            "station_name": forecast["station_name"],
            "borough": forecast["borough"],
            "date": date,
            "vehicle_capacity": capacity,
            "summary": {
                "average_demand": forecast["summary"]["average_ridership"],
                "peak_demand": forecast["summary"]["peak_ridership"],
                "peak_hour": forecast["summary"]["peak_hour"],
                "max_vehicles_required": max(h["vehicles_required"] for h in hourly_schedule),
                "min_vehicles_required": min(h["vehicles_required"] for h in hourly_schedule),
                "avg_vehicles_required": round(np.mean([h["vehicles_required"] for h in hourly_schedule]), 1)
            },
            "hourly_schedule": hourly_schedule,
            "recommendations": recs,
            "planning_disclaimer": "Capacity recommendations are computational planning guidelines designed for headway modeling and fleet sizing."
        }
