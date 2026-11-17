"""
Capacity Planner & Headway Frequency Optimization Module for TRANSIT AI.

Determines recommended departure frequencies (headways) in minutes, hourly vehicle trips,
and performs scenario analysis comparing different vehicle sizing options (e.g. 30, 50, 80 passengers).
"""

import math
from typing import Dict, List, Any, Optional

import numpy as np


class CapacityPlanner:
    """
    Translates passenger demand into service headway recommendations and vehicle unit sizing comparisons.
    """

    def __init__(self, default_vehicle_capacity: int = 50, min_frequency_minutes: int = 3, max_frequency_minutes: int = 30):
        self.default_capacity = default_vehicle_capacity
        self.min_headway = min_frequency_minutes
        self.max_headway = max_frequency_minutes

    def plan_service_frequency(self, hourly_demand: float, vehicle_capacity: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculates suggested departure interval (headway in minutes).
        High demand -> frequent departures (short headway).
        Low demand -> longer headway (bounded by policy max).
        """
        cap = vehicle_capacity or self.default_capacity
        demand = max(0.0, float(hourly_demand))
        
        # Trips needed per hour to satisfy demand
        trips_needed = max(1, math.ceil(demand / cap))
        
        # Ideal headway = 60 minutes / trips_needed
        ideal_headway = 60.0 / trips_needed
        
        # Clamp between policy bounds
        practical_headway = max(self.min_headway, min(self.max_headway, round(ideal_headway)))
        actual_trips_per_hour = math.floor(60 / practical_headway)
        capacity_provided = actual_trips_per_hour * cap
        
        return {
            "hourly_demand": round(demand, 1),
            "vehicle_capacity": cap,
            "suggested_headway_minutes": practical_headway,
            "scheduled_trips_per_hour": actual_trips_per_hour,
            "hourly_capacity_offered": capacity_provided,
            "surplus_capacity": round(capacity_provided - demand, 1),
            "utilization_pct": round((demand / capacity_provided) * 100, 1) if capacity_provided > 0 else 0.0
        }

    def compare_scenarios(self, hourly_demand: float, capacities: List[int] = [30, 50, 80, 120]) -> List[Dict[str, Any]]:
        """
        Compares service frequency, vehicle requirements, and operating efficiency across multiple fleet configurations.
        """
        scenarios = []
        for cap in capacities:
            plan = self.plan_service_frequency(hourly_demand, cap)
            scenarios.append({
                "vehicle_capacity": cap,
                "vehicle_type_label": f"Unit Size {cap} (e.g. {'Micro-transit' if cap <= 30 else ('Standard Train Car' if cap <= 80 else 'Articulated / Heavy Rail')})",
                "suggested_headway_min": plan["suggested_headway_minutes"],
                "trips_per_hour": plan["scheduled_trips_per_hour"],
                "capacity_provided": plan["hourly_capacity_offered"],
                "utilization_pct": plan["utilization_pct"],
                "surplus_seats": plan["surplus_capacity"]
            })
        return scenarios
