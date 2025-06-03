"""Main application file for the Matching Service."""
from flask import Flask
from flask_restful import Api

from api.matching import PlacementRequestResource, PlacementRequestListResource
from events.consumers import start_consumers
from shared.config import get_config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get configuration
    config = get_config()

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configure logging
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(PlacementRequestListResource, '/api/placement-requests')
    api.add_resource(PlacementRequestResource, '/api/placement-requests/<int:request_id>')

    # Start Kafka consumers
    start_consumers()

    return app


if __name__ == "__main__":
    config = get_config()
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.MATCHING_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )