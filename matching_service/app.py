"""Main application file for the Matching Service."""
import logging
import signal
import sys

from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from api.anfrage import (
    PlatzsucheResource,
    PlatzsucheListResource,
    KontaktanfrageResource,
    TherapeutenZurAuswahlResource,
    TherapeutenanfrageResource,
    TherapeutenanfrageListResource,
    AnfrageCreationResource,
    AnfrageResponseResource
)
from events.consumers import start_consumers
from shared.config import get_config
# Commented out for Option 1: Use only Alembic migrations
# from db import init_db, close_db
from db import close_db

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
    
    # Reduce Kafka logging verbosity
    logging.getLogger('kafka').setLevel(logging.WARNING)
    logging.getLogger('kafka.consumer').setLevel(logging.WARNING)
    logging.getLogger('kafka.conn').setLevel(logging.WARNING)
    logging.getLogger('kafka.client').setLevel(logging.WARNING)
    logging.getLogger('kafka.protocol').setLevel(logging.WARNING)

    # Initialize RESTful API
    api = Api(app)
    
    # Register anfrage system API endpoints
    api.add_resource(PlatzsucheListResource, '/api/platzsuchen')
    api.add_resource(PlatzsucheResource, '/api/platzsuchen/<int:search_id>')
    api.add_resource(KontaktanfrageResource, '/api/platzsuchen/<int:search_id>/kontaktanfrage')
    
    # Therapist selection endpoint
    api.add_resource(TherapeutenZurAuswahlResource, '/api/therapeuten-zur-auswahl')
    
    # Anfrage management endpoints
    api.add_resource(TherapeutenanfrageListResource, '/api/therapeutenanfragen')
    api.add_resource(TherapeutenanfrageResource, '/api/therapeutenanfragen/<int:anfrage_id>')
    api.add_resource(AnfrageCreationResource, '/api/therapeutenanfragen/erstellen-fuer-therapeut')
    api.add_resource(AnfrageResponseResource, '/api/therapeutenanfragen/<int:anfrage_id>/antwort')

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
    
    # COMMENTED OUT - Option 1: Use only Alembic migrations
    # Initialize database (ensure tables exist)
    # Note: In production, use Alembic migrations instead
    # try:
    #     init_db()
    #     logging.info("Database initialized successfully")
    # except Exception as e:
    #     logging.error(f"Failed to initialize database: {str(e)}")
    #     # Continue anyway - migrations might handle this
    
    # Create and run app
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.MATCHING_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )
