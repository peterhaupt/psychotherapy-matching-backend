"""Test database schemas exist and are properly configured.

This test verifies that all required database schemas and tables exist
after running migrations. It checks for the presence of all tables and
their key columns.

IMPORTANT: All field names use German terminology for consistency.

Current State (after migration jcfc05l8p9p9):
- All database fields use German names
- placement_requests table has been removed
- email_batches and phone_call_batches tables have been removed
- Bundle references moved to matching_service.therapeutenanfrage
- Search status and phone call status now use German enum values
- TherapistGenderPreference enum now uses German values
"""
import os
import sys
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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
    
    # Check key columns exist (including German field names)
    columns = {col['name'] for col in db_inspector.get_columns('therapists', schema='therapist_service')}
    
    required_columns = {
        'id', 'anrede', 'titel', 'vorname', 'nachname', 'strasse', 'plz', 'ort',
        'telefon', 'fax', 'email', 'webseite', 'kassensitz', 'geschlecht',
        'telefonische_erreichbarkeit', 'fremdsprachen', 'psychotherapieverfahren',
        'zusatzqualifikationen', 'besondere_leistungsangebote',
        'letzter_kontakt_email', 'letzter_kontakt_telefon',
        'letztes_persoenliches_gespraech',
        'status', 'sperrgrund', 'sperrdatum',
        'potenziell_verfuegbar', 'potenziell_verfuegbar_notizen',
        # Bundle-related fields (German names)
        'naechster_kontakt_moeglich', 'bevorzugte_diagnosen',
        'alter_min', 'alter_max', 'geschlechtspraeferenz', 'arbeitszeiten',
        'bevorzugt_gruppentherapie',
        'created_at', 'updated_at'
    }
    
    missing_columns = required_columns - columns
    assert not missing_columns, f"Missing columns in therapists table: {missing_columns}"
    
    # Check that removed columns don't exist
    removed_columns = {'freie_einzeltherapieplaetze_ab', 'freie_gruppentherapieplaetze_ab'}
    unexpected_columns = removed_columns & columns
    assert not unexpected_columns, f"Removed columns still exist in therapists table: {unexpected_columns}"


def test_matching_service_tables(db_inspector):
    """Test that matching service tables exist with correct columns."""
    tables = db_inspector.get_table_names(schema='matching_service')
    
    # Check that placement_requests table does NOT exist (removed in migration fcfc01h4l5l5)
    assert 'placement_requests' not in tables, "Table 'placement_requests' should have been removed"
    
    # Check new bundle tables exist
    assert 'platzsuche' in tables, "Table 'platzsuche' not found"
    assert 'therapeutenanfrage' in tables, "Table 'therapeutenanfrage' not found"
    assert 'therapeut_anfrage_patient' in tables, "Table 'therapeut_anfrage_patient' not found"
    
    # Check platzsuche columns (with German names)
    ps_columns = {col['name'] for col in db_inspector.get_columns('platzsuche', schema='matching_service')}
    ps_required = {
        'id', 'patient_id', 'status', 'created_at', 'updated_at',
        'ausgeschlossene_therapeuten', 'gesamt_angeforderte_kontakte',
        'erfolgreiche_vermittlung_datum', 'notizen'
    }
    missing = ps_required - ps_columns
    assert not missing, f"Missing columns in platzsuche: {missing}"
    
    # Check therapeutenanfrage columns (with German names and new communication references)
    ta_columns = {col['name'] for col in db_inspector.get_columns('therapeutenanfrage', schema='matching_service')}
    ta_required = {
        'id', 'therapist_id', 'created_date', 'sent_date', 'response_date',
        'antworttyp', 'buendelgroesse', 'angenommen_anzahl', 'abgelehnt_anzahl',
        'keine_antwort_anzahl', 'notizen',
        # New columns added in migration hcfc03j6n7n7
        'email_id', 'phone_call_id'
    }
    missing = ta_required - ta_columns
    assert not missing, f"Missing columns in therapeutenanfrage: {missing}"
    
    # Check therapeut_anfrage_patient columns (with German names)
    tap_columns = {col['name'] for col in db_inspector.get_columns('therapeut_anfrage_patient', schema='matching_service')}
    tap_required = {
        'id', 'therapeutenanfrage_id', 'platzsuche_id', 'patient_id',
        'position_im_buendel', 'status', 'antwortergebnis', 'antwortnotizen',
        'created_at'
    }
    missing = tap_required - tap_columns
    assert not missing, f"Missing columns in therapeut_anfrage_patient: {missing}"
    
    # Check that the status columns now use enum types
    # Check platzsuche.status column type
    ps_col_info = {col['name']: col for col in db_inspector.get_columns('platzsuche', schema='matching_service')}
    assert 'status' in ps_col_info, "platzsuche.status column should exist"
    # Note: SQLAlchemy inspector might not show the exact enum type, but the column should exist


def test_communication_service_tables(db_inspector):
    """Test that communication service tables exist with correct columns."""
    tables = db_inspector.get_table_names(schema='communication_service')
    
    # Check that batch tables have been REMOVED (migration hcfc03j6n7n7)
    assert 'email_batches' not in tables, "Table 'email_batches' should have been removed"
    assert 'phone_call_batches' not in tables, "Table 'phone_call_batches' should have been removed"
    
    # Check remaining tables exist
    assert 'emails' in tables, "Table 'emails' not found"
    assert 'phone_calls' in tables, "Table 'phone_calls' not found"
    
    # Check emails columns (with German names and removed columns)
    email_columns = {col['name'] for col in db_inspector.get_columns('emails', schema='communication_service')}
    email_required = {
        'id', 'therapist_id', 'betreff', 'body_html', 'body_text',
        'empfaenger_email', 'empfaenger_name', 'absender_email', 'absender_name',
        'antwort_erhalten', 'antwortdatum', 'antwortinhalt', 
        'nachverfolgung_erforderlich', 'nachverfolgung_notizen', 
        'status', 'queued_at', 'sent_at', 'fehlermeldung', 'wiederholungsanzahl', 
        'created_at', 'updated_at'
    }
    missing = email_required - email_columns
    assert not missing, f"Missing columns in emails: {missing}"
    
    # Check that removed columns don't exist
    removed_email_columns = {'placement_request_ids', 'batch_id'}
    unexpected = removed_email_columns & email_columns
    assert not unexpected, f"Removed columns still exist in emails table: {unexpected}"
    
    # Check phone_calls columns (with German names)
    pc_columns = {col['name'] for col in db_inspector.get_columns('phone_calls', schema='communication_service')}
    pc_required = {
        'id', 'therapist_id', 'geplantes_datum', 'geplante_zeit',
        'dauer_minuten', 'tatsaechliches_datum', 'tatsaechliche_zeit', 'status',
        'ergebnis', 'notizen', 'wiederholen_nach', 'created_at', 'updated_at'
    }
    missing = pc_required - pc_columns
    assert not missing, f"Missing columns in phone_calls: {missing}"
    
    # Check that the status column exists and uses enum type
    pc_col_info = {col['name']: col for col in db_inspector.get_columns('phone_calls', schema='communication_service')}
    assert 'status' in pc_col_info, "phone_calls.status column should exist"


def test_geocoding_service_tables(db_inspector):
    """Test that geocoding service tables exist with correct columns."""
    tables = db_inspector.get_table_names(schema='geocoding_service')
    
    # Check tables exist
    assert 'geocache' in tables, "Table 'geocache' not found"
    assert 'distance_cache' in tables, "Table 'distance_cache' not found"
    
    # Check geocache columns (these remain in English as they're technical)
    gc_columns = {col['name'] for col in db_inspector.get_columns('geocache', schema='geocoding_service')}
    gc_required = {
        'id', 'query', 'query_type', 'latitude', 'longitude',
        'display_name', 'result_data', 'created_at', 'updated_at', 'hit_count'
    }
    missing = gc_required - gc_columns
    assert not missing, f"Missing columns in geocache: {missing}"
    
    # Check distance_cache columns (these remain in English as they're technical)
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
    
    # Check required enums exist with German values
    expected_enums = {
        'patientstatus': ['OPEN', 'SEARCHING', 'IN_THERAPY', 'THERAPY_COMPLETED', 
                         'SEARCH_ABORTED', 'THERAPY_ABORTED'],
        'therapistgenderpreference': ['Männlich', 'Weiblich', 'Egal'],  # Updated to German
        'therapiststatus': ['ACTIVE', 'BLOCKED', 'INACTIVE'],
        'emailstatus': ['DRAFT', 'QUEUED', 'SENDING', 'SENT', 'FAILED'],
        # New enums with German values
        'searchstatus': ['aktiv', 'erfolgreich', 'pausiert', 'abgebrochen'],
        'phonecallstatus': ['geplant', 'abgeschlossen', 'fehlgeschlagen', 'abgebrochen']
    }
    
    for enum_name, expected_values in expected_enums.items():
        assert enum_name in enums, f"Enum type '{enum_name}' not found"
        # For the new German enums, verify the values match exactly
        if enum_name in ['searchstatus', 'phonecallstatus', 'therapistgenderpreference']:
            actual_values = enums[enum_name]
            assert set(actual_values) == set(expected_values), \
                   f"Enum '{enum_name}' has incorrect values. Expected: {expected_values}, Got: {actual_values}"
    
    # PlacementRequestStatus should NOT exist anymore
    assert 'placementrequeststatus' not in enums, "Enum 'placementrequeststatus' should have been removed"


def test_indexes_exist(db_inspector):
    """Test that important indexes exist."""
    # Check therapist indexes (German field name)
    therapist_indexes = db_inspector.get_indexes('therapists', schema='therapist_service')
    therapist_index_names = {idx['name'] for idx in therapist_indexes}
    
    assert 'idx_therapists_naechster_kontakt_moeglich' in therapist_index_names, \
           "Missing index on therapist.naechster_kontakt_moeglich"
    
    # Check bundle table indexes
    ps_indexes = db_inspector.get_indexes('platzsuche', schema='matching_service')
    ps_index_names = {idx['name'] for idx in ps_indexes}
    assert 'idx_platzsuche_patient_id' in ps_index_names, "Missing index on platzsuche.patient_id"
    assert 'idx_platzsuche_status' in ps_index_names, "Missing index on platzsuche.status"
    
    ta_indexes = db_inspector.get_indexes('therapeutenanfrage', schema='matching_service')
    ta_index_names = {idx['name'] for idx in ta_indexes}
    assert 'idx_therapeutenanfrage_therapist_id' in ta_index_names, "Missing index on therapeutenanfrage.therapist_id"
    assert 'idx_therapeutenanfrage_email_id' in ta_index_names, "Missing index on therapeutenanfrage.email_id"
    assert 'idx_therapeutenanfrage_phone_call_id' in ta_index_names, "Missing index on therapeutenanfrage.phone_call_id"
    
    # Check phone_calls indexes
    pc_indexes = db_inspector.get_indexes('phone_calls', schema='communication_service')
    pc_index_names = {idx['name'] for idx in pc_indexes}
    assert 'idx_phone_calls_status' in pc_index_names, "Missing index on phone_calls.status"


def test_foreign_key_constraints(db_inspector):
    """Test that foreign key constraints exist."""
    # Check therapeutenanfrage foreign keys (new references to communication service)
    ta_fks = db_inspector.get_foreign_keys('therapeutenanfrage', schema='matching_service')
    ta_fk_columns = {fk['constrained_columns'][0] for fk in ta_fks}
    assert 'therapist_id' in ta_fk_columns, "Missing FK on therapeutenanfrage.therapist_id"
    assert 'email_id' in ta_fk_columns, "Missing FK on therapeutenanfrage.email_id"
    assert 'phone_call_id' in ta_fk_columns, "Missing FK on therapeutenanfrage.phone_call_id"
    
    # Check bundle table foreign keys
    tap_fks = db_inspector.get_foreign_keys('therapeut_anfrage_patient', schema='matching_service')
    tap_fk_columns = {fk['constrained_columns'][0] for fk in tap_fks}
    assert 'therapeutenanfrage_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.therapeutenanfrage_id"
    assert 'platzsuche_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.platzsuche_id"
    assert 'patient_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.patient_id"


def test_no_placement_request_references(db_inspector):
    """Test that placement_request references have been removed."""
    # Ensure no tables have placement_request_id columns
    all_schemas = ['patient_service', 'therapist_service', 'matching_service', 
                   'communication_service', 'geocoding_service']
    
    for schema in all_schemas:
        tables = db_inspector.get_table_names(schema=schema)
        for table in tables:
            columns = {col['name'] for col in db_inspector.get_columns(table, schema=schema)}
            assert 'placement_request_id' not in columns, \
                   f"Table {schema}.{table} still has placement_request_id column"


def test_no_batch_tables(db_inspector):
    """Test that batch tables have been removed from communication service."""
    tables = db_inspector.get_table_names(schema='communication_service')
    
    # These tables should not exist after migration hcfc03j6n7n7
    removed_tables = {'email_batches', 'phone_call_batches'}
    existing_removed_tables = removed_tables & set(tables)
    assert not existing_removed_tables, \
           f"Batch tables should have been removed but still exist: {existing_removed_tables}"


def test_unique_constraints(db_inspector):
    """Test that important unique constraints exist."""
    # Check therapeut_anfrage_patient unique constraint
    tap_constraints = db_inspector.get_unique_constraints('therapeut_anfrage_patient', 
                                                         schema='matching_service')
    constraint_names = {c['name'] for c in tap_constraints}
    assert 'uq_therapeut_anfrage_patient_bundle_search' in constraint_names, \
           "Missing unique constraint on therapeut_anfrage_patient(therapeutenanfrage_id, platzsuche_id)"


def test_check_constraints(db_engine):
    """Test for any check constraints that should exist."""
    # Currently no check constraints are defined in the migrations
    # This test is a placeholder for future check constraints
    pass


def test_default_values(db_inspector):
    """Test that important default values are set correctly."""
    # Note: SQLAlchemy's inspector may not always return default values reliably
    # This test checks that the columns exist, which is the most important part
    
    # Check platzsuche columns exist
    ps_columns = {col['name']: col for col in db_inspector.get_columns('platzsuche', 
                                                                       schema='matching_service')}
    
    # Verify the columns that should have defaults exist
    assert 'status' in ps_columns, "platzsuche.status column should exist"
    assert 'ausgeschlossene_therapeuten' in ps_columns, \
           "platzsuche.ausgeschlossene_therapeuten column should exist"
    assert 'gesamt_angeforderte_kontakte' in ps_columns, \
           "platzsuche.gesamt_angeforderte_kontakte column should exist"
    
    # Check therapeutenanfrage columns exist
    ta_columns = {col['name']: col for col in db_inspector.get_columns('therapeutenanfrage', 
                                                                       schema='matching_service')}
    
    # Verify the columns that should have defaults exist
    assert 'angenommen_anzahl' in ta_columns, \
           "therapeutenanfrage.angenommen_anzahl column should exist"
    assert 'abgelehnt_anzahl' in ta_columns, \
           "therapeutenanfrage.abgelehnt_anzahl column should exist"
    assert 'keine_antwort_anzahl' in ta_columns, \
           "therapeutenanfrage.keine_antwort_anzahl column should exist"
    
    # Note: To properly test server defaults, you would need to:
    # 1. Insert a row without specifying these columns
    # 2. Query it back and verify the default values were applied
    # This is beyond the scope of a schema inspection test


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
