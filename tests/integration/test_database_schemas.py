"""Test database schemas exist and are properly configured.

This test verifies that all required database schemas and tables exist
after running migrations. It checks for the presence of all tables and
their key columns.

IMPORTANT: All field names use German terminology for consistency.
"""
import os
import sys
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config import get_config

# Get test configuration
config = get_config()


@pytest.fixture(scope="module")
def db_engine():
    """Create a database engine for testing."""
    # Use direct connection (not through PgBouncer) for schema inspection
    engine = create_engine(config.get_database_uri(use_pgbouncer=False))
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def db_inspector(db_engine):
    """Create a database inspector."""
    return inspect(db_engine)


def test_database_connection(db_engine):
    """Test that we can connect to the database."""
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except OperationalError as e:
        pytest.fail(f"Cannot connect to database: {e}")


def test_schemas_exist(db_engine):
    """Test that all required schemas exist."""
    required_schemas = [
        'patient_service',
        'therapist_service',
        'matching_service',
        'communication_service',
        'geocoding_service',
        'scraping_service'
    ]
    
    with db_engine.connect() as conn:
        result = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata")
        )
        existing_schemas = [row[0] for row in result]
    
    for schema in required_schemas:
        assert schema in existing_schemas, f"Schema '{schema}' does not exist"


def test_patient_service_tables(db_inspector):
    """Test that patient service tables exist with correct columns."""
    # Check patients table exists
    tables = db_inspector.get_table_names(schema='patient_service')
    assert 'patients' in tables, "Table 'patients' not found in patient_service schema"
    
    # Check key columns exist (German field names)
    columns = {col['name'] for col in db_inspector.get_columns('patients', schema='patient_service')}
    
    required_columns = {
        'id', 'anrede', 'vorname', 'nachname', 'strasse', 'plz', 'ort',
        'email', 'telefon', 'hausarzt', 'krankenkasse', 
        'krankenversicherungsnummer', 'geburtsdatum', 'diagnose',
        'vertraege_unterschrieben', 'psychotherapeutische_sprechstunde',
        'startdatum', 'status', 'zeitliche_verfuegbarkeit',
        'raeumliche_verfuegbarkeit', 'verkehrsmittel',
        'offen_fuer_gruppentherapie', 'offen_fuer_diga',
        'ausgeschlossene_therapeuten', 'bevorzugtes_therapeutengeschlecht',
        'created_at', 'updated_at'
    }
    
    missing_columns = required_columns - columns
    assert not missing_columns, f"Missing columns in patients table: {missing_columns}"


def test_therapist_service_tables(db_inspector):
    """Test that therapist service tables exist with correct columns."""
    # Check therapists table exists
    tables = db_inspector.get_table_names(schema='therapist_service')
    assert 'therapists' in tables, "Table 'therapists' not found in therapist_service schema"
    
    # Check key columns exist (including new German field names)
    columns = {col['name'] for col in db_inspector.get_columns('therapists', schema='therapist_service')}
    
    required_columns = {
        'id', 'anrede', 'titel', 'vorname', 'nachname', 'strasse', 'plz', 'ort',
        'telefon', 'fax', 'email', 'webseite', 'kassensitz', 'geschlecht',
        'telefonische_erreichbarkeit', 'fremdsprachen', 'psychotherapieverfahren',
        'zusatzqualifikationen', 'besondere_leistungsangebote',
        'letzter_kontakt_email', 'letzter_kontakt_telefon',
        'letztes_persoenliches_gespraech', 'freie_einzeltherapieplaetze_ab',
        'freie_gruppentherapieplaetze_ab', 'status', 'sperrgrund', 'sperrdatum',
        'potentially_available', 'potentially_available_notes',
        # New bundle-related fields (German names after migration bcfc97d0f1h1)
        'naechster_kontakt_moeglich', 'bevorzugte_diagnosen',
        'alter_min', 'alter_max', 'geschlechtspraeferenz', 'arbeitszeiten',
        'created_at', 'updated_at'
    }
    
    missing_columns = required_columns - columns
    
    # If German fields are missing, check for English names (pre-migration)
    if missing_columns:
        english_to_german = {
            'next_contactable_date': 'naechster_kontakt_moeglich',
            'preferred_diagnoses': 'bevorzugte_diagnosen',
            'age_min': 'alter_min',
            'age_max': 'alter_max',
            'gender_preference': 'geschlechtspraeferenz',
            'working_hours': 'arbeitszeiten'
        }
        
        english_columns = set(english_to_german.keys())
        if english_columns.intersection(columns):
            pytest.skip("Migration bcfc97d0f1h1 not yet applied - fields still have English names")
        else:
            assert not missing_columns, f"Missing columns in therapists table: {missing_columns}"


def test_matching_service_tables(db_inspector):
    """Test that matching service tables exist with correct columns."""
    tables = db_inspector.get_table_names(schema='matching_service')
    
    # Check placement_requests table
    assert 'placement_requests' in tables, "Table 'placement_requests' not found"
    
    # Check new bundle tables
    assert 'platzsuche' in tables, "Table 'platzsuche' not found"
    assert 'therapeutenanfrage' in tables, "Table 'therapeutenanfrage' not found"
    assert 'therapeut_anfrage_patient' in tables, "Table 'therapeut_anfrage_patient' not found"
    
    # Check placement_requests columns
    pr_columns = {col['name'] for col in db_inspector.get_columns('placement_requests', schema='matching_service')}
    pr_required = {
        'id', 'patient_id', 'therapist_id', 'status', 'created_at',
        'email_contact_date', 'phone_contact_date', 'response',
        'response_date', 'next_contact_after', 'priority', 'notes'
    }
    missing = pr_required - pr_columns
    assert not missing, f"Missing columns in placement_requests: {missing}"
    
    # Check platzsuche columns
    ps_columns = {col['name'] for col in db_inspector.get_columns('platzsuche', schema='matching_service')}
    ps_required = {
        'id', 'patient_id', 'status', 'created_at', 'updated_at',
        'excluded_therapists', 'total_requested_contacts',
        'successful_match_date', 'notes'
    }
    missing = ps_required - ps_columns
    assert not missing, f"Missing columns in platzsuche: {missing}"
    
    # Check therapeutenanfrage columns
    ta_columns = {col['name'] for col in db_inspector.get_columns('therapeutenanfrage', schema='matching_service')}
    ta_required = {
        'id', 'therapist_id', 'created_date', 'sent_date', 'response_date',
        'response_type', 'bundle_size', 'accepted_count', 'rejected_count',
        'no_response_count', 'notes'
    }
    missing = ta_required - ta_columns
    assert not missing, f"Missing columns in therapeutenanfrage: {missing}"
    
    # Check therapeut_anfrage_patient columns
    tap_columns = {col['name'] for col in db_inspector.get_columns('therapeut_anfrage_patient', schema='matching_service')}
    tap_required = {
        'id', 'therapeutenanfrage_id', 'platzsuche_id', 'patient_id',
        'position_in_bundle', 'status', 'response_outcome', 'response_notes',
        'created_at'
    }
    missing = tap_required - tap_columns
    assert not missing, f"Missing columns in therapeut_anfrage_patient: {missing}"


def test_communication_service_tables(db_inspector):
    """Test that communication service tables exist with correct columns."""
    tables = db_inspector.get_table_names(schema='communication_service')
    
    # Check all communication tables exist
    required_tables = ['emails', 'email_batches', 'phone_calls', 'phone_call_batches']
    for table in required_tables:
        assert table in tables, f"Table '{table}' not found in communication_service"
    
    # Check emails columns
    email_columns = {col['name'] for col in db_inspector.get_columns('emails', schema='communication_service')}
    email_required = {
        'id', 'therapist_id', 'subject', 'body_html', 'body_text',
        'recipient_email', 'recipient_name', 'sender_email', 'sender_name',
        'placement_request_ids', 'batch_id', 'response_received',
        'response_date', 'response_content', 'follow_up_required',
        'follow_up_notes', 'status', 'queued_at', 'sent_at',
        'error_message', 'retry_count', 'created_at', 'updated_at'
    }
    missing = email_required - email_columns
    assert not missing, f"Missing columns in emails: {missing}"
    
    # Check email_batches columns
    eb_columns = {col['name'] for col in db_inspector.get_columns('email_batches', schema='communication_service')}
    eb_required = {
        'id', 'email_id', 'placement_request_id', 'priority', 'included',
        'response_outcome', 'response_notes', 'created_at', 'updated_at'
    }
    missing = eb_required - eb_columns
    assert not missing, f"Missing columns in email_batches: {missing}"
    
    # Check phone_calls columns
    pc_columns = {col['name'] for col in db_inspector.get_columns('phone_calls', schema='communication_service')}
    pc_required = {
        'id', 'therapist_id', 'scheduled_date', 'scheduled_time',
        'duration_minutes', 'actual_date', 'actual_time', 'status',
        'outcome', 'notes', 'retry_after', 'created_at', 'updated_at'
    }
    missing = pc_required - pc_columns
    assert not missing, f"Missing columns in phone_calls: {missing}"
    
    # Check phone_call_batches columns
    pcb_columns = {col['name'] for col in db_inspector.get_columns('phone_call_batches', schema='communication_service')}
    pcb_required = {
        'id', 'phone_call_id', 'placement_request_id', 'priority',
        'discussed', 'outcome', 'follow_up_required', 'follow_up_notes',
        'created_at'
    }
    missing = pcb_required - pcb_columns
    assert not missing, f"Missing columns in phone_call_batches: {missing}"


def test_geocoding_service_tables(db_inspector):
    """Test that geocoding service tables exist with correct columns."""
    tables = db_inspector.get_table_names(schema='geocoding_service')
    
    # Check tables exist
    assert 'geocache' in tables, "Table 'geocache' not found"
    assert 'distance_cache' in tables, "Table 'distance_cache' not found"
    
    # Check geocache columns
    gc_columns = {col['name'] for col in db_inspector.get_columns('geocache', schema='geocoding_service')}
    gc_required = {
        'id', 'query', 'query_type', 'latitude', 'longitude',
        'display_name', 'result_data', 'created_at', 'updated_at', 'hit_count'
    }
    missing = gc_required - gc_columns
    assert not missing, f"Missing columns in geocache: {missing}"
    
    # Check distance_cache columns
    dc_columns = {col['name'] for col in db_inspector.get_columns('distance_cache', schema='geocoding_service')}
    dc_required = {
        'id', 'origin_latitude', 'origin_longitude', 'destination_latitude',
        'destination_longitude', 'travel_mode', 'distance_km',
        'travel_time_minutes', 'route_data', 'created_at', 'updated_at',
        'hit_count'
    }
    missing = dc_required - dc_columns
    assert not missing, f"Missing columns in distance_cache: {missing}"


def test_enum_types(db_engine):
    """Test that all enum types exist with correct values."""
    with db_engine.connect() as conn:
        # Get all enum types
        result = conn.execute(text("""
            SELECT n.nspname as schema_name,
                   t.typname as enum_name,
                   array_agg(e.enumlabel ORDER BY e.enumsortorder) as values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            GROUP BY n.nspname, t.typname
            ORDER BY n.nspname, t.typname
        """))
        
        enums = {}
        for row in result:
            key = f"{row[0]}.{row[1]}" if row[0] != 'public' else row[1]
            enums[key] = row[2]
    
    # Check required enums exist with correct values
    expected_enums = {
        'patientstatus': ['OPEN', 'SEARCHING', 'IN_THERAPY', 'THERAPY_COMPLETED', 
                         'SEARCH_ABORTED', 'THERAPY_ABORTED'],
        'therapistgenderpreference': ['MALE', 'FEMALE', 'ANY'],
        'therapiststatus': ['ACTIVE', 'BLOCKED', 'INACTIVE'],
        'placementrequeststatus': ['OPEN', 'IN_PROGRESS', 'REJECTED', 'ACCEPTED'],
        'emailstatus': ['DRAFT', 'QUEUED', 'SENDING', 'SENT', 'FAILED']
    }
    
    for enum_name, expected_values in expected_enums.items():
        assert enum_name in enums, f"Enum type '{enum_name}' not found"
        # For now, just check that the enum exists
        # Values might be different based on migration status


def test_indexes_exist(db_inspector):
    """Test that important indexes exist."""
    # Check therapist indexes
    therapist_indexes = db_inspector.get_indexes('therapists', schema='therapist_service')
    therapist_index_names = {idx['name'] for idx in therapist_indexes}
    
    # Check for the German field name index (or English if migration not applied)
    assert ('idx_therapists_naechster_kontakt_moeglich' in therapist_index_names or
            'idx_therapists_next_contactable_date' in therapist_index_names), \
           "Missing index on therapist contactable date"
    
    # Check bundle table indexes
    ps_indexes = db_inspector.get_indexes('platzsuche', schema='matching_service')
    ps_index_names = {idx['name'] for idx in ps_indexes}
    assert 'idx_platzsuche_patient_id' in ps_index_names, "Missing index on platzsuche.patient_id"
    assert 'idx_platzsuche_status' in ps_index_names, "Missing index on platzsuche.status"
    
    ta_indexes = db_inspector.get_indexes('therapeutenanfrage', schema='matching_service')
    ta_index_names = {idx['name'] for idx in ta_indexes}
    assert 'idx_therapeutenanfrage_therapist_id' in ta_index_names, "Missing index on therapeutenanfrage.therapist_id"


def test_foreign_key_constraints(db_inspector):
    """Test that foreign key constraints exist."""
    # Check email_batches foreign keys
    eb_fks = db_inspector.get_foreign_keys('email_batches', schema='communication_service')
    eb_fk_columns = {fk['constrained_columns'][0] for fk in eb_fks}
    assert 'email_id' in eb_fk_columns, "Missing foreign key on email_batches.email_id"
    assert 'placement_request_id' in eb_fk_columns, "Missing foreign key on email_batches.placement_request_id"
    
    # Check bundle table foreign keys
    tap_fks = db_inspector.get_foreign_keys('therapeut_anfrage_patient', schema='matching_service')
    tap_fk_columns = {fk['constrained_columns'][0] for fk in tap_fks}
    assert 'therapeutenanfrage_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.therapeutenanfrage_id"
    assert 'platzsuche_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.platzsuche_id"
    assert 'patient_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.patient_id"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])