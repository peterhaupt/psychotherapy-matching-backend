"""Main application file for the Geocoding Service."""
import logging
from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS

from api.geocoding import (
    GeocodingResource,
    ReverseGeocodingResource,
    DistanceCalculationResource,
    PLZDistanceResource
)
from events.consumers import start_consumers
from shared.config import get_config, setup_logging


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get configuration
    config = get_config()

    # Configure CORS using centralized settings
    CORS(app, **config.get_cors_settings())

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure OpenStreetMap settings
    app.config["OSM_API_URL"] = config.OSM_API_URL
    app.config["OSM_USER_AGENT"] = config.OSM_USER_AGENT
    app.config["CACHE_TTL_SECONDS"] = config.CACHE_TTL_SECONDS
    
    # Configure logging
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(GeocodingResource, '/api/geocode')
    api.add_resource(ReverseGeocodingResource, '/api/reverse-geocode')
    api.add_resource(DistanceCalculationResource, '/api/calculate-distance')
    api.add_resource(PLZDistanceResource, '/api/calculate-plz-distance')

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "geocoding-service"
        }), 200

    # Start Kafka consumers
    start_consumers()

    return app


if __name__ == "__main__":
    # Set up centralized logging
    setup_logging("geocoding-service")
    
    config = get_config()
    logger = logging.getLogger(__name__)
    
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.GEOCODING_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )