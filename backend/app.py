"""
Main Flask Application for TRANSIT AI Backend.
Intelligent Public Transportation Demand Forecasting & Optimization System.
"""

import os
import sys
import logging
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .database.db import init_db
from .routes.dashboard_routes import dashboard_bp
from .routes.analytics_routes import analytics_bp
from .routes.prediction_routes import prediction_bp
from .routes.optimization_routes import optimization_bp
from .routes.data_routes import data_bp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("TransitAI_App")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS for frontend clients
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize Database
    init_db(app)
    
    # Register API Blueprints
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(prediction_bp, url_prefix="/api")
    app.register_blueprint(optimization_bp, url_prefix="/api/optimization")
    app.register_blueprint(data_bp, url_prefix="/api/datasets")
    
    # Health check endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "online",
            "service": "TRANSIT AI Backend REST API",
            "version": "1.0.0",
            "models_loaded": True
        }), 200
        
    # Global JSON error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "Internal server error"}), 500
        
    return app


if __name__ == "__main__":
    app = create_app()
    logger.info("Starting TRANSIT AI Flask Backend server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
