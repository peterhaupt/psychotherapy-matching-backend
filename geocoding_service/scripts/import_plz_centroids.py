#!/usr/bin/env python3
"""Import German PLZ centroids into the database.

This script reads postal code data from a JSON file and imports it into
the plz_centroids table for fast distance calculations.

Usage:
    python geocoding_service/scripts/import_plz_centroids.py data/zipcodes.de.json
"""
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from shared.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def import_plz_data(json_file_path: str):
    """Import PLZ data from JSON file into database.
    
    Args:
        json_file_path: Path to the zipcodes.de.json file
    """
    config = get_config()
    
    # Create engine with direct connection (not through PgBouncer)
    engine = create_engine(config.get_database_uri(use_pgbouncer=False))
    
    # Read JSON file
    logger.info(f"Reading PLZ data from {json_file_path}")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file: {e}")
        sys.exit(1)
    
    # Filter for German entries (should be all of them in de.json)
    german_entries = [
        entry for entry in data 
        if entry.get('country_code') == 'DE'
    ]
    
    logger.info(f"Found {len(german_entries)} German PLZ entries")
    
    if not german_entries:
        logger.error("No German postal codes found in the file!")
        sys.exit(1)
    
    # Import data
    imported = 0
    skipped = 0
    updated = 0
    errors = 0
    
    # Start import
    logger.info("Starting import into plz_centroids table...")
    start_time = datetime.now()
    
    with engine.connect() as conn:
        # Begin transaction
        trans = conn.begin()
        
        try:
            for i, entry in enumerate(german_entries):
                try:
                    # Map JSON fields to German database columns
                    plz = entry.get('zipcode', '').strip()
                    
                    # Skip invalid PLZ
                    if not plz or len(plz) != 5 or not plz.isdigit():
                        logger.warning(f"Skipping invalid PLZ: {plz}")
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
                        logger.warning(f"Skipping PLZ {plz} with invalid coordinates")
                        skipped += 1
                        continue
                    
                    # Check if PLZ already exists
                    exists_result = conn.execute(
                        text("SELECT 1 FROM geocoding_service.plz_centroids WHERE plz = :plz"),
                        {'plz': plz}
                    ).fetchone()
                    
                    if exists_result:
                        # Update existing record
                        conn.execute(text("""
                            UPDATE geocoding_service.plz_centroids 
                            SET ort = :ort,
                                bundesland = :bundesland,
                                bundesland_code = :bundesland_code,
                                latitude = :latitude,
                                longitude = :longitude,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE plz = :plz
                        """), data_dict)
                        updated += 1
                    else:
                        # Insert new record
                        conn.execute(text("""
                            INSERT INTO geocoding_service.plz_centroids 
                            (plz, ort, bundesland, bundesland_code, latitude, longitude)
                            VALUES (:plz, :ort, :bundesland, :bundesland_code, :latitude, :longitude)
                        """), data_dict)
                        imported += 1
                    
                    # Log progress every 1000 records
                    if (i + 1) % 1000 == 0:
                        logger.info(f"Processed {i + 1}/{len(german_entries)} records...")
                        
                except (ValueError, KeyError) as e:
                    logger.error(f"Error processing entry {i}: {e}")
                    logger.debug(f"Problem entry: {entry}")
                    errors += 1
                    continue
                except SQLAlchemyError as e:
                    logger.error(f"Database error for PLZ {entry.get('zipcode')}: {e}")
                    errors += 1
                    continue
            
            # Commit transaction
            trans.commit()
            
            # Calculate duration
            duration = datetime.now() - start_time
            
            # Final statistics
            logger.info("=" * 60)
            logger.info("Import completed successfully!")
            logger.info(f"Duration: {duration}")
            logger.info(f"Total processed: {len(german_entries)}")
            logger.info(f"Imported (new): {imported}")
            logger.info(f"Updated (existing): {updated}")
            logger.info(f"Skipped (invalid): {skipped}")
            logger.info(f"Errors: {errors}")
            logger.info("=" * 60)
            
            # Verify import
            count_result = conn.execute(
                text("SELECT COUNT(*) FROM geocoding_service.plz_centroids")
            ).scalar()
            logger.info(f"Total PLZ centroids in database: {count_result}")
            
            # Show sample data
            logger.info("\nSample imported data:")
            samples = conn.execute(text("""
                SELECT plz, ort, bundesland, latitude, longitude 
                FROM geocoding_service.plz_centroids 
                ORDER BY plz 
                LIMIT 5
            """)).fetchall()
            
            for sample in samples:
                logger.info(f"  PLZ {sample[0]}: {sample[1]}, {sample[2]} ({sample[3]:.4f}, {sample[4]:.4f})")
                
        except Exception as e:
            # Rollback on any error
            trans.rollback()
            logger.error(f"Import failed: {e}")
            raise
    
    # Close engine
    engine.dispose()
    
    # Final message
    if imported > 0 or updated > 0:
        logger.info("\n✅ PLZ centroids import successful!")
        logger.info("The geocoding service can now use PLZ-based distance calculations.")
    else:
        logger.warning("\n⚠️  No data was imported. Please check the input file.")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python import_plz_centroids.py <path_to_zipcodes.de.json>")
        print("Example: python geocoding_service/scripts/import_plz_centroids.py data/zipcodes.de.json")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    # Check if file exists
    if not Path(json_file_path).exists():
        logger.error(f"File not found: {json_file_path}")
        sys.exit(1)
    
    # Run import
    try:
        import_plz_data(json_file_path)
    except Exception as e:
        logger.error(f"Import failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
