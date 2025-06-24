# PLZ-Based Distance Calculation Implementation Guide

## Overview
This guide describes how to implement a fast, approximate distance calculation system using German PLZ (postal code) centroids stored in PostgreSQL for the Psychotherapy Matching Platform.

## Background
The current geocoding service makes external API calls to OpenStreetMap for every distance calculation, which is:
- Slow (~200-500ms per request)
- Rate-limited
- Fails with test/invalid addresses
- Requires internet connectivity

The new PLZ-based system will provide:
- Fast lookups (~1-5ms per request)
- 100% reliability
- Works with test data
- No external dependencies

## Architecture Overview

```
Current Architecture:
Matching Service → Geocoding Service → OpenStreetMap API → Route calculation

New Architecture:
Matching Service → Geocoding Service → PostgreSQL (PLZ centroids) → Haversine distance
```

## Implementation Steps

### Step 1: Database Setup

Create a new table in the geocoding service schema:

```sql
-- Create the PLZ centroids table
CREATE TABLE geocoding_service.plz_centroids (
    plz VARCHAR(5) PRIMARY KEY,
    ort VARCHAR(255) NOT NULL,
    bundesland VARCHAR(100),
    bundesland_code VARCHAR(2),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast lookups
CREATE INDEX idx_plz_centroids_plz ON geocoding_service.plz_centroids(plz);

-- Add comment
COMMENT ON TABLE geocoding_service.plz_centroids IS 'German postal code centroids for fast distance approximation';
```

### Step 2: Obtain PLZ Data

1. **Primary Source**: https://github.com/zauberware/postal-codes-json-xml-csv
   - Download: `de.json` file
   - Contains ~8,200 German postal codes with coordinates
   - Format: JSON array with postal codes and their centroids

2. **Alternative Sources**:
   - https://www.suche-postleitzahl.org/download_files/public/plz_verzeichnis_sql.zip
   - https://github.com/openpotato/openplzapi-data

### Step 3: Create Import Script

Create `geocoding_service/scripts/import_plz_centroids.py`:

```python
"""Import German PLZ centroids into the database."""
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from shared.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_plz_data(json_file_path: str):
    """Import PLZ data from JSON file into database."""
    config = get_config()
    engine = create_engine(config.get_database_uri())
    
    # Read JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter for German entries
    german_entries = [
        entry for entry in data 
        if entry.get('country_code') == 'DE'
    ]
    
    logger.info(f"Found {len(german_entries)} German PLZ entries")
    
    # Import data
    imported = 0
    skipped = 0
    
    with engine.connect() as conn:
        for entry in german_entries:
            try:
                conn.execute(text("""
                    INSERT INTO geocoding_service.plz_centroids 
                    (plz, ort, bundesland, bundesland_code, latitude, longitude)
                    VALUES (:plz, :ort, :bundesland, :bundesland_code, :latitude, :longitude)
                    ON CONFLICT (plz) DO UPDATE SET
                        ort = EXCLUDED.ort,
                        bundesland = EXCLUDED.bundesland,
                        bundesland_code = EXCLUDED.bundesland_code,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    'plz': entry['zipcode'],
                    'ort': entry['place'],
                    'bundesland': entry.get('state', ''),
                    'bundesland_code': entry.get('state_code', ''),
                    'latitude': float(entry['latitude']),
                    'longitude': float(entry['longitude'])
                })
                imported += 1
            except Exception as e:
                logger.error(f"Error importing PLZ {entry.get('zipcode')}: {e}")
                skipped += 1
        
        conn.commit()
    
    logger.info(f"Import complete: {imported} imported, {skipped} skipped")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_plz_centroids.py <path_to_de.json>")
        sys.exit(1)
    
    import_plz_data(sys.argv[1])
```

### Step 4: Add New API Endpoint

Update `geocoding_service/api/geocoding.py`:

```python
class PLZDistanceResource(Resource):
    """REST resource for PLZ-based distance calculation."""
    
    def get(self):
        """Calculate distance between two PLZ centroids."""
        parser = reqparse.RequestParser()
        parser.add_argument('origin_plz', type=str, required=True,
                          help='Origin PLZ is required',
                          location='args')
        parser.add_argument('destination_plz', type=str, required=True,
                          help='Destination PLZ is required',
                          location='args')
        
        args = parser.parse_args()
        
        # Calculate distance using PLZ centroids
        result = calculate_plz_distance(
            args['origin_plz'],
            args['destination_plz']
        )
        
        if result:
            return result, 200
        else:
            return {
                'status': 'error',
                'error': 'One or both PLZ codes not found'
            }, 404
```

Register the endpoint in `geocoding_service/app.py`:
```python
api.add_resource(PLZDistanceResource, '/api/calculate-plz-distance')
```

### Step 5: Implement PLZ Distance Calculation

Add to `geocoding_service/utils/distance.py`:

```python
def get_plz_centroid(plz: str) -> Optional[Tuple[float, float]]:
    """Get centroid coordinates for a PLZ code.
    
    Args:
        plz: German postal code
        
    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT latitude, longitude 
            FROM geocoding_service.plz_centroids 
            WHERE plz = :plz
        """), {'plz': plz}).fetchone()
        
        if result:
            return (result.latitude, result.longitude)
        return None
        
    finally:
        db.close()


def calculate_plz_distance(
    origin_plz: str,
    destination_plz: str
) -> Optional[Dict[str, Any]]:
    """Calculate distance between two PLZ centroids.
    
    Args:
        origin_plz: Origin postal code
        destination_plz: Destination postal code
        
    Returns:
        Dict with distance information or None if PLZ not found
    """
    # Get centroids
    origin_coords = get_plz_centroid(origin_plz)
    destination_coords = get_plz_centroid(destination_plz)
    
    if not origin_coords or not destination_coords:
        return None
    
    # Calculate Haversine distance
    distance_km = calculate_haversine_distance(origin_coords, destination_coords)
    
    return {
        "distance_km": distance_km,
        "status": "success",
        "source": "plz_centroids",
        "origin_centroid": {
            "latitude": origin_coords[0],
            "longitude": origin_coords[1]
        },
        "destination_centroid": {
            "latitude": destination_coords[0],
            "longitude": destination_coords[1]
        }
    }
```

### Step 6: Update Existing Distance Calculation

Modify the existing `calculate_distance` function to use PLZ fallback:

```python
def calculate_distance(
    origin: Union[str, Tuple[float, float]],
    destination: Union[str, Tuple[float, float]],
    travel_mode: str = "car",
    use_cache: bool = True,
    use_plz_fallback: bool = True
) -> Dict[str, Any]:
    """Calculate distance with PLZ fallback."""
    
    # Try normal calculation first
    result = # ... existing implementation ...
    
    # If failed and PLZ fallback enabled
    if not result and use_plz_fallback and isinstance(origin, str) and isinstance(destination, str):
        # Extract PLZ from addresses
        origin_plz = extract_plz_from_address(origin)
        destination_plz = extract_plz_from_address(destination)
        
        if origin_plz and destination_plz:
            plz_result = calculate_plz_distance(origin_plz, destination_plz)
            if plz_result:
                plz_result["note"] = "Approximate distance based on postal code areas"
                return plz_result
    
    return result
```

### Step 7: Remove Unused Endpoint

Remove from `geocoding_service/api/geocoding.py`:
- `TherapistSearchResource` class
- Related imports

Remove from `geocoding_service/app.py`:
- `api.add_resource(TherapistSearchResource, '/api/find-therapists')` line

### Step 8: Create Alembic Migration

Create a new migration file:

