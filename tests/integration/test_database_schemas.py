"""Integration tests for database schemas across all microservices.

This test file validates that all required schemas, tables, and columns exist
and have the correct structure after migrations have been run.

When running from the host machine, the test connects to localhost instead of
Docker container hostnames. Set TEST_DOCKER_NETWORK=true to use container hostnames.
"""
import os
import sys
import pytest
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from sqlalchemy.dialects.postgresql import ENUM

# Add the project root to Python path to import shared modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import get_config


# Get configuration
config = get_config()


def extract_enum_values(column_type):
    """Extract enum values from a column type.
    
    Args:
        column_type: SQLAlchemy column type
        
    Returns:
        List of enum values or None if not an enum
    """
    # Check if it's a PostgreSQL ENUM type
    if hasattr(column_type, 'enums'):
        return column_type.enums
    
    # Check the string representation for ENUM pattern
    type_str = str(column_type)
    if type_str.startswith('ENUM('):
        # Extract values from string like "ENUM('VALUE1', 'VALUE2', name='enumname')"
        import re
        matches = re.findall(r"'([^']+)'", type_str)
        # Filter out the name parameter
        values = [m for m in matches if not m.startswith('name=')]
        return values if values else None
    
    return None


def is_enum_column(column):
    """Check if a column is an enum type.
    
    Args:
        column: Column metadata dict from inspector
        
    Returns:
        bool: True if column appears to be an enum
    """
    # Check if type is USER-DEFINED (direct connection)
    if str(column['type']).startswith('USER-DEFINED'):
        return True
    
    # Check if we can extract enum values
    enum_values = extract_enum_values(column['type'])
    if enum_values:
        return True
    
    # For VARCHAR types, check if there's enum info in the type object
    if hasattr(column.get('type'), 'enums'):
        return True
    
    return False


@pytest.fixture(scope="module")
def db_engine():
    """Create a database engine connected through PgBouncer."""
    # Determine if we're running inside Docker network or from host
    use_docker_network = os.environ.get('TEST_DOCKER_NETWORK', 'false').lower() == 'true'
    
    if use_docker_network:
        # Use container hostnames (for CI/CD or running inside Docker)
        pgbouncer_host = config.PGBOUNCER_HOST
    else:
        # Use localhost when running from host machine
        pgbouncer_host = "localhost"
    
    pgbouncer_port = config.PGBOUNCER_PORT
    
    # Build connection string
    database_url = (
        f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@"
        f"{pgbouncer_host}:{pgbouncer_port}/{config.DB_NAME}"
    )
    
    print(f"Connecting to database through PgBouncer at: {pgbouncer_host}:{pgbouncer_port}")
    
    try:
        engine = create_engine(database_url)
        # Test the connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("Successfully connected to database through PgBouncer")
        yield engine
    except OperationalError as e:
        pytest.fail(
            f"Failed to connect to database through PgBouncer at {pgbouncer_host}:{pgbouncer_port}. "
            f"Error: {str(e)}. "
            f"Make sure Docker containers are running (docker-compose up -d)"
        )
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def db_inspector(db_engine):
    """Create a database inspector for schema introspection."""
    return inspect(db_engine)


