"""
Analytics API Routes for TRANSIT AI.
"""

import logging
from flask import Blueprint, jsonify, request

from ..src.analytics.analytics_engine import AnalyticsEngine

logger = logging.getLogger("AnalyticsRoutes")
analytics_bp = Blueprint("analytics", __name__)

_analytics_engine = None

def get_engine():
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


@analytics_bp.route("/hourly", methods=["GET"])
def get_hourly():
    try:
        data = get_engine().get_hourly_distribution()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in hourly analytics: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/weekly", methods=["GET"])
def get_weekly():
    try:
        data = get_engine().get_daily_distribution()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in weekly analytics: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/monthly", methods=["GET"])
def get_monthly():
    try:
        data = get_engine().get_monthly_trend()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in monthly analytics: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/stations", methods=["GET"])
def get_stations_ranking():
    try:
        top_n = int(request.args.get("top_n", 10))
        data = get_engine().get_station_rankings(top_n=top_n)
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in station ranking: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/stations/<station_id>", methods=["GET"])
def get_station_details(station_id):
    try:
        data = get_engine().get_station_details(station_id)
        if not data:
            return jsonify({"success": False, "error": "Station not found"}), 404
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in station details: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/boroughs", methods=["GET"])
def get_boroughs():
    try:
        data = get_engine().get_borough_stats()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in borough stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/peak", methods=["GET"])
def get_peak_analysis():
    try:
        data = get_engine().get_peak_analysis()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in peak analysis: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/weekday-weekend", methods=["GET"])
def get_weekday_weekend():
    try:
        data = get_engine().get_weekday_weekend_comparison()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in weekday-weekend analytics: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/heatmap", methods=["GET"])
def get_heatmap():
    try:
        data = get_engine().get_demand_heatmap_data()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in heatmap data: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/routes", methods=["GET"])
def get_routes():
    try:
        data = get_engine().get_route_analytics()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Error in route analytics: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