```python
"""Add PLZ centroids table for fast distance calculation

Revision ID: xxx
Revises: yyy
Create Date: 2024-xx-xx
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create PLZ centroids table
    op.create_table(
        'plz_centroids',
        sa.Column('plz', sa.String(5), primary_key=True),
        sa.Column('ort', sa.String(255), nullable=False),
        sa.Column('bundesland', sa.String(100)),
        sa.Column('bundesland_code', sa.String(2)),
        sa.Column('latitude', sa.Float, nullable=False),
        sa.Column('longitude', sa.Float, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp()),
        schema='geocoding_service'
    )
    
    # Create index
    op.create_index('idx_plz_centroids_plz', 'plz_centroids', ['plz'], schema='geocoding_service')

def downgrade():
    op.drop_index('idx_plz_centroids_plz', schema='geocoding_service')
    op.drop_table('plz_centroids', schema='geocoding_service')
```

## Usage Examples

### 1. Fast Pre-filtering in Matching Service

```python
# In matching_service/algorithms/anfrage_creator.py
def check_distance_constraint_fast(patient_plz: str, therapist_plz: str, max_distance: float) -> bool:
    """Quick check using PLZ distance before detailed calculation."""
    response = requests.get(
        f"{GEOCODING_SERVICE_URL}/api/calculate-plz-distance",
        params={
            'origin_plz': patient_plz,
            'destination_plz': therapist_plz
        }
    )
    
    if response.status_code == 200:
        distance = response.json()['distance_km']
        # Add 50% buffer for PLZ approximation
        return distance <= max_distance * 1.5
    
    # If PLZ lookup fails, allow through to detailed check
    return True
```

### 2. Display Approximate Distance

```python
# For UI display
def get_approximate_distance(patient_plz: str, therapist_plz: str) -> str:
    """Get approximate distance for display."""
    response = requests.get(
        f"{GEOCODING_SERVICE_URL}/api/calculate-plz-distance",
        params={
            'origin_plz': patient_plz,
            'destination_plz': therapist_plz
        }
    )
    
    if response.status_code == 200:
        distance = response.json()['distance_km']
        return f"~{round(distance, 0):.0f} km"
    
    return "Entfernung unbekannt"
```

## Testing

### Unit Tests

```python
def test_plz_distance_calculation():
    """Test PLZ-based distance calculation."""
    # Berlin Mitte to Munich
    result = calculate_plz_distance("10117", "80331")
    assert result is not None
    assert 500 < result['distance_km'] < 600
    
    # Same PLZ
    result = calculate_plz_distance("10117", "10117")
    assert result['distance_km'] == 0
    
    # Invalid PLZ
    result = calculate_plz_distance("99999", "10117")
    assert result is None
```

### Integration Tests

```bash
# Test the API endpoint
curl "http://localhost:8005/api/calculate-plz-distance?origin_plz=10117&destination_plz=80331"

# Expected response:
{
  "distance_km": 504.7,
  "status": "success",
  "source": "plz_centroids",
  "origin_centroid": {"latitude": 52.5200, "longitude": 13.4050},
  "destination_centroid": {"latitude": 48.1351, "longitude": 11.5820}
}
```

## Performance Comparison

| Operation | Current (OSM) | New (PLZ) | Improvement |
|-----------|--------------|-----------|-------------|
| Single distance | 200-500ms | 1-5ms | 100x faster |
| 100 distances | 20-50s | 0.1-0.5s | 100x faster |
| External dependency | Yes | No | More reliable |
| Works offline | No | Yes | Better for testing |
| Accuracy | ±100m | ±5km | Good for filtering |

## Migration Strategy

1. **Phase 1**: Deploy PLZ system alongside existing system
2. **Phase 2**: Use PLZ for pre-filtering in matching service
3. **Phase 3**: Monitor performance and accuracy
4. **Phase 4**: Optimize based on results

## Future Enhancements

1. **Weighted Centroids**: Calculate centroids based on population density
2. **PLZ Boundaries**: Store actual PLZ boundaries for more accurate calculations
3. **Caching Layer**: Add Redis for even faster lookups
4. **Batch Endpoint**: Calculate distances for multiple PLZ pairs in one request

## Conclusion

This implementation provides a simple, fast, and reliable distance approximation system that:
- Solves the test data problem
- Dramatically improves performance
- Reduces external dependencies
- Maintains the existing precise calculation for when accuracy is needed

The system can be implemented incrementally without disrupting existing functionality.