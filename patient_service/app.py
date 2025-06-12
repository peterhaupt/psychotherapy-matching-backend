"""Main application file for the Patient Service."""
from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from api.patients import PatientResource, PatientListResource, PatientCommunicationResource
from shared.config import get_config


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
    
    # Configure logging
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(PatientListResource, '/api/patients')
    api.add_resource(PatientResource, '/api/patients/<int:patient_id>')
    
    # NEW: Register communication history endpoint
    api.add_resource(PatientCommunicationResource, 
                     '/api/patients/<int:patient_id>/communication')

    return app


if __name__ == "__main__":
    config = get_config()
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.PATIENT_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )