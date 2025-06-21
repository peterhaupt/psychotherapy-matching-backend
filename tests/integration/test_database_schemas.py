"""Test database schemas exist and are properly configured.

This test verifies that all required database schemas and tables exist
after running migrations. It checks for the presence of all tables and
their key columns.

IMPORTANT: All field names use German terminology for consistency.

Current State (after Phase 2 migration):
- All database table names use German names (patienten, therapeuten, telefonanrufe)
- All database fields use German names
- All enum types use German names
- All enum values use German values
- placement_requests table has been removed
- email_batches and phone_call_batches tables have been removed
- Bundle references renamed to anfrage/inquiry (Phase 2)
- Email/phone call tables support both therapist AND patient recipients
- nachverfolgung_erforderlich and nachverfolgung_notizen removed from emails table
- wiederholen_nach removed from telefonanrufe table
- New patient preference fields added (Phase 2)
- New therapist field for Curavani awareness added (Phase 2)
- Patient therapist age preferences removed
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
    """Test that patient service tables exist with correct columns including Phase 2 additions."""
    # Check patienten table exists (German name)
    tables = db_inspector.get_table_names(schema='patient_service')
    assert 'patienten' in tables, "Table 'patienten' not found in patient_service schema"
    
    # Ensure old table name doesn't exist
    assert 'patients' not in tables, "Old table name 'patients' should not exist"
    
    # Check key columns exist (German field names)
    columns = {col['name'] for col in db_inspector.get_columns('patienten', schema='patient_service')}
    
    required_columns = {
        'id', 'anrede', 'vorname', 'nachname', 'strasse', 'plz', 'ort',
        'email', 'telefon', 'hausarzt', 'krankenkasse', 
        'krankenversicherungsnummer', 'geburtsdatum', 'diagnose',
        # NEW Phase 2 fields
        'symptome', 'erfahrung_mit_psychotherapie',
        'bevorzugtes_therapieverfahren',
        # REMOVED: bevorzugtes_therapeutenalter_min and bevorzugtes_therapeutenalter_max
        # End NEW Phase 2 fields
        'vertraege_unterschrieben', 'psychotherapeutische_sprechstunde',
        'startdatum', 'status', 'zeitliche_verfuegbarkeit',
        'raeumliche_verfuegbarkeit', 'verkehrsmittel',
        'offen_fuer_gruppentherapie', 'offen_fuer_diga',
        'ausgeschlossene_therapeuten', 'bevorzugtes_therapeutengeschlecht',
        'created_at', 'updated_at', 'letzter_kontakt'
    }
    
    missing_columns = required_columns - columns
    assert not missing_columns, f"Missing columns in patienten table: {missing_columns}"
    
    # Check bevorzugtes_therapieverfahren is an ARRAY type
    for col in db_inspector.get_columns('patienten', schema='patient_service'):
        if col['name'] == 'bevorzugtes_therapieverfahren':
            assert 'ARRAY' in str(col['type']), \
                f"bevorzugtes_therapieverfahren should be ARRAY type, got: {col['type']}"
    
    # Verify removed columns don't exist
    removed_columns = {'bevorzugtes_therapeutenalter_min', 'bevorzugtes_therapeutenalter_max'}
    unexpected_columns = removed_columns & columns
    assert not unexpected_columns, f"Removed columns still exist in patienten table: {unexpected_columns}"


def test_therapist_service_tables(db_inspector):
    """Test that therapist service tables exist with correct columns including Phase 2 addition."""
    # Check therapeuten table exists (German name)
    tables = db_inspector.get_table_names(schema='therapist_service')
    assert 'therapeuten' in tables, "Table 'therapeuten' not found in therapist_service schema"
    
    # Ensure old table name doesn't exist
    assert 'therapists' not in tables, "Old table name 'therapists' should not exist"
    
    # Check key columns exist (including German field names)
    columns = {col['name'] for col in db_inspector.get_columns('therapeuten', schema='therapist_service')}
    
    required_columns = {
        'id', 'anrede', 'titel', 'vorname', 'nachname', 'strasse', 'plz', 'ort',
        'telefon', 'fax', 'email', 'webseite', 'kassensitz', 'geschlecht',
        'telefonische_erreichbarkeit', 'fremdsprachen', 'psychotherapieverfahren',
        'zusatzqualifikationen', 'besondere_leistungsangebote',
        'letzter_kontakt_email', 'letzter_kontakt_telefon',
        'letztes_persoenliches_gespraech',
        'status', 'sperrgrund', 'sperrdatum',
        'potenziell_verfuegbar', 'potenziell_verfuegbar_notizen',
        # NEW Phase 2 field
        'ueber_curavani_informiert',
        # Inquiry-related fields (German names)
        'naechster_kontakt_moeglich', 'bevorzugte_diagnosen',
        'alter_min', 'alter_max', 'geschlechtspraeferenz', 'arbeitszeiten',
        'bevorzugt_gruppentherapie',
        'created_at', 'updated_at'
    }
    
    missing_columns = required_columns - columns
    assert not missing_columns, f"Missing columns in therapeuten table: {missing_columns}"
    
    # Check that removed columns don't exist
    removed_columns = {'freie_einzeltherapieplaetze_ab', 'freie_gruppentherapieplaetze_ab'}
    unexpected_columns = removed_columns & columns
    assert not unexpected_columns, f"Removed columns still exist in therapeuten table: {unexpected_columns}"


def test_matching_service_tables(db_inspector):
    """Test that matching service tables exist with correct columns including Phase 2 renames."""
    tables = db_inspector.get_table_names(schema='matching_service')
    
    # Check that placement_requests table does NOT exist (removed in migration)
    assert 'placement_requests' not in tables, "Table 'placement_requests' should have been removed"
    
    # Check new inquiry tables exist
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
    
    # Check therapeutenanfrage columns (with German names and Phase 2 rename)
    ta_columns = {col['name'] for col in db_inspector.get_columns('therapeutenanfrage', schema='matching_service')}
    ta_required = {
        'id', 'therapist_id', 'erstellt_datum', 'gesendet_datum', 'antwort_datum',  # German column names
        'antworttyp', 
        'anfragegroesse',  # RENAMED from buendelgroesse (Phase 2)
        'angenommen_anzahl', 'abgelehnt_anzahl',
        'keine_antwort_anzahl', 'notizen',
        # Communication references
        'email_id', 'phone_call_id'
    }
    missing = ta_required - ta_columns
    assert not missing, f"Missing columns in therapeutenanfrage: {missing}"
    
    # Check that old column names don't exist
    old_column_names = {'buendelgroesse', 'created_date', 'sent_date', 'response_date'}
    unexpected = old_column_names & ta_columns
    assert not unexpected, f"Old column names still exist in therapeutenanfrage: {unexpected}"
    
    # Check therapeut_anfrage_patient columns (with German names and Phase 2 rename)
    tap_columns = {col['name'] for col in db_inspector.get_columns('therapeut_anfrage_patient', schema='matching_service')}
    tap_required = {
        'id', 'therapeutenanfrage_id', 'platzsuche_id', 'patient_id',
        'position_in_anfrage',  # RENAMED from position_im_buendel (Phase 2)
        'status', 'antwortergebnis', 'antwortnotizen',
        'created_at'
    }
    missing = tap_required - tap_columns
    assert not missing, f"Missing columns in therapeut_anfrage_patient: {missing}"
    
    # Check that old column name doesn't exist
    assert 'position_im_buendel' not in tap_columns, \
        "Old column name 'position_im_buendel' should have been renamed to 'position_in_anfrage'"


def test_communication_service_tables(db_inspector):
    """Test that communication service tables exist with correct columns."""
    tables = db_inspector.get_table_names(schema='communication_service')
    
    # Check that batch tables have been REMOVED
    assert 'email_batches' not in tables, "Table 'email_batches' should have been removed"
    assert 'phone_call_batches' not in tables, "Table 'phone_call_batches' should have been removed"
    
    # Check remaining tables exist
    assert 'emails' in tables, "Table 'emails' not found"
    assert 'telefonanrufe' in tables, "Table 'telefonanrufe' not found"  # German name
    
    # Ensure old table name doesn't exist
    assert 'phone_calls' not in tables, "Old table name 'phone_calls' should not exist"
    
    # Check emails columns (with German names and Phase 1 removed columns)
    email_columns = {col['name'] for col in db_inspector.get_columns('emails', schema='communication_service')}
    email_required = {
        'id', 'therapist_id', 'patient_id', 'betreff', 'inhalt_html', 'inhalt_text',  # Now includes patient_id
        'empfaenger_email', 'empfaenger_name', 'absender_email', 'absender_name',
        'antwort_erhalten', 'antwortdatum', 'antwortinhalt', 
        # REMOVED: 'nachverfolgung_erforderlich', 'nachverfolgung_notizen' (Phase 1 changes)
        'status', 'in_warteschlange_am', 'gesendet_am', 'fehlermeldung', 'wiederholungsanzahl',
        'created_at', 'updated_at'
    }
    missing = email_required - email_columns
    assert not missing, f"Missing columns in emails: {missing}"
    
    # Check that removed columns don't exist
    removed_email_columns = {
        'nachverfolgung_erforderlich', 'nachverfolgung_notizen',  # Phase 1 removals
        'placement_request_ids', 'batch_id'  # Earlier removals
    }
    unexpected = removed_email_columns & email_columns
    assert not unexpected, f"Removed columns still exist in emails table: {unexpected}"
    
    # Check that old English column names don't exist
    old_english_columns = {'body_html', 'body_text', 'queued_at', 'sent_at'}
    unexpected = old_english_columns & email_columns
    assert not unexpected, f"Old English column names still exist in emails table: {unexpected}"
    
    # Check telefonanrufe columns (with German names and Phase 1 removed columns)
    pc_columns = {col['name'] for col in db_inspector.get_columns('telefonanrufe', schema='communication_service')}
    pc_required = {
        'id', 'therapist_id', 'patient_id', 'geplantes_datum', 'geplante_zeit',  # Now includes patient_id
        'dauer_minuten', 'tatsaechliches_datum', 'tatsaechliche_zeit', 'status',
        'ergebnis', 'notizen', 
        # REMOVED: 'wiederholen_nach' (Phase 1 change)
        'created_at', 'updated_at'
    }
    missing = pc_required - pc_columns
    assert not missing, f"Missing columns in telefonanrufe: {missing}"
    
    # Check that removed columns don't exist
    removed_phone_columns = {'wiederholen_nach'}  # Phase 1 removal
    unexpected = removed_phone_columns & pc_columns
    assert not unexpected, f"Removed columns still exist in telefonanrufe table: {unexpected}"


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
    """Test that all enum types exist with correct German values including Phase 2 additions."""
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
    
    # Check required enums exist with German names and values
    expected_enums = {
        # Updated German enum names and values
        'patientenstatus': ['offen', 'auf_der_Suche', 'in_Therapie', 
                           'Therapie_abgeschlossen', 'Suche_abgebrochen', 'Therapie_abgebrochen'],
        'therapeutgeschlechtspraeferenz': ['Männlich', 'Weiblich', 'Egal'],
        # NEW Phase 2 enum
        'therapieverfahren': ['egal', 'Verhaltenstherapie', 'tiefenpsychologisch_fundierte_Psychotherapie'],
        'therapeutstatus': ['aktiv', 'gesperrt', 'inaktiv'],
        'emailstatus': ['Entwurf', 'In_Warteschlange', 'Wird_gesendet', 'Gesendet', 'Fehlgeschlagen'],
        'suchstatus': ['aktiv', 'erfolgreich', 'pausiert', 'abgebrochen'],
        'telefonanrufstatus': ['geplant', 'abgeschlossen', 'fehlgeschlagen', 'abgebrochen'],
        'antworttyp': ['vollstaendige_Annahme', 'teilweise_Annahme', 'vollstaendige_Ablehnung', 'keine_Antwort'],
        'patientenergebnis': ['angenommen', 'abgelehnt_Kapazitaet', 'abgelehnt_nicht_geeignet', 
                             'abgelehnt_sonstiges', 'nicht_erschienen', 'in_Sitzungen'],
        # RENAMED from buendel_patient_status (Phase 2)
        'anfrage_patient_status': ['anstehend', 'angenommen', 'abgelehnt', 'keine_antwort']
    }
    
    for enum_name, expected_values in expected_enums.items():
        assert enum_name in enums, f"Enum type '{enum_name}' not found. Available enums: {list(enums.keys())}"
        actual_values = enums[enum_name]
        assert set(actual_values) == set(expected_values), \
               f"Enum '{enum_name}' has incorrect values. Expected: {expected_values}, Got: {actual_values}"
    
    # Old enum names should NOT exist anymore
    old_enum_names = [
        'patientstatus',  # Should be patientenstatus
        'therapiststatus',  # Should be therapeutstatus  
        'therapistgenderpreference',  # Should be therapeutgeschlechtspraeferenz
        'searchstatus',  # Should be suchstatus
        'phonecallstatus',  # Should be telefonanrufstatus
        'placementrequeststatus',  # Should not exist at all
        'responsetype',  # Should be antworttyp
        'patientoutcome',  # Should be patientenergebnis
        'buendel_patient_status'  # Should be anfrage_patient_status (Phase 2)
    ]
    
    for old_name in old_enum_names:
        assert old_name not in enums, f"Old enum name '{old_name}' should have been renamed or removed"


def test_indexes_exist(db_inspector):
    """Test that important indexes exist with updated names."""
    # Check therapeuten indexes (German table and field names)
    therapeuten_indexes = db_inspector.get_indexes('therapeuten', schema='therapist_service')
    therapeuten_index_names = {idx['name'] for idx in therapeuten_indexes}
    
    assert 'idx_therapists_naechster_kontakt_moeglich' in therapeuten_index_names, \
           "Missing index on therapeuten.naechster_kontakt_moeglich"
    
    # Check inquiry table indexes
    ps_indexes = db_inspector.get_indexes('platzsuche', schema='matching_service')
    ps_index_names = {idx['name'] for idx in ps_indexes}
    assert 'idx_platzsuche_patient_id' in ps_index_names, "Missing index on platzsuche.patient_id"
    assert 'idx_platzsuche_status' in ps_index_names, "Missing index on platzsuche.status"
    
    ta_indexes = db_inspector.get_indexes('therapeutenanfrage', schema='matching_service')
    ta_index_names = {idx['name'] for idx in ta_indexes}
    assert 'idx_therapeutenanfrage_therapist_id' in ta_index_names, "Missing index on therapeutenanfrage.therapist_id"
    assert 'idx_therapeutenanfrage_email_id' in ta_index_names, "Missing index on therapeutenanfrage.email_id"
    assert 'idx_therapeutenanfrage_phone_call_id' in ta_index_names, "Missing index on therapeutenanfrage.phone_call_id"
    
    # Check telefonanrufe indexes (German table name)
    pc_indexes = db_inspector.get_indexes('telefonanrufe', schema='communication_service')
    pc_index_names = {idx['name'] for idx in pc_indexes}
    assert 'idx_phone_calls_status' in pc_index_names, "Missing index on telefonanrufe.status"


def test_foreign_key_constraints(db_inspector):
    """Test that foreign key constraints exist with updated table references."""
    # Check therapeutenanfrage foreign keys (new references to communication service)
    ta_fks = db_inspector.get_foreign_keys('therapeutenanfrage', schema='matching_service')
    ta_fk_columns = {fk['constrained_columns'][0] for fk in ta_fks}
    assert 'therapist_id' in ta_fk_columns, "Missing FK on therapeutenanfrage.therapist_id"
    assert 'email_id' in ta_fk_columns, "Missing FK on therapeutenanfrage.email_id"
    assert 'phone_call_id' in ta_fk_columns, "Missing FK on therapeutenanfrage.phone_call_id"
    
    # Verify the foreign keys point to the correct renamed tables
    for fk in ta_fks:
        if fk['constrained_columns'][0] == 'therapist_id':
            # Should reference therapeuten table (German name)
            assert 'therapeuten' in fk['referred_table'], f"therapist_id should reference therapeuten table, got: {fk['referred_table']}"
        elif fk['constrained_columns'][0] == 'phone_call_id':
            # Should reference telefonanrufe table (German name)
            assert 'telefonanrufe' in fk['referred_table'], f"phone_call_id should reference telefonanrufe table, got: {fk['referred_table']}"
    
    # Check inquiry table foreign keys
    tap_fks = db_inspector.get_foreign_keys('therapeut_anfrage_patient', schema='matching_service')
    tap_fk_columns = {fk['constrained_columns'][0] for fk in tap_fks}
    assert 'therapeutenanfrage_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.therapeutenanfrage_id"
    assert 'platzsuche_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.platzsuche_id"
    assert 'patient_id' in tap_fk_columns, "Missing FK on therapeut_anfrage_patient.patient_id"
    
    # Verify patient_id references the renamed patienten table
    for fk in tap_fks:
        if fk['constrained_columns'][0] == 'patient_id':
            assert 'patienten' in fk['referred_table'], f"patient_id should reference patienten table, got: {fk['referred_table']}"


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
    
    # These tables should not exist after migration
    removed_tables = {'email_batches', 'phone_call_batches'}
    existing_removed_tables = removed_tables & set(tables)
    assert not existing_removed_tables, \
           f"Batch tables should have been removed but still exist: {existing_removed_tables}"


def test_no_old_table_names(db_inspector):
    """Test that old English table names don't exist."""
    schemas_and_old_tables = [
        ('patient_service', 'patients'),
        ('therapist_service', 'therapists'),
        ('communication_service', 'phone_calls')
    ]
    
    for schema, old_table in schemas_and_old_tables:
        tables = db_inspector.get_table_names(schema=schema)
        assert old_table not in tables, f"Old table name '{old_table}' should not exist in {schema}"


def test_unique_constraints(db_inspector):
    """Test that important unique constraints exist with Phase 2 renamed constraints."""
    # Check therapeut_anfrage_patient unique constraint (renamed in Phase 2)
    tap_constraints = db_inspector.get_unique_constraints('therapeut_anfrage_patient', 
                                                         schema='matching_service')
    constraint_names = {c['name'] for c in tap_constraints}
    assert 'uq_therapeut_anfrage_patient_anfrage_search' in constraint_names, \
           "Missing renamed unique constraint on therapeut_anfrage_patient(therapeutenanfrage_id, platzsuche_id)"
    
    # Old constraint name should not exist
    assert 'uq_therapeut_anfrage_patient_bundle_search' not in constraint_names, \
           "Old constraint name 'uq_therapeut_anfrage_patient_bundle_search' should have been renamed"


def test_check_constraints(db_engine):
    """Test for check constraints on tables including Phase 2 renamed constraints."""
    with db_engine.connect() as conn:
        # Check email recipient constraint
        email_constraints_query = text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conrelid = 'communication_service.emails'::regclass 
            AND contype = 'c'
        """)
        result = conn.execute(email_constraints_query)
        constraint_names = [row[0] for row in result]
        
        assert 'email_recipient_check' in constraint_names, \
            "Missing check constraint 'email_recipient_check' on emails table"
        
        # Check phone call recipient constraint
        phone_constraints_query = text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conrelid = 'communication_service.telefonanrufe'::regclass 
            AND contype = 'c'
        """)
        result = conn.execute(phone_constraints_query)
        constraint_names = [row[0] for row in result]
        
        assert 'phone_call_recipient_check' in constraint_names, \
            "Missing check constraint 'phone_call_recipient_check' on telefonanrufe table"
        
        # Check therapeutenanfrage constraints (Phase 2 renamed)
        ta_constraints_query = text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conrelid = 'matching_service.therapeutenanfrage'::regclass 
            AND contype = 'c'
        """)
        result = conn.execute(ta_constraints_query)
        constraint_names = [row[0] for row in result]
        
        assert 'anfrage_size_check' in constraint_names, \
            "Missing renamed check constraint 'anfrage_size_check' on therapeutenanfrage table"
        
        # Old constraint name should not exist
        assert 'bundle_size_check' not in constraint_names, \
            "Old constraint name 'bundle_size_check' should have been renamed"


def test_primary_key_constraints(db_inspector):
    """Test that primary keys exist on renamed tables."""
    tables_to_check = [
        ('patient_service', 'patienten'),
        ('therapist_service', 'therapeuten'),
        ('communication_service', 'telefonanrufe'),
        ('matching_service', 'platzsuche'),
        ('matching_service', 'therapeutenanfrage'),
        ('matching_service', 'therapeut_anfrage_patient')
    ]
    
    for schema, table in tables_to_check:
        pk = db_inspector.get_pk_constraint(table, schema=schema)
        assert pk['constrained_columns'], f"Missing primary key on {schema}.{table}"
        assert 'id' in pk['constrained_columns'], f"Primary key should be 'id' on {schema}.{table}"


def test_table_comments_updated(db_engine):
    """Test that table comments reference German names if they exist."""
    # This is optional - comments may not exist
    # Just verify that if comments exist, they don't reference old English names
    with db_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT schemaname, tablename, obj_description(c.oid) as comment
            FROM pg_tables pt
            JOIN pg_class c ON c.relname = pt.tablename
            JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = pt.schemaname
            WHERE schemaname IN ('patient_service', 'therapist_service', 'communication_service')
            AND obj_description(c.oid) IS NOT NULL
        """))
        
        for row in result:
            comment = row[2] or ""
            # Check that comments don't reference old English table names or bundle
            old_names = ['patients', 'therapists', 'phone_calls', 'bundle']
            for old_name in old_names:
                assert old_name not in comment.lower(), \
                       f"Table comment for {row[0]}.{row[1]} still references old term '{old_name}': {comment}"


