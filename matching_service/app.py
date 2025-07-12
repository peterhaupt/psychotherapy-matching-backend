"""Main application file for the Matching Service."""
import logging
import signal
import sys
import threading
import time
from datetime import datetime, time as datetime_time

from flask import Flask
from flask_restful import Api, Resource
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
    AnfrageResponseResource,
    AnfrageSendResource
)
from events.consumers import start_consumers
from shared.config import get_config, setup_logging
from db import close_db, get_db_context
from services import AnfrageService

# Initialize Flask-SQLAlchemy (for potential future use with Flask-SQLAlchemy features)
db = SQLAlchemy()

# Global flag for graceful shutdown
shutdown_flag = threading.Event()


class HealthCheckResource(Resource):
    """Health check endpoint for service monitoring."""
    
    def get(self):
        """Return health status of the matching service."""
        return {
            'status': 'healthy',
            'service': 'matching-service'
        }


def schedule_follow_up_calls():
    """Background task to schedule follow-up phone calls for unanswered anfragen."""
    logger = logging.getLogger(__name__)
    config = get_config()
    
    logger.info("Starting follow-up call scheduler thread")
    
    while not shutdown_flag.is_set():
        try:
            # Run at 09:00 daily
            now = datetime.now()
            target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
            
            # If it's already past 9 AM today, schedule for tomorrow
            if now >= target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            # Calculate seconds until 9 AM
            seconds_until_target = (target_time - now).total_seconds()
            
            logger.info(f"Next follow-up check scheduled for {target_time} ({seconds_until_target/3600:.1f} hours from now)")
            
            # Wait until target time or shutdown
            if shutdown_flag.wait(timeout=seconds_until_target):
                # Shutdown requested
                break
            
            # Perform the follow-up scheduling
            logger.info("Running daily follow-up call scheduling...")
            
            with get_db_context() as db:
                scheduled_count = AnfrageService.schedule_follow_up_calls(db)
                logger.info(f"Daily follow-up scheduling complete: {scheduled_count} calls scheduled")
                
        except Exception as e:
            logger.error(f"Error in follow-up scheduler: {str(e)}", exc_info=True)
            # Wait 5 minutes before retrying on error
            shutdown_flag.wait(timeout=300)
    
    logger.info("Follow-up call scheduler thread stopped")


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get and validate configuration
    config = get_config()
    config.validate("matching")
    
    # Log configuration status (non-sensitive values only)
    app.logger.info(f"Configuration validated for matching service")
    app.logger.info(f"Flask Environment: {config.FLASK_ENV}")
    app.logger.info(f"Database: {config.DB_NAME}")

    # Configure CORS using centralized settings
    CORS(app, **config.get_cors_settings())

    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = config.get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize Flask-SQLAlchemy with app
    db.init_app(app)
    
    # Configure logging for Flask app
    app.logger.setLevel(config.LOG_LEVEL)

    # Initialize RESTful API
    api = Api(app)
    
    # Register health check endpoint (at root level, not under /api)
    api.add_resource(HealthCheckResource, '/health')
    
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
    api.add_resource(AnfrageSendResource, '/api/therapeutenanfragen/<int:anfrage_id>/senden')

    # Start Kafka consumers
    start_consumers()
    
    # Start follow-up scheduler thread
    scheduler_thread = threading.Thread(
        target=schedule_follow_up_calls,
        daemon=True,
        name="follow-up-scheduler"
    )
    scheduler_thread.start()
    
    return app


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info('Shutting down Matching Service...')
    
    # Signal the follow-up scheduler to stop
    shutdown_flag.set()
    
    # Close database connections
    close_db()
    
    sys.exit(0)


if __name__ == "__main__":
    # Set up centralized logging
    setup_logging("matching-service")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration
    config = get_config()
    
    # Create and run app
    app = create_app()
    app.run(
        host="0.0.0.0", 
        port=config.MATCHING_SERVICE_PORT, 
        debug=config.FLASK_DEBUG
    )