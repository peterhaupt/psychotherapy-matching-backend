"""Main application file for the Geocoding Service."""
import logging
import os
import json
from pathlib import Path
from flask import Flask, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
from sqlalchemy import create_engine, text

from api.geocoding import (
    GeocodingResource,
    ReverseGeocodingResource,
    DistanceCalculationResource,
    PLZDistanceResource
)
from events.consumers import start_consumers
from shared.config import get_config, setup_logging


class HealthCheckResource(Resource):
    """Health check endpoint for service monitoring."""
    
    def get(self):
        """Return health status of the geocoding service."""
        return {
            'status': 'healthy',
            'service': 'geocoding-service'
        }


def check_plz_data_exists(engine):
    """Check if PLZ centroids data exists in the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM geocoding_service.plz_centroids")
            ).scalar()
            return result > 0
    except Exception as e:
        logging.error(f"Error checking PLZ data: {e}")
        return False


def import_plz_data(engine, json_file_path):
    """Import PLZ data from JSON file into database."""
    logger = logging.getLogger(__name__)
    
    try:
        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filter for German entries
        german_entries = [
            entry for entry in data 
            if entry.get('country_code') == 'DE'
        ]
        
        logger.info(f"Found {len(german_entries)} German PLZ entries to import")
        
        if not german_entries:
            logger.warning("No German postal codes found in the file!")
            return False
        
        imported = 0
        skipped = 0
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                for entry in german_entries:
                    # Map JSON fields to German database columns
                    plz = entry.get('zipcode', '').strip()
                    
                    # Skip invalid PLZ
                    if not plz or len(plz) != 5 or not plz.isdigit():
                        skipped += 1
                        continue
                    
                    # Prepare data
                    data_dict = {
                        'plz': plz,
                        'ort': entry.get('place', '').strip(),
                        'bundesland': entry.get('state', '').strip(),
                        'bundesland_code': entry.get('state_code', '').strip(),
                        'latitude': float(entry.get('latitude', 0)),
                        'longitude': float(entry.get('longitude', 0))
                    }
                    
                    # Validate coordinates
                    if data_dict['latitude'] == 0 or data_dict['longitude'] == 0:
                        skipped += 1
                        continue
                    
                    # Insert (ignore duplicates)
                    conn.execute(text("""
                        INSERT INTO geocoding_service.plz_centroids 
                        (plz, ort, bundesland, bundesland_code, latitude, longitude)
                        VALUES (:plz, :ort, :bundesland, :bundesland_code, :latitude, :longitude)
                        ON CONFLICT (plz) DO NOTHING
                    """), data_dict)
                    imported += 1
                
                trans.commit()
                logger.info(f"Successfully imported {imported} PLZ entries ({skipped} skipped)")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error during PLZ import: {e}")
                return False
                
    except FileNotFoundError:
        logger.warning(f"PLZ data file not found: {json_file_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in PLZ data file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error importing PLZ data: {e}")
        return False


def initialize_plz_data():
    """Initialize PLZ centroids data if not already present."""
    logger = logging.getLogger(__name__)
    config = get_config()
    
    # Create engine with direct connection (not through PgBouncer)
    engine = create_engine(config.get_database_uri(use_pgbouncer=False))
    
    try:
        # Check if data already exists
        if check_plz_data_exists(engine):
            logger.info("PLZ centroids data already exists, skipping import")
            return
        
        logger.info("PLZ centroids data not found, attempting to import...")
        
        # Try to find the zipcodes file
        # In Docker, it should be mounted at /data/zipcodes.de.json
        # For local development, try ../data/zipcodes.de.json
        possible_paths = [
            "/data/zipcodes.de.json",  # Docker mount
            "../data/zipcodes.de.json",  # Local development
            "data/zipcodes.de.json",  # Alternative local path
        ]
        
        json_file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                json_file_path = path
                logger.info(f"Found PLZ data file at: {path}")
                break
        
        if not json_file_path:
            logger.warning(
                "PLZ data file (zipcodes.de.json) not found. "
                "PLZ distance calculations will not work. "
                "Please ensure the data folder is mounted or the file exists."
            )
            return
        
        # Import the data
        if import_plz_data(engine, json_file_path):
            logger.info("PLZ centroids data imported successfully")
        else:
            logger.warning("Failed to import PLZ centroids data")
            
    finally:
        engine.dispose()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Get and validate configuration
    config = get_config()
    config.validate("geocoding")
    
    # Log configuration status (non-sensitive values only)
    app.logger.info(f"Configuration validated for geocoding service")
    app.logger.info(f"Flask Environment: {config.FLASK_ENV}")
    app.logger.info(f"Database: {config.DB_NAME}")

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

    # Register health check endpoint (at root level, not under /api)
    api.add_resource(HealthCheckResource, '/health')

    # Register API endpoints
    api.add_resource(GeocodingResource, '/api/geocode')
    api.add_resource(ReverseGeocodingResource, '/api/reverse-geocode')
    api.add_resource(DistanceCalculationResource, '/api/calculate-distance')
    api.add_resource(PLZDistanceResource, '/api/calculate-plz-distance')

    # Initialize PLZ data if needed
    initialize_plz_data()

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
        port=config.GEOCODING_SERVICE_INTERNAL_PORT,
        debug=config.FLASK_DEBUG
    )