def test_sample_data_integrity(db_engine):
    """Test that any existing data survived the migration."""
    # This test checks that basic table operations work on the renamed tables
    with db_engine.connect() as conn:
        # Test basic SELECT operations on renamed tables
        try:
            # Test patienten table
            result = conn.execute(text("SELECT COUNT(*) FROM patient_service.patienten"))
            patient_count = result.scalar()
            assert patient_count >= 0, "Should be able to query patienten table"
            
            # Test therapeuten table
            result = conn.execute(text("SELECT COUNT(*) FROM therapist_service.therapeuten"))
            therapist_count = result.scalar()
            assert therapist_count >= 0, "Should be able to query therapeuten table"
            
            # Test telefonanrufe table
            result = conn.execute(text("SELECT COUNT(*) FROM communication_service.telefonanrufe"))
            phone_count = result.scalar()
            assert phone_count >= 0, "Should be able to query telefonanrufe table"
            
        except Exception as e:
            pytest.fail(f"Failed to query renamed tables: {e}")


def test_communication_service_patient_support(db_inspector):
    """Test that communication service tables support patient communication."""
    # Check emails table has nullable therapist_id and patient_id
    email_columns = db_inspector.get_columns('emails', schema='communication_service')
    
    therapist_col = next(col for col in email_columns if col['name'] == 'therapist_id')
    patient_col = next(col for col in email_columns if col['name'] == 'patient_id')
    
    assert therapist_col['nullable'] == True, "therapist_id should be nullable in emails table"
    assert patient_col['nullable'] == True, "patient_id should be nullable in emails table"
    
    # Check telefonanrufe table has nullable therapist_id and patient_id
    phone_columns = db_inspector.get_columns('telefonanrufe', schema='communication_service')
    
    therapist_col = next(col for col in phone_columns if col['name'] == 'therapist_id')
    patient_col = next(col for col in phone_columns if col['name'] == 'patient_id')
    
    assert therapist_col['nullable'] == True, "therapist_id should be nullable in telefonanrufe table"
    assert patient_col['nullable'] == True, "patient_id should be nullable in telefonanrufe table"


def test_phase2_column_renames(db_inspector):
    """Test that Phase 2 column renames were applied correctly."""
    # Check therapeutenanfrage has anfragegroesse (not buendelgroesse)
    ta_columns = {col['name'] for col in db_inspector.get_columns('therapeutenanfrage', schema='matching_service')}
    assert 'anfragegroesse' in ta_columns, "Column 'anfragegroesse' not found in therapeutenanfrage"
    assert 'buendelgroesse' not in ta_columns, "Old column 'buendelgroesse' should not exist"
    
    # Check therapeut_anfrage_patient has position_in_anfrage (not position_im_buendel)
    tap_columns = {col['name'] for col in db_inspector.get_columns('therapeut_anfrage_patient', schema='matching_service')}
    assert 'position_in_anfrage' in tap_columns, "Column 'position_in_anfrage' not found in therapeut_anfrage_patient"
    assert 'position_im_buendel' not in tap_columns, "Old column 'position_im_buendel' should not exist"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])