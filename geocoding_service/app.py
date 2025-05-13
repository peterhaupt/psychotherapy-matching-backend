"""Main application file for the Geocoding Service."""
import logging
from flask import Flask
from flask_restful import Api

from api.geocoding import (
    GeocodingResource,
    ReverseGeocodingResource,
    DistanceCalculationResource,
    TherapistSearchResource
)
from events.consumers import start_consumers
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure OpenStreetMap settings
    app.config["OSM_API_URL"] = config.OSM_API_URL
    app.config["OSM_USER_AGENT"] = config.OSM_USER_AGENT
    app.config["CACHE_TTL_SECONDS"] = config.CACHE_TTL_SECONDS

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(GeocodingResource, '/api/geocode')
    api.add_resource(ReverseGeocodingResource, '/api/reverse-geocode')
    api.add_resource(DistanceCalculationResource, '/api/calculate-distance')
    api.add_resource(TherapistSearchResource, '/api/find-therapists')

    # Start Kafka consumers
    start_consumers()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=config.SERVICE_PORT, debug=config.DEBUG)