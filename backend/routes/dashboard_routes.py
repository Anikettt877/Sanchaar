"""
Dashboard API Routes for TRANSIT AI.
"""

import logging
from flask import Blueprint, jsonify, request

from ..src.analytics.analytics_engine import AnalyticsEngine
from ..database.db import get_recent_predictions

logger = logging.getLogger("DashboardRoutes")
dashboard_bp = Blueprint("dashboard", __name__)

_analytics_engine = None

def get_engine():
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


@dashboard_bp.route("/summary", methods=["GET"])
def get_summary():
    """Returns top-level metric counters and key statistics."""
    try:
        engine = get_engine()
        stats = engine.get_summary_stats()
        return jsonify({"success": True, "data": stats}), 200
    except Exception as e:
        logger.error(f"Error fetching summary: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/trends", methods=["GET"])
def get_trends():
    """Returns monthly demand trends and ridership aggregates."""
    try:
        engine = get_engine()
        trends = engine.get_monthly_trend()
        return jsonify({"success": True, "data": trends}), 200
    except Exception as e:
        logger.error(f"Error fetching trends: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/recent-activity", methods=["GET"])
def get_recent_activity():
    """Returns recent prediction records from database audit trail."""
    try:
        records = get_recent_predictions(limit=10)
        return jsonify({
            "success": True,
            "data": records
        }), 200
    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}", exc_info=True)
        return jsonify({"success": True, "data": []}), 200