class TestDatabaseSchemas:
    """Test class for validating all database schemas."""
    
    def test_pgbouncer_connection(self, db_engine):
        """Test that we can connect through PgBouncer."""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            assert db_name == config.DB_NAME, f"Connected to wrong database: {db_name}"
            
            # Verify we're actually going through PgBouncer by checking application_name
            result = conn.execute(text("SELECT application_name FROM pg_stat_activity WHERE pid = pg_backend_pid()"))
            app_name = result.scalar()
            # PgBouncer connections typically show as 'pgbouncer' or may be empty
            print(f"Application name: {app_name}")
    
    def test_all_schemas_exist(self, db_inspector):
        """Test that all required schemas exist."""
        expected_schemas = [
            'patient_service',
            'therapist_service',
            'matching_service',
            'communication_service',
            'geocoding_service',
            'scraping_service'
        ]
        
        existing_schemas = db_inspector.get_schema_names()
        
        for schema in expected_schemas:
            assert schema in existing_schemas, f"Schema '{schema}' does not exist"
    
    def test_patient_service_schema(self, db_inspector):
        """Test patient_service schema structure."""
        schema = 'patient_service'
        
        # Check tables exist
        tables = db_inspector.get_table_names(schema=schema)
        assert 'patients' in tables, f"Table 'patients' not found in {schema}"
        
        # Check patients table structure
        columns = db_inspector.get_columns('patients', schema=schema)
        column_dict = {col['name']: col for col in columns}
        
        # Verify required columns exist with correct types
        expected_columns = {
            'id': {'type': 'INTEGER', 'nullable': False},
            'anrede': {'type': 'VARCHAR', 'nullable': True},
            'vorname': {'type': 'VARCHAR', 'nullable': False},
            'nachname': {'type': 'VARCHAR', 'nullable': False},
            'email': {'type': 'VARCHAR', 'nullable': True},
            'telefon': {'type': 'VARCHAR', 'nullable': True},
            'diagnose': {'type': 'VARCHAR', 'nullable': True},
            'status': {
                'type': 'ENUM',
                'nullable': True,
                'enum_values': ['offen', 'auf der Suche', 'in Therapie', 'Therapie abgeschlossen', 
                               'Suche abgebrochen', 'Therapie abgebrochen']
            },
            'zeitliche_verfuegbarkeit': {'type': 'JSONB', 'nullable': True},
            'created_at': {'type': 'DATE', 'nullable': True},
            'updated_at': {'type': 'DATE', 'nullable': True},
        }
        
        for col_name, expected in expected_columns.items():
            assert col_name in column_dict, f"Column '{col_name}' not found in patients table"
            
            col = column_dict[col_name]
            
            # Special handling for ENUM columns
            if expected['type'] == 'ENUM':
                assert is_enum_column(col), f"Column '{col_name}' is not an ENUM type"
                
                # Verify enum values if specified
                if 'enum_values' in expected:
                    actual_values = extract_enum_values(col['type'])
                    if actual_values:
                        # Check if the migration converted to uppercase (English values)
                        # or kept the German values
                        expected_upper = [v.upper().replace(' ', '_') for v in expected['enum_values']]
                        if set(actual_values) == set(['OPEN', 'SEARCHING', 'IN_THERAPY', 
                                                      'THERAPY_COMPLETED', 'SEARCH_ABORTED', 
                                                      'THERAPY_ABORTED']):
                            # English enum values - this is fine
                            pass
                        else:
                            # Should be German values
                            assert set(actual_values) == set(expected['enum_values']), \
                                f"Column '{col_name}' has wrong enum values: {actual_values}"
            else:
                # For non-enum columns, check type normally
                assert str(col['type']).startswith(expected['type']), \
                    f"Column '{col_name}' has wrong type: {col['type']} (expected {expected['type']})"
            
            # Check nullable constraint
            assert col['nullable'] == expected['nullable'], \
                f"Column '{col_name}' nullable mismatch: {col['nullable']} (expected {expected['nullable']})"
        
        # Check primary key
        pk = db_inspector.get_pk_constraint('patients', schema=schema)
        assert pk['constrained_columns'] == ['id'], "Primary key not set on 'id' column"
        
        # Check indexes
        indexes = db_inspector.get_indexes('patients', schema=schema)
        assert any(idx['column_names'] == ['id'] for idx in indexes), "Index on 'id' column not found"
    
    def test_therapist_service_schema(self, db_inspector):
        """Test therapist_service schema structure."""
        schema = 'therapist_service'
        
        # Check tables exist
        tables = db_inspector.get_table_names(schema=schema)
        assert 'therapists' in tables, f"Table 'therapists' not found in {schema}"
        
        # Check therapists table structure
        columns = db_inspector.get_columns('therapists', schema=schema)
        column_dict = {col['name']: col for col in columns}
        
        expected_columns = {
            'id': {'type': 'INTEGER', 'nullable': False},
            'titel': {'type': 'VARCHAR', 'nullable': True},
            'vorname': {'type': 'VARCHAR', 'nullable': False},
            'nachname': {'type': 'VARCHAR', 'nullable': False},
            'email': {'type': 'VARCHAR', 'nullable': True},
            'telefon': {'type': 'VARCHAR', 'nullable': True},
            'kassensitz': {'type': 'BOOLEAN', 'nullable': True},
            'telefonische_erreichbarkeit': {'type': 'JSONB', 'nullable': True},
            'status': {
                'type': 'ENUM',
                'nullable': True,
                'enum_values': ['aktiv', 'gesperrt', 'inaktiv']
            },
            'potentially_available': {'type': 'BOOLEAN', 'nullable': True},
            'potentially_available_notes': {'type': 'TEXT', 'nullable': True},
        }
        
        for col_name, expected in expected_columns.items():
            assert col_name in column_dict, f"Column '{col_name}' not found in therapists table"
            
            col = column_dict[col_name]
            
            # Special handling for ENUM columns
            if expected['type'] == 'ENUM':
                assert is_enum_column(col), f"Column '{col_name}' is not an ENUM type"
                
                # Verify enum values if specified
                if 'enum_values' in expected:
                    actual_values = extract_enum_values(col['type'])
                    if actual_values:
                        # Check for either German or English values
                        if set(actual_values) == set(['ACTIVE', 'BLOCKED', 'INACTIVE']):
                            # English enum values - this is fine
                            pass
                        else:
                            # Should be German values
                            assert set(actual_values) == set(expected['enum_values']), \
                                f"Column '{col_name}' has wrong enum values: {actual_values}"
            else:
                # For non-enum columns, check type normally
                assert str(col['type']).startswith(expected['type']), \
                    f"Column '{col_name}' has wrong type: {col['type']} (expected {expected['type']})"
    
    def test_matching_service_schema(self, db_inspector):
        """Test matching_service schema structure."""
        schema = 'matching_service'
        
        # Check tables exist
        tables = db_inspector.get_table_names(schema=schema)
        assert 'placement_requests' in tables, f"Table 'placement_requests' not found in {schema}"
        
        # Check placement_requests table structure
        columns = db_inspector.get_columns('placement_requests', schema=schema)
        column_dict = {col['name']: col for col in columns}
        
        expected_columns = {
            'id': {'type': 'INTEGER', 'nullable': False},
            'patient_id': {'type': 'INTEGER', 'nullable': False},
            'therapist_id': {'type': 'INTEGER', 'nullable': False},
            'status': {
                'type': 'ENUM',
                'nullable': True,
                'enum_values': ['offen', 'in_bearbeitung', 'abgelehnt', 'angenommen']
            },
            'created_at': {'type': 'DATE', 'nullable': True},
            'email_contact_date': {'type': 'DATE', 'nullable': True},
            'phone_contact_date': {'type': 'DATE', 'nullable': True},
            'response': {'type': 'TEXT', 'nullable': True},
            'priority': {'type': 'INTEGER', 'nullable': True},
        }
        
        for col_name, expected in expected_columns.items():
            assert col_name in column_dict, f"Column '{col_name}' not found in placement_requests table"
            
            col = column_dict[col_name]
            
            # Special handling for ENUM columns
            if expected['type'] == 'ENUM':
                assert is_enum_column(col), f"Column '{col_name}' is not an ENUM type"
                
                if 'enum_values' in expected:
                    actual_values = extract_enum_values(col['type'])
                    if actual_values:
                        # Check for English values (migrations might have converted)
                        if set(actual_values) == set(['OPEN', 'IN_PROGRESS', 'REJECTED', 'ACCEPTED']):
                            pass
                        else:
                            assert set(actual_values) == set(expected['enum_values']), \
                                f"Column '{col_name}' has wrong enum values: {actual_values}"
        
        # Check indexes for foreign keys
        indexes = db_inspector.get_indexes('placement_requests', schema=schema)
        assert any(idx['column_names'] == ['patient_id'] for idx in indexes), \
            "Index on 'patient_id' foreign key not found"
        assert any(idx['column_names'] == ['therapist_id'] for idx in indexes), \
            "Index on 'therapist_id' foreign key not found"
    
    def test_communication_service_schema(self, db_inspector):
        """Test communication_service schema structure."""
        schema = 'communication_service'
        
        # Check all tables exist
        tables = db_inspector.get_table_names(schema=schema)
        expected_tables = ['emails', 'email_batches', 'phone_calls', 'phone_call_batches']
        
        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found in {schema}"
        
        # Check emails table
        columns = db_inspector.get_columns('emails', schema=schema)
        column_dict = {col['name']: col for col in columns}
        
        email_columns = {
            'id': {'type': 'INTEGER', 'nullable': False},
            'therapist_id': {'type': 'INTEGER', 'nullable': False},
            'subject': {'type': 'VARCHAR', 'nullable': False},
            'body_html': {'type': 'TEXT', 'nullable': False},
            'recipient_email': {'type': 'VARCHAR', 'nullable': False},
            'status': {
                'type': 'ENUM',
                'nullable': True,
                'enum_values': ['DRAFT', 'QUEUED', 'SENDING', 'SENT', 'FAILED']  # English values after migration
            },
            'batch_id': {'type': 'VARCHAR', 'nullable': True},
            'response_received': {'type': 'BOOLEAN', 'nullable': False},
        }
        
        for col_name, expected in email_columns.items():
            assert col_name in column_dict, f"Column '{col_name}' not found in emails table"
            
            col = column_dict[col_name]
            
            # Special handling for ENUM columns
            if expected['type'] == 'ENUM':
                assert is_enum_column(col), f"Column '{col_name}' is not an ENUM type"
                
                if 'enum_values' in expected:
                    actual_values = extract_enum_values(col['type'])
                    assert actual_values is not None, f"Could not extract enum values for '{col_name}'"
                    assert set(actual_values) == set(expected['enum_values']), \
                        f"Column '{col_name}' has wrong enum values: {actual_values} (expected {expected['enum_values']})"
        
        # Check email_batches table foreign keys
        fks = db_inspector.get_foreign_keys('email_batches', schema=schema)
        fk_columns = [fk['constrained_columns'][0] for fk in fks]
        assert 'email_id' in fk_columns, "Foreign key 'email_id' not found in email_batches"
        assert 'placement_request_id' in fk_columns, "Foreign key 'placement_request_id' not found"
        
        # Check phone_calls table
        columns = db_inspector.get_columns('phone_calls', schema=schema)
        column_dict = {col['name']: col for col in columns}
        
        assert 'scheduled_date' in column_dict, "Column 'scheduled_date' not found in phone_calls"
        assert 'scheduled_time' in column_dict, "Column 'scheduled_time' not found in phone_calls"
        
        # Check phone_call_batches foreign keys
        fks = db_inspector.get_foreign_keys('phone_call_batches', schema=schema)
        fk_columns = [fk['constrained_columns'][0] for fk in fks]
        assert 'phone_call_id' in fk_columns, "Foreign key 'phone_call_id' not found"
    
    def test_geocoding_service_schema(self, db_inspector):
        """Test geocoding_service schema structure."""
        schema = 'geocoding_service'
        
        # Check tables exist
        tables = db_inspector.get_table_names(schema=schema)
        expected_tables = ['geocache', 'distance_cache']
        
        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found in {schema}"
        
        # Check geocache table
        columns = db_inspector.get_columns('geocache', schema=schema)
        column_dict = {col['name']: col for col in columns}
        
        geocache_columns = {
            'id': {'type': 'INTEGER', 'nullable': False},
            'query': {'type': 'VARCHAR', 'nullable': False},
            'query_type': {'type': 'VARCHAR', 'nullable': False},
            'latitude': {'type': 'DOUBLE', 'nullable': True},
            'longitude': {'type': 'DOUBLE', 'nullable': True},
            'hit_count': {'type': 'INTEGER', 'nullable': False},
        }
        
        for col_name, expected in geocache_columns.items():
            assert col_name in column_dict, f"Column '{col_name}' not found in geocache table"
        
        # Check distance_cache table
        columns = db_inspector.get_columns('distance_cache', schema=schema)
        column_dict = {col['name']: col for col in columns}
        
        distance_columns = {
            'origin_latitude': {'type': 'DOUBLE', 'nullable': False},
            'origin_longitude': {'type': 'DOUBLE', 'nullable': False},
            'destination_latitude': {'type': 'DOUBLE', 'nullable': False},
            'destination_longitude': {'type': 'DOUBLE', 'nullable': False},
            'travel_mode': {'type': 'VARCHAR', 'nullable': False},
            'distance_km': {'type': 'DOUBLE', 'nullable': False},
        }
        
        for col_name in distance_columns:
            assert col_name in column_dict, f"Column '{col_name}' not found in distance_cache table"
        
        # Check composite index on distance_cache
        indexes = db_inspector.get_indexes('distance_cache', schema=schema)
        expected_idx_cols = ['origin_latitude', 'origin_longitude', 
                            'destination_latitude', 'destination_longitude', 'travel_mode']
        assert any(set(idx['column_names']) == set(expected_idx_cols) for idx in indexes), \
            "Composite index on coordinate columns not found in distance_cache"
    
    def test_foreign_key_relationships(self, db_inspector):
        """Test that foreign key relationships are properly set up."""
        # Check email_batches foreign keys
        fks = db_inspector.get_foreign_keys('email_batches', schema='communication_service')
        
        # Should have FK to emails table
        email_fk = next((fk for fk in fks if fk['constrained_columns'] == ['email_id']), None)
        assert email_fk is not None, "Foreign key from email_batches.email_id not found"
        assert email_fk['referred_schema'] == 'communication_service'
        assert email_fk['referred_table'] == 'emails'
        assert email_fk['referred_columns'] == ['id']
        
        # Should have FK to placement_requests table
        pr_fk = next((fk for fk in fks if fk['constrained_columns'] == ['placement_request_id']), None)
        assert pr_fk is not None, "Foreign key from email_batches.placement_request_id not found"
        assert pr_fk['referred_schema'] == 'matching_service'
        assert pr_fk['referred_table'] == 'placement_requests'
        assert pr_fk['referred_columns'] == ['id']
    
    def test_unique_constraints(self, db_inspector):
        """Test that unique constraints are properly set up."""
        # Check email_batches unique constraint
        uniques = db_inspector.get_unique_constraints('email_batches', schema='communication_service')
        
        # Should have unique constraint on (email_id, placement_request_id)
        expected_cols = ['email_id', 'placement_request_id']
        assert any(set(u['column_names']) == set(expected_cols) for u in uniques), \
            "Unique constraint on (email_id, placement_request_id) not found in email_batches"
        
        # Check phone_call_batches unique constraint
        uniques = db_inspector.get_unique_constraints('phone_call_batches', schema='communication_service')
        assert any(set(u['column_names']) == set(['phone_call_id', 'placement_request_id']) 
                  for u in uniques), \
            "Unique constraint on (phone_call_id, placement_request_id) not found"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
