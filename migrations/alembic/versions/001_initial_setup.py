"""complete database setup with patient communication support

Revision ID: 001_initial_setup
Revises: 
Create Date: 2024-12-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_setup'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete database schema with German naming conventions."""
    
    # ========== STEP 1: CREATE SCHEMAS ==========
    
    op.execute("CREATE SCHEMA IF NOT EXISTS patient_service")
    op.execute("CREATE SCHEMA IF NOT EXISTS therapist_service")
    op.execute("CREATE SCHEMA IF NOT EXISTS matching_service")
    op.execute("CREATE SCHEMA IF NOT EXISTS communication_service")
    op.execute("CREATE SCHEMA IF NOT EXISTS geocoding_service")
    op.execute("CREATE SCHEMA IF NOT EXISTS scraping_service")
    
    # ========== STEP 2: CREATE ALL ENUM TYPES WITH GERMAN NAMES AND VALUES ==========
    
    # Patient status enum
    op.execute("""
        CREATE TYPE patientenstatus AS ENUM (
            'offen', 'auf_der_Suche', 'in_Therapie', 
            'Therapie_abgeschlossen', 'Suche_abgebrochen', 'Therapie_abgebrochen'
        )
    """)
    
    # Therapist gender preference enum
    op.execute("""
        CREATE TYPE therapeutgeschlechtspraeferenz AS ENUM (
            'Männlich', 'Weiblich', 'Egal'
        )
    """)
    
    # Therapist status enum
    op.execute("""
        CREATE TYPE therapeutstatus AS ENUM (
            'aktiv', 'gesperrt', 'inaktiv'
        )
    """)
    
    # Email status enum
    op.execute("""
        CREATE TYPE emailstatus AS ENUM (
            'Entwurf', 'In_Warteschlange', 'Wird_gesendet', 'Gesendet', 'Fehlgeschlagen'
        )
    """)
    
    # Search status enum
    op.execute("""
        CREATE TYPE suchstatus AS ENUM (
            'aktiv', 'erfolgreich', 'pausiert', 'abgebrochen'
        )
    """)
    
    # Phone call status enum
    op.execute("""
        CREATE TYPE telefonanrufstatus AS ENUM (
            'geplant', 'abgeschlossen', 'fehlgeschlagen', 'abgebrochen'
        )
    """)
    
    # Response type enum
    op.execute("""
        CREATE TYPE antworttyp AS ENUM (
            'vollstaendige_Annahme', 'teilweise_Annahme', 
            'vollstaendige_Ablehnung', 'keine_Antwort'
        )
    """)
    
    # Patient outcome enum
    op.execute("""
        CREATE TYPE patientenergebnis AS ENUM (
            'angenommen', 'abgelehnt_Kapazitaet', 'abgelehnt_nicht_geeignet', 
            'abgelehnt_sonstiges', 'nicht_erschienen', 'in_Sitzungen'
        )
    """)
    
    # Bundle patient status enum
    op.execute("""
        CREATE TYPE buendel_patient_status AS ENUM (
            'anstehend', 'angenommen', 'abgelehnt', 'keine_antwort'
        )
    """)
    
    # ========== STEP 3: CREATE PATIENT SERVICE TABLES ==========
    
    # Create patienten table (German name)
    op.create_table('patienten',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anrede', sa.String(10), nullable=True),
        sa.Column('vorname', sa.String(100), nullable=False),
        sa.Column('nachname', sa.String(100), nullable=False),
        sa.Column('strasse', sa.String(255), nullable=True),
        sa.Column('plz', sa.String(10), nullable=True),
        sa.Column('ort', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telefon', sa.String(50), nullable=True),
        sa.Column('hausarzt', sa.String(255), nullable=True),
        sa.Column('krankenkasse', sa.String(100), nullable=True),
        sa.Column('krankenversicherungsnummer', sa.String(50), nullable=True),
        sa.Column('geburtsdatum', sa.Date(), nullable=True),
        sa.Column('diagnose', sa.String(50), nullable=True),
        sa.Column('vertraege_unterschrieben', sa.Boolean(), default=False),
        sa.Column('psychotherapeutische_sprechstunde', sa.Boolean(), default=False),
        sa.Column('startdatum', sa.Date(), nullable=True),
        sa.Column('erster_therapieplatz_am', sa.Date(), nullable=True),
        sa.Column('funktionierender_therapieplatz_am', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('offen', 'auf_der_Suche', 'in_Therapie', 
                                           'Therapie_abgeschlossen', 'Suche_abgebrochen', 
                                           'Therapie_abgebrochen', 
                                           name='patientenstatus', create_type=False), 
                  nullable=True, server_default='offen'),
        sa.Column('empfehler_der_unterstuetzung', sa.Text(), nullable=True),
        sa.Column('zeitliche_verfuegbarkeit', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('raeumliche_verfuegbarkeit', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('verkehrsmittel', sa.String(50), nullable=True),
        sa.Column('offen_fuer_gruppentherapie', sa.Boolean(), default=False),
        sa.Column('offen_fuer_diga', sa.Boolean(), default=False),
        sa.Column('letzter_kontakt', sa.Date(), nullable=True),
        sa.Column('psychotherapieerfahrung', sa.Boolean(), default=False),
        sa.Column('stationaere_behandlung', sa.Boolean(), default=False),
        sa.Column('berufliche_situation', sa.Text(), nullable=True),
        sa.Column('familienstand', sa.String(50), nullable=True),
        sa.Column('aktuelle_psychische_beschwerden', sa.Text(), nullable=True),
        sa.Column('beschwerden_seit', sa.Date(), nullable=True),
        sa.Column('bisherige_behandlungen', sa.Text(), nullable=True),
        sa.Column('relevante_koerperliche_erkrankungen', sa.Text(), nullable=True),
        sa.Column('aktuelle_medikation', sa.Text(), nullable=True),
        sa.Column('aktuelle_belastungsfaktoren', sa.Text(), nullable=True),
        sa.Column('unterstuetzungssysteme', sa.Text(), nullable=True),
        sa.Column('anlass_fuer_die_therapiesuche', sa.Text(), nullable=True),
        sa.Column('erwartungen_an_die_therapie', sa.Text(), nullable=True),
        sa.Column('therapieziele', sa.Text(), nullable=True),
        sa.Column('fruehere_therapieerfahrungen', sa.Text(), nullable=True),
        sa.Column('ausgeschlossene_therapeuten', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=True, server_default='[]'),
        sa.Column('bevorzugtes_therapeutengeschlecht', 
                  postgresql.ENUM('Männlich', 'Weiblich', 'Egal', 
                                 name='therapeutgeschlechtspraeferenz', create_type=False), 
                  nullable=True, server_default='Egal'),
        sa.Column('created_at', sa.Date(), nullable=True),
        sa.Column('updated_at', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='patient_service'
    )
    op.create_index('ix_patient_service_patienten_id', 'patienten', ['id'], 
                    unique=False, schema='patient_service')
    
    # ========== STEP 4: CREATE THERAPIST SERVICE TABLES ==========
    
    # Create therapeuten table (German name)
    op.create_table('therapeuten',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('anrede', sa.String(10), nullable=True),
        sa.Column('titel', sa.String(20), nullable=True),
        sa.Column('vorname', sa.String(100), nullable=False),
        sa.Column('nachname', sa.String(100), nullable=False),
        sa.Column('strasse', sa.String(255), nullable=True),
        sa.Column('plz', sa.String(10), nullable=True),
        sa.Column('ort', sa.String(100), nullable=True),
        sa.Column('telefon', sa.String(50), nullable=True),
        sa.Column('fax', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('webseite', sa.String(255), nullable=True),
        sa.Column('kassensitz', sa.Boolean(), default=True),
        sa.Column('geschlecht', sa.String(20), nullable=True),
        sa.Column('telefonische_erreichbarkeit', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('fremdsprachen', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('psychotherapieverfahren', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('zusatzqualifikationen', sa.Text(), nullable=True),
        sa.Column('besondere_leistungsangebote', sa.Text(), nullable=True),
        sa.Column('letzter_kontakt_email', sa.Date(), nullable=True),
        sa.Column('letzter_kontakt_telefon', sa.Date(), nullable=True),
        sa.Column('letztes_persoenliches_gespraech', sa.Date(), nullable=True),
        sa.Column('potenziell_verfuegbar', sa.Boolean(), default=False),
        sa.Column('potenziell_verfuegbar_notizen', sa.Text(), nullable=True),
        sa.Column('naechster_kontakt_moeglich', sa.Date(), nullable=True),
        sa.Column('bevorzugte_diagnosen', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('alter_min', sa.Integer(), nullable=True),
        sa.Column('alter_max', sa.Integer(), nullable=True),
        sa.Column('geschlechtspraeferenz', sa.String(50), nullable=True),
        sa.Column('arbeitszeiten', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('bevorzugt_gruppentherapie', sa.Boolean(), default=False),
        sa.Column('status', postgresql.ENUM('aktiv', 'gesperrt', 'inaktiv', 
                                           name='therapeutstatus', create_type=False), 
                  nullable=True, server_default='aktiv'),
        sa.Column('sperrgrund', sa.Text(), nullable=True),
        sa.Column('sperrdatum', sa.Date(), nullable=True),
        sa.Column('created_at', sa.Date(), nullable=True),
        sa.Column('updated_at', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='therapist_service'
    )
    op.create_index('ix_therapist_service_therapeuten_id', 'therapeuten', ['id'], 
                    unique=False, schema='therapist_service')
    op.create_index('idx_therapists_naechster_kontakt_moeglich', 'therapeuten', 
                    ['naechster_kontakt_moeglich'], schema='therapist_service')
    
    # ========== STEP 5: CREATE MATCHING SERVICE TABLES ==========
    
    # Create platzsuche table
    op.create_table('platzsuche',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('aktiv', 'erfolgreich', 'pausiert', 'abgebrochen',
                                           name='suchstatus', create_type=False), 
                  nullable=False, server_default='aktiv'),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('ausgeschlossene_therapeuten', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, server_default='[]'),
        sa.Column('gesamt_angeforderte_kontakte', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('erfolgreiche_vermittlung_datum', sa.DateTime(), nullable=True),
        sa.Column('notizen', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patient_service.patienten.id'], 
                               ondelete='CASCADE'),
        schema='matching_service'
    )
    op.create_index('idx_platzsuche_patient_id', 'platzsuche', ['patient_id'], 
                   schema='matching_service')
    op.create_index('idx_platzsuche_status', 'platzsuche', ['status'], 
                   schema='matching_service')
    
    # Create therapeutenanfrage table
    op.create_table('therapeutenanfrage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=False),
        sa.Column('erstellt_datum', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('gesendet_datum', sa.DateTime(), nullable=True),
        sa.Column('antwort_datum', sa.DateTime(), nullable=True),
        sa.Column('antworttyp', postgresql.ENUM('vollstaendige_Annahme', 'teilweise_Annahme',
                                                'vollstaendige_Ablehnung', 'keine_Antwort',
                                                name='antworttyp', create_type=False), 
                  nullable=True),
        sa.Column('buendelgroesse', sa.Integer(), nullable=False),
        sa.Column('angenommen_anzahl', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('abgelehnt_anzahl', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('keine_antwort_anzahl', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notizen', sa.Text(), nullable=True),
        sa.Column('email_id', sa.Integer(), nullable=True),
        sa.Column('phone_call_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['therapist_id'], ['therapist_service.therapeuten.id'], 
                               ondelete='CASCADE'),
        schema='matching_service'
    )
    op.create_index('idx_therapeutenanfrage_therapist_id', 'therapeutenanfrage', 
                   ['therapist_id'], schema='matching_service')
    op.create_index('idx_therapeutenanfrage_sent_date', 'therapeutenanfrage', 
                   ['gesendet_datum'], schema='matching_service')
    op.create_index('idx_therapeutenanfrage_response_type', 'therapeutenanfrage', 
                   ['antworttyp'], schema='matching_service')
    op.create_index('idx_therapeutenanfrage_email_id', 'therapeutenanfrage', 
                   ['email_id'], schema='matching_service')
    op.create_index('idx_therapeutenanfrage_phone_call_id', 'therapeutenanfrage', 
                   ['phone_call_id'], schema='matching_service')
    
    # Create therapeut_anfrage_patient table
    op.create_table('therapeut_anfrage_patient',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapeutenanfrage_id', sa.Integer(), nullable=False),
        sa.Column('platzsuche_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('position_im_buendel', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('anstehend', 'angenommen', 'abgelehnt', 'keine_antwort',
                                           name='buendel_patient_status', create_type=False), 
                  nullable=False, server_default='anstehend'),
        sa.Column('antwortergebnis', postgresql.ENUM('angenommen', 'abgelehnt_Kapazitaet', 
                                                     'abgelehnt_nicht_geeignet', 'abgelehnt_sonstiges', 
                                                     'nicht_erschienen', 'in_Sitzungen',
                                                     name='patientenergebnis', create_type=False), 
                  nullable=True),
        sa.Column('antwortnotizen', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['therapeutenanfrage_id'], 
                               ['matching_service.therapeutenanfrage.id'], 
                               ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platzsuche_id'], 
                               ['matching_service.platzsuche.id'], 
                               ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], 
                               ['patient_service.patienten.id'], 
                               ondelete='CASCADE'),
        sa.UniqueConstraint('therapeutenanfrage_id', 'platzsuche_id', 
                          name='uq_therapeut_anfrage_patient_bundle_search'),
        schema='matching_service'
    )
    op.create_index('idx_therapeut_anfrage_patient_therapeutenanfrage_id', 
                   'therapeut_anfrage_patient', ['therapeutenanfrage_id'], 
                   schema='matching_service')
    op.create_index('idx_therapeut_anfrage_patient_platzsuche_id', 
                   'therapeut_anfrage_patient', ['platzsuche_id'], 
                   schema='matching_service')
    op.create_index('idx_therapeut_anfrage_patient_patient_id', 
                   'therapeut_anfrage_patient', ['patient_id'], 
                   schema='matching_service')
    op.create_index('idx_therapeut_anfrage_patient_status', 
                   'therapeut_anfrage_patient', ['status'], 
                   schema='matching_service')
    
    # ========== STEP 6: CREATE COMMUNICATION SERVICE TABLES (WITH PATIENT SUPPORT) ==========
    
    # Create emails table - NOW WITH PATIENT SUPPORT
    op.create_table('emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=True),  # Now nullable!
        sa.Column('patient_id', sa.Integer(), nullable=True),    # NEW: patient support
        sa.Column('betreff', sa.String(255), nullable=False),
        sa.Column('inhalt_html', sa.Text(), nullable=False),
        sa.Column('inhalt_text', sa.Text(), nullable=False),
        sa.Column('empfaenger_email', sa.String(255), nullable=False),
        sa.Column('empfaenger_name', sa.String(255), nullable=False),
        sa.Column('absender_email', sa.String(255), nullable=False),
        sa.Column('absender_name', sa.String(255), nullable=False),
        sa.Column('antwort_erhalten', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('antwortdatum', sa.DateTime(), nullable=True),
        sa.Column('antwortinhalt', sa.Text(), nullable=True),
        sa.Column('nachverfolgung_erforderlich', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('nachverfolgung_notizen', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('Entwurf', 'In_Warteschlange', 'Wird_gesendet', 
                                           'Gesendet', 'Fehlgeschlagen',
                                           name='emailstatus', create_type=False), 
                  nullable=True, server_default='Entwurf'),
        sa.Column('in_warteschlange_am', sa.DateTime(), nullable=True),
        sa.Column('gesendet_am', sa.DateTime(), nullable=True),
        sa.Column('fehlermeldung', sa.Text(), nullable=True),
        sa.Column('wiederholungsanzahl', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        # Add check constraint: either therapist OR patient, not both
        sa.CheckConstraint(
            '(therapist_id IS NOT NULL AND patient_id IS NULL) OR '
            '(therapist_id IS NULL AND patient_id IS NOT NULL)',
            name='email_recipient_check'
        ),
        schema='communication_service'
    )
    op.create_index('ix_communication_service_emails_id', 'emails', ['id'], 
                   unique=False, schema='communication_service')
    op.create_index('ix_communication_service_emails_therapist_id', 'emails', 
                   ['therapist_id'], unique=False, schema='communication_service')
    op.create_index('ix_communication_service_emails_patient_id', 'emails', 
                   ['patient_id'], unique=False, schema='communication_service')  # NEW index
    
    # Create telefonanrufe table - NOW WITH PATIENT SUPPORT
    op.create_table('telefonanrufe',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=True),  # Now nullable!
        sa.Column('patient_id', sa.Integer(), nullable=True),    # NEW: patient support
        sa.Column('geplantes_datum', sa.Date(), nullable=False),
        sa.Column('geplante_zeit', sa.Time(), nullable=False),
        sa.Column('dauer_minuten', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('tatsaechliches_datum', sa.Date(), nullable=True),
        sa.Column('tatsaechliche_zeit', sa.Time(), nullable=True),
        sa.Column('status', postgresql.ENUM('geplant', 'abgeschlossen', 'fehlgeschlagen', 'abgebrochen',
                                           name='telefonanrufstatus', create_type=False), 
                  nullable=False, server_default='geplant'),
        sa.Column('ergebnis', sa.Text(), nullable=True),
        sa.Column('notizen', sa.Text(), nullable=True),
        sa.Column('wiederholen_nach', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        # Add check constraint: either therapist OR patient, not both
        sa.CheckConstraint(
            '(therapist_id IS NOT NULL AND patient_id IS NULL) OR '
            '(therapist_id IS NULL AND patient_id IS NOT NULL)',
            name='phone_call_recipient_check'
        ),
        schema='communication_service'
    )
    op.create_index('idx_phone_calls_therapist_id', 'telefonanrufe', ['therapist_id'], 
                   schema='communication_service')
    op.create_index('idx_phone_calls_patient_id', 'telefonanrufe', ['patient_id'], 
                   schema='communication_service')  # NEW index
    op.create_index('idx_phone_calls_scheduled_date', 'telefonanrufe', ['geplantes_datum'], 
                   schema='communication_service')
    op.create_index('idx_phone_calls_status', 'telefonanrufe', ['status'], 
                   schema='communication_service')
    
    # ========== STEP 7: CREATE GEOCODING SERVICE TABLES ==========
    
    # Create geocache table
    op.create_table('geocache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(255), nullable=False),
        sa.Column('query_type', sa.String(50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('result_data', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        schema='geocoding_service'
    )
    op.create_index('ix_geocache_query', 'geocache', ['query'], 
                   schema='geocoding_service')
    op.create_index('ix_geocache_query_type', 'geocache', ['query_type'], 
                   schema='geocoding_service')
    op.create_index('ix_geocache_created_at', 'geocache', ['created_at'], 
                   schema='geocoding_service')
    
    # Create distance_cache table
    op.create_table('distance_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('origin_latitude', sa.Float(), nullable=False),
        sa.Column('origin_longitude', sa.Float(), nullable=False),
        sa.Column('destination_latitude', sa.Float(), nullable=False),
        sa.Column('destination_longitude', sa.Float(), nullable=False),
        sa.Column('travel_mode', sa.String(50), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('travel_time_minutes', sa.Float(), nullable=True),
        sa.Column('route_data', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        schema='geocoding_service'
    )
    op.create_index('ix_distance_cache_points', 'distance_cache', 
                   ['origin_latitude', 'origin_longitude', 
                    'destination_latitude', 'destination_longitude',
                    'travel_mode'], 
                   schema='geocoding_service')
    
    # ========== STEP 8: ADD FOREIGN KEY CONSTRAINTS ==========
    # These are added after all tables are created to avoid dependency issues
    
    # Communication service foreign keys for email
    op.create_foreign_key('emails_therapist_id_fkey',
                          'emails', 'therapeuten',
                          ['therapist_id'], ['id'],
                          source_schema='communication_service',
                          referent_schema='therapist_service',
                          ondelete='CASCADE')
    
    op.create_foreign_key('emails_patient_id_fkey',
                          'emails', 'patienten',
                          ['patient_id'], ['id'],
                          source_schema='communication_service',
                          referent_schema='patient_service',
                          ondelete='CASCADE')
    
    # Communication service foreign keys for phone calls
    op.create_foreign_key('telefonanrufe_therapist_id_fkey',
                          'telefonanrufe', 'therapeuten',
                          ['therapist_id'], ['id'],
                          source_schema='communication_service',
                          referent_schema='therapist_service',
                          ondelete='CASCADE')
    
    op.create_foreign_key('telefonanrufe_patient_id_fkey',
                          'telefonanrufe', 'patienten',
                          ['patient_id'], ['id'],
                          source_schema='communication_service',
                          referent_schema='patient_service',
                          ondelete='CASCADE')
    
    # Matching service foreign keys
    op.create_foreign_key('therapeutenanfrage_email_id_fkey',
                          'therapeutenanfrage', 'emails',
                          ['email_id'], ['id'],
                          source_schema='matching_service',
                          referent_schema='communication_service',
                          ondelete='SET NULL')
    
    op.create_foreign_key('therapeutenanfrage_phone_call_id_fkey',
                          'therapeutenanfrage', 'telefonanrufe',
                          ['phone_call_id'], ['id'],
                          source_schema='matching_service',
                          referent_schema='communication_service',
                          ondelete='SET NULL')


def downgrade() -> None:
    """Drop all tables and types."""
    # Drop all tables in reverse order of creation
    
    # Drop foreign key constraints first
    op.drop_constraint('therapeutenanfrage_phone_call_id_fkey', 'therapeutenanfrage', 
                      schema='matching_service', type_='foreignkey')
    op.drop_constraint('therapeutenanfrage_email_id_fkey', 'therapeutenanfrage', 
                      schema='matching_service', type_='foreignkey')
    op.drop_constraint('telefonanrufe_patient_id_fkey', 'telefonanrufe', 
                      schema='communication_service', type_='foreignkey')
    op.drop_constraint('telefonanrufe_therapist_id_fkey', 'telefonanrufe', 
                      schema='communication_service', type_='foreignkey')
    op.drop_constraint('emails_patient_id_fkey', 'emails', 
                      schema='communication_service', type_='foreignkey')
    op.drop_constraint('emails_therapist_id_fkey', 'emails', 
                      schema='communication_service', type_='foreignkey')
    
    # Drop geocoding service tables
    op.drop_index('ix_distance_cache_points', table_name='distance_cache', 
                 schema='geocoding_service')
    op.drop_table('distance_cache', schema='geocoding_service')
    
    op.drop_index('ix_geocache_created_at', table_name='geocache', 
                 schema='geocoding_service')
    op.drop_index('ix_geocache_query_type', table_name='geocache', 
                 schema='geocoding_service')
    op.drop_index('ix_geocache_query', table_name='geocache', 
                 schema='geocoding_service')
    op.drop_table('geocache', schema='geocoding_service')
    
    # Drop communication service tables
    op.drop_index('idx_phone_calls_status', table_name='telefonanrufe', 
                 schema='communication_service')
    op.drop_index('idx_phone_calls_scheduled_date', table_name='telefonanrufe', 
                 schema='communication_service')
    op.drop_index('idx_phone_calls_patient_id', table_name='telefonanrufe', 
                 schema='communication_service')
    op.drop_index('idx_phone_calls_therapist_id', table_name='telefonanrufe', 
                 schema='communication_service')
    op.drop_table('telefonanrufe', schema='communication_service')
    
    op.drop_index('ix_communication_service_emails_patient_id', table_name='emails', 
                 schema='communication_service')
    op.drop_index('ix_communication_service_emails_therapist_id', table_name='emails', 
                 schema='communication_service')
    op.drop_index('ix_communication_service_emails_id', table_name='emails', 
                 schema='communication_service')
    op.drop_table('emails', schema='communication_service')
    
    # Drop matching service tables
    op.drop_index('idx_therapeut_anfrage_patient_status', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    op.drop_index('idx_therapeut_anfrage_patient_patient_id', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    op.drop_index('idx_therapeut_anfrage_patient_platzsuche_id', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    op.drop_index('idx_therapeut_anfrage_patient_therapeutenanfrage_id', 
                 table_name='therapeut_anfrage_patient', schema='matching_service')
    op.drop_table('therapeut_anfrage_patient', schema='matching_service')
    
    op.drop_index('idx_therapeutenanfrage_phone_call_id', table_name='therapeutenanfrage', 
                 schema='matching_service')
    op.drop_index('idx_therapeutenanfrage_email_id', table_name='therapeutenanfrage', 
                 schema='matching_service')
    op.drop_index('idx_therapeutenanfrage_response_type', table_name='therapeutenanfrage', 
                 schema='matching_service')
    op.drop_index('idx_therapeutenanfrage_sent_date', table_name='therapeutenanfrage', 
                 schema='matching_service')
    op.drop_index('idx_therapeutenanfrage_therapist_id', table_name='therapeutenanfrage', 
                 schema='matching_service')
    op.drop_table('therapeutenanfrage', schema='matching_service')
    
    op.drop_index('idx_platzsuche_status', table_name='platzsuche', schema='matching_service')
    op.drop_index('idx_platzsuche_patient_id', table_name='platzsuche', schema='matching_service')
    op.drop_table('platzsuche', schema='matching_service')
    
    # Drop therapist service tables
    op.drop_index('idx_therapists_naechster_kontakt_moeglich', table_name='therapeuten', 
                 schema='therapist_service')
    op.drop_index('ix_therapist_service_therapeuten_id', table_name='therapeuten', 
                 schema='therapist_service')
    op.drop_table('therapeuten', schema='therapist_service')
    
    # Drop patient service tables
    op.drop_index('ix_patient_service_patienten_id', table_name='patienten', 
                 schema='patient_service')
    op.drop_table('patienten', schema='patient_service')
    
    # Drop all enum types
    op.execute("DROP TYPE IF EXISTS buendel_patient_status")
    op.execute("DROP TYPE IF EXISTS patientenergebnis")
    op.execute("DROP TYPE IF EXISTS antworttyp")
    op.execute("DROP TYPE IF EXISTS telefonanrufstatus")
    op.execute("DROP TYPE IF EXISTS suchstatus")
    op.execute("DROP TYPE IF EXISTS emailstatus")
    op.execute("DROP TYPE IF EXISTS therapeutstatus")
    op.execute("DROP TYPE IF EXISTS therapeutgeschlechtspraeferenz")
    op.execute("DROP TYPE IF EXISTS patientenstatus")
    
    # Drop all schemas
    op.execute("DROP SCHEMA IF EXISTS scraping_service CASCADE")
    op.execute("DROP SCHEMA IF EXISTS geocoding_service CASCADE")
    op.execute("DROP SCHEMA IF EXISTS communication_service CASCADE")
    op.execute("DROP SCHEMA IF EXISTS matching_service CASCADE")
    op.execute("DROP SCHEMA IF EXISTS therapist_service CASCADE")
    op.execute("DROP SCHEMA IF EXISTS patient_service CASCADE")