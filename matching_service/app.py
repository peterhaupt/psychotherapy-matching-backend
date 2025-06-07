"""Main application file for the Matching Service."""
import logging
import signal
import sys

from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from api.matching import PlacementRequestResource, PlacementRequestListResource
from events.consumers import start_consumers
from shared.config import get_config
from db import init_db, close_db

# Initialize Flask-SQLAlchemy (for potential future use with Flask-SQLAlchemy features)
db = SQLAlchemy()


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
    
    # Initialize Flask-SQLAlchemy with app
    db.init_app(app)
    
    # Configure logging
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)

    # Register API endpoints
    api.add_resource(PlacementRequestListResource, '/api/placement-requests')
    api.add_resource(PlacementRequestResource, '/api/placement-requests/<int:request_id>')
    
    # TODO: Add bundle-specific endpoints when implemented
    # api.add_resource(PlatzsucheListResource, '/api/platzsuchen')
    # api.add_resource(PlatzsucheResource, '/api/platzsuchen/<int:search_id>')
    # api.add_resource(BundleListResource, '/api/therapeutenanfragen')
    # api.add_resource(BundleResource, '/api/therapeutenanfragen/<int:bundle_id>')
    # api.add_resource(BundleCreationResource, '/api/buendel/erstellen')

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Simple health check endpoint."""
        return {'status': 'healthy', 'service': 'matching-service'}, 200

    # Start Kafka consumers
    start_consumers()
    
    return app


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info('Shutting down Matching Service...')
    
    # Close database connections
    close_db()
    
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration
    config = get_config()
    
    # Initialize database (ensure tables exist)
    # Note: In production, use Alembic migrations instead
    try:
        init_db()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        # Continue anyway - migrations might handle this
    
    # Create and run app
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.MATCHING_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )