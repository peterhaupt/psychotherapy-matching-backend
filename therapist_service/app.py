"""Main application file for the Therapist Service."""
from flask import Flask
from flask_restful import Api

from api.therapists import TherapistResource, TherapistListResource
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
    api.add_resource(TherapistListResource, '/api/therapists')
    api.add_resource(TherapistResource, '/api/therapists/<int:therapist_id>')

    return app


if __name__ == "__main__":
    config = get_config()
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.THERAPIST_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )