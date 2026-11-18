"""
Transport Capacity Optimization & Allocation Routes for Sanchaar.
"""

import logging
from flask import Blueprint, jsonify, request

from ..src.optimization.optimizer import TransportOptimizer
from ..src.optimization.capacity_planner import CapacityPlanner

logger = logging.getLogger("OptimizationRoutes")
optimization_bp = Blueprint("optimization", __name__)

_optimizer = None
_planner = None

def get_optimizer(cap=50):
    global _optimizer
    if _optimizer is None or _optimizer.default_capacity != cap:
        _optimizer = TransportOptimizer(default_vehicle_capacity=cap)
    return _optimizer

def get_planner(cap=50):
    global _planner
    if _planner is None or _planner.default_capacity != cap:
        _planner = CapacityPlanner(default_vehicle_capacity=cap)
    return _planner


@optimization_bp.route("/recommend", methods=["POST"])
def get_recommendations():
    """
    Computes vehicle requirement sizing and operational recommendations.
    Payload: {"station_id": "229", "date": "2024-06-15", "vehicle_capacity": 50}
    """
    try:
        data = request.get_json() or {}
        station_id = str(data.get("station_id", "229"))
        date_str = data.get("date", "2024-06-15")
        capacity = int(data.get("vehicle_capacity", 50))
        
        opt = get_optimizer(capacity)
        report = opt.generate_daily_plan(station_id, date_str, capacity)
        return jsonify({"success": True, "data": report}), 200
    except Exception as e:
        logger.error(f"Optimization recommendation failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@optimization_bp.route("/allocate", methods=["POST"])
def allocate_fleet():
    """
    Solves proportional vehicle allocation across stations given total fleet constraints.
    Payload: {"station_predictions": [...], "total_vehicles": 120, "vehicle_capacity": 50}
    """
    try:
        data = request.get_json() or {}
        predictions = data.get("station_predictions", [])
        total_fleet = int(data.get("total_vehicles", 100))
        capacity = int(data.get("vehicle_capacity", 50))
        
        opt = get_optimizer(capacity)
        allocation = opt.optimize_allocation(predictions, total_fleet, capacity)
        return jsonify({"success": True, "data": allocation}), 200
    except Exception as e:
        logger.error(f"Fleet allocation failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@optimization_bp.route("/scenarios", methods=["POST"])
def compare_scenarios():
    """
    Compares vehicle capacity sizes (e.g. 30, 50, 80, 120 passengers).
    Payload: {"hourly_demand": 2400, "capacities": [30, 50, 80, 120]}
    """
    try:
        data = request.get_json() or {}
        demand = float(data.get("hourly_demand", 2000.0))
        caps = data.get("capacities", [30, 50, 80, 120])
        
        planner = get_planner()
        results = planner.compare_scenarios(demand, caps)
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        logger.error(f"Scenario comparison failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
