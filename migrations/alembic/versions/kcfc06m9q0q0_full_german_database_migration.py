"""full german database migration

Revision ID: kcfc06m9q0q0
Revises: jcfc05l8p9p9
Create Date: 2024-12-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'kcfc06m9q0q0'
down_revision: Union[str, None] = 'jcfc05l8p9p9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade to full German database schema."""
    
    # ========== PHASE 1: ENUM CHANGES ==========
    
    # 1. Update patientstatus enum values from English to German
    op.execute("""
        -- Create new enum type with German name and values
        CREATE TYPE patientenstatus AS ENUM ('offen', 'auf_der_Suche', 'in_Therapie', 
            'Therapie_abgeschlossen', 'Suche_abgebrochen', 'Therapie_abgebrochen');
        
        -- Add temporary column
        ALTER TABLE patient_service.patients ADD COLUMN status_temp patientenstatus;
        
        -- Migrate data
        UPDATE patient_service.patients 
        SET status_temp = CASE status::text
            WHEN 'OPEN' THEN 'offen'::patientenstatus
            WHEN 'SEARCHING' THEN 'auf_der_Suche'::patientenstatus
            WHEN 'IN_THERAPY' THEN 'in_Therapie'::patientenstatus
            WHEN 'THERAPY_COMPLETED' THEN 'Therapie_abgeschlossen'::patientenstatus
            WHEN 'SEARCH_ABORTED' THEN 'Suche_abgebrochen'::patientenstatus
            WHEN 'THERAPY_ABORTED' THEN 'Therapie_abgebrochen'::patientenstatus
        END;
        
        -- Drop old column and rename new one
        ALTER TABLE patient_service.patients DROP COLUMN status;
        ALTER TABLE patient_service.patients RENAME COLUMN status_temp TO status;
        
        -- Drop old enum type
        DROP TYPE patientstatus;
    """)
    
    # 2. Update therapiststatus enum values from English to German
    op.execute("""
        -- Create new enum type with German name and values
        CREATE TYPE therapeutstatus AS ENUM ('aktiv', 'gesperrt', 'inaktiv');
        
        -- Add temporary column
        ALTER TABLE therapist_service.therapists ADD COLUMN status_temp therapeutstatus;
        
        -- Migrate data
        UPDATE therapist_service.therapists 
        SET status_temp = CASE status::text
            WHEN 'ACTIVE' THEN 'aktiv'::therapeutstatus
            WHEN 'BLOCKED' THEN 'gesperrt'::therapeutstatus
            WHEN 'INACTIVE' THEN 'inaktiv'::therapeutstatus
        END;
        
        -- Drop old column and rename new one
        ALTER TABLE therapist_service.therapists DROP COLUMN status;
        ALTER TABLE therapist_service.therapists RENAME COLUMN status_temp TO status;
        
        -- Drop old enum type
        DROP TYPE therapiststatus;
    """)
    
    # 3. Update emailstatus enum values to German
    op.execute("""
        -- Create temporary enum with new values
        ALTER TYPE emailstatus RENAME TO emailstatus_old;
        CREATE TYPE emailstatus AS ENUM ('Entwurf', 'In_Warteschlange', 'Wird_gesendet', 'Gesendet', 'Fehlgeschlagen');
        
        -- Update the column
        ALTER TABLE communication_service.emails 
            ALTER COLUMN status TYPE emailstatus 
            USING CASE status::text
                WHEN 'DRAFT' THEN 'Entwurf'::emailstatus
                WHEN 'QUEUED' THEN 'In_Warteschlange'::emailstatus
                WHEN 'SENDING' THEN 'Wird_gesendet'::emailstatus
                WHEN 'SENT' THEN 'Gesendet'::emailstatus
                WHEN 'FAILED' THEN 'Fehlgeschlagen'::emailstatus
            END;
        
        -- Drop old enum
        DROP TYPE emailstatus_old;
    """)
    
    # 4. Update responsetype to antworttyp with German values
    op.execute("""
        -- Create new enum type with German name and values
        CREATE TYPE antworttyp AS ENUM ('vollstaendige_Annahme', 'teilweise_Annahme', 
            'vollstaendige_Ablehnung', 'keine_Antwort');
        
        -- Check if responsetype is used anywhere
        -- If used in therapeutenanfrage.antworttyp, update it
        -- Since antworttyp column is varchar, we just need to update values if any exist
        UPDATE matching_service.therapeutenanfrage 
        SET antworttyp = CASE antworttyp
            WHEN 'FULL_ACCEPTANCE' THEN 'vollstaendige_Annahme'
            WHEN 'PARTIAL_ACCEPTANCE' THEN 'teilweise_Annahme'
            WHEN 'FULL_REJECTION' THEN 'vollstaendige_Ablehnung'
            WHEN 'NO_RESPONSE' THEN 'keine_Antwort'
            ELSE antworttyp
        END
        WHERE antworttyp IN ('FULL_ACCEPTANCE', 'PARTIAL_ACCEPTANCE', 'FULL_REJECTION', 'NO_RESPONSE');
        
        -- Drop old enum if it exists
        DROP TYPE IF EXISTS responsetype;
    """)
    
    # 5. Update patientoutcome to patientenergebnis with German values
    op.execute("""
        -- Create new enum type with German name and values
        CREATE TYPE patientenergebnis AS ENUM ('angenommen', 'abgelehnt_Kapazitaet', 
            'abgelehnt_nicht_geeignet', 'abgelehnt_sonstiges', 'nicht_erschienen', 'in_Sitzungen');
        
        -- If this enum is used in therapeut_anfrage_patient.antwortergebnis, update values
        UPDATE matching_service.therapeut_anfrage_patient 
        SET antwortergebnis = CASE antwortergebnis
            WHEN 'ACCEPTED' THEN 'angenommen'
            WHEN 'REJECTED_CAPACITY' THEN 'abgelehnt_Kapazitaet'
            WHEN 'REJECTED_NOT_SUITABLE' THEN 'abgelehnt_nicht_geeignet'
            WHEN 'REJECTED_OTHER' THEN 'abgelehnt_sonstiges'
            WHEN 'NO_SHOW' THEN 'nicht_erschienen'
            WHEN 'IN_SESSIONS' THEN 'in_Sitzungen'
            ELSE antwortergebnis
        END
        WHERE antwortergebnis IN ('ACCEPTED', 'REJECTED_CAPACITY', 'REJECTED_NOT_SUITABLE', 
                                 'REJECTED_OTHER', 'NO_SHOW', 'IN_SESSIONS');
        
        -- Drop old enum if it exists
        DROP TYPE IF EXISTS patientoutcome;
    """)
    
    # 6. Rename enum types
    op.execute("ALTER TYPE searchstatus RENAME TO suchstatus;")
    op.execute("ALTER TYPE phonecallstatus RENAME TO telefonanrufstatus;")
    op.execute("ALTER TYPE therapistgenderpreference RENAME TO therapeutgeschlechtspraeferenz;")
    
    # ========== PHASE 2: COLUMN RENAMES ==========
    
    # Communication Service - emails table
    op.alter_column('emails', 'body_html', new_column_name='inhalt_html', schema='communication_service')
    op.alter_column('emails', 'body_text', new_column_name='inhalt_text', schema='communication_service')
    op.alter_column('emails', 'queued_at', new_column_name='in_warteschlange_am', schema='communication_service')
    op.alter_column('emails', 'sent_at', new_column_name='gesendet_am', schema='communication_service')
    
    # Matching Service - therapeutenanfrage table
    op.alter_column('therapeutenanfrage', 'created_date', new_column_name='erstellt_datum', schema='matching_service')
    op.alter_column('therapeutenanfrage', 'sent_date', new_column_name='gesendet_datum', schema='matching_service')
    op.alter_column('therapeutenanfrage', 'response_date', new_column_name='antwort_datum', schema='matching_service')
    
    # ========== PHASE 3: TABLE RENAMES ==========
    
    # Store foreign key information before dropping
    op.execute("""
        -- Store FK information for recreation
        CREATE TEMP TABLE fk_backup AS
        SELECT 
            conname as constraint_name,
            conrelid::regclass as table_name,
            a.attname as column_name,
            confrelid::regclass as foreign_table_name,
            af.attname as foreign_column_name,
            n.nspname as schema_name,
            nf.nspname as foreign_schema_name
        FROM pg_constraint
        JOIN pg_attribute a ON a.attnum = ANY(conkey) AND a.attrelid = conrelid
        JOIN pg_attribute af ON af.attnum = ANY(confkey) AND af.attrelid = confrelid
        JOIN pg_class c ON c.oid = conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_class cf ON cf.oid = confrelid
        JOIN pg_namespace nf ON nf.oid = cf.relnamespace
        WHERE contype = 'f' 
        AND (conrelid::regclass::text LIKE '%.patients' 
            OR conrelid::regclass::text LIKE '%.therapists' 
            OR conrelid::regclass::text LIKE '%.phone_calls'
            OR confrelid::regclass::text LIKE '%.patients' 
            OR confrelid::regclass::text LIKE '%.therapists' 
            OR confrelid::regclass::text LIKE '%.phone_calls');
    """)
    
    # Drop all foreign keys that reference the tables we're renaming
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT constraint_name, table_name FROM fk_backup)
            LOOP
                EXECUTE 'ALTER TABLE ' || r.table_name || ' DROP CONSTRAINT IF EXISTS ' || r.constraint_name;
            END LOOP;
        END $$;
    """)
    
    # Rename tables
    op.rename_table('patients', 'patienten', schema='patient_service')
    op.rename_table('therapists', 'therapeuten', schema='therapist_service')
    op.rename_table('phone_calls', 'telefonanrufe', schema='communication_service')
    
    # Recreate foreign keys with updated table names
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT * FROM fk_backup)
            LOOP
                DECLARE
                    new_table_name text;
                    new_foreign_table_name text;
                BEGIN
                    -- Update table names
                    new_table_name := CASE 
                        WHEN r.table_name::text LIKE '%.patients' THEN replace(r.table_name::text, 'patients', 'patienten')
                        WHEN r.table_name::text LIKE '%.therapists' THEN replace(r.table_name::text, 'therapists', 'therapeuten')
                        WHEN r.table_name::text LIKE '%.phone_calls' THEN replace(r.table_name::text, 'phone_calls', 'telefonanrufe')
                        ELSE r.table_name::text
                    END;
                    
                    new_foreign_table_name := CASE 
                        WHEN r.foreign_table_name::text LIKE '%.patients' THEN replace(r.foreign_table_name::text, 'patients', 'patienten')
                        WHEN r.foreign_table_name::text LIKE '%.therapists' THEN replace(r.foreign_table_name::text, 'therapists', 'therapeuten')
                        WHEN r.foreign_table_name::text LIKE '%.phone_calls' THEN replace(r.foreign_table_name::text, 'phone_calls', 'telefonanrufe')
                        ELSE r.foreign_table_name::text
                    END;
                    
                    -- Recreate constraint
                    EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES %s(%s)',
                        new_table_name, r.constraint_name, r.column_name, new_foreign_table_name, r.foreign_column_name);
                END;
            END LOOP;
        END $$;
    """)
    
    # Update indexes that were automatically renamed
    op.execute("""
        -- Update primary key index names
        ALTER INDEX IF EXISTS patient_service.patients_pkey RENAME TO patienten_pkey;
        ALTER INDEX IF EXISTS therapist_service.therapists_pkey RENAME TO therapeuten_pkey;
        ALTER INDEX IF EXISTS communication_service.phone_calls_pkey RENAME TO telefonanrufe_pkey;
        
        -- Update other indexes
        ALTER INDEX IF EXISTS patient_service.ix_patient_service_patients_id RENAME TO ix_patient_service_patienten_id;
        ALTER INDEX IF EXISTS therapist_service.ix_therapist_service_therapists_id RENAME TO ix_therapist_service_therapeuten_id;
    """)


def downgrade() -> None:
    """Downgrade from German back to English schema."""
    
    # ========== PHASE 1: TABLE RENAMES BACK TO ENGLISH ==========
    
    # Store foreign key information before dropping
    op.execute("""
        CREATE TEMP TABLE fk_backup_down AS
        SELECT 
            conname as constraint_name,
            conrelid::regclass as table_name,
            a.attname as column_name,
            confrelid::regclass as foreign_table_name,
            af.attname as foreign_column_name
        FROM pg_constraint
        JOIN pg_attribute a ON a.attnum = ANY(conkey) AND a.attrelid = conrelid
        JOIN pg_attribute af ON af.attnum = ANY(confkey) AND af.attrelid = confrelid
        WHERE contype = 'f' 
        AND (conrelid::regclass::text LIKE '%.patienten' 
            OR conrelid::regclass::text LIKE '%.therapeuten' 
            OR conrelid::regclass::text LIKE '%.telefonanrufe'
            OR confrelid::regclass::text LIKE '%.patienten' 
            OR confrelid::regclass::text LIKE '%.therapeuten' 
            OR confrelid::regclass::text LIKE '%.telefonanrufe');
    """)
    
    # Drop all foreign keys
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT constraint_name, table_name FROM fk_backup_down)
            LOOP
                EXECUTE 'ALTER TABLE ' || r.table_name || ' DROP CONSTRAINT IF EXISTS ' || r.constraint_name;
            END LOOP;
        END $$;
    """)
    
    # Rename tables back to English
    op.rename_table('patienten', 'patients', schema='patient_service')
    op.rename_table('therapeuten', 'therapists', schema='therapist_service')
    op.rename_table('telefonanrufe', 'phone_calls', schema='communication_service')
    
    # Recreate foreign keys
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT * FROM fk_backup_down)
            LOOP
                DECLARE
                    new_table_name text;
                    new_foreign_table_name text;
                BEGIN
                    -- Update table names back to English
                    new_table_name := CASE 
                        WHEN r.table_name::text LIKE '%.patienten' THEN replace(r.table_name::text, 'patienten', 'patients')
                        WHEN r.table_name::text LIKE '%.therapeuten' THEN replace(r.table_name::text, 'therapeuten', 'therapists')
                        WHEN r.table_name::text LIKE '%.telefonanrufe' THEN replace(r.table_name::text, 'telefonanrufe', 'phone_calls')
                        ELSE r.table_name::text
                    END;
                    
                    new_foreign_table_name := CASE 
                        WHEN r.foreign_table_name::text LIKE '%.patienten' THEN replace(r.foreign_table_name::text, 'patienten', 'patients')
                        WHEN r.foreign_table_name::text LIKE '%.therapeuten' THEN replace(r.foreign_table_name::text, 'therapeuten', 'therapists')
                        WHEN r.foreign_table_name::text LIKE '%.telefonanrufe' THEN replace(r.foreign_table_name::text, 'telefonanrufe', 'phone_calls')
                        ELSE r.foreign_table_name::text
                    END;
                    
                    EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %s FOREIGN KEY (%s) REFERENCES %s(%s)',
                        new_table_name, r.constraint_name, r.column_name, new_foreign_table_name, r.foreign_column_name);
                END;
            END LOOP;
        END $$;
    """)
    
    # ========== PHASE 2: COLUMN RENAMES BACK TO ENGLISH ==========
    
    # Communication Service - emails table
    op.alter_column('emails', 'inhalt_html', new_column_name='body_html', schema='communication_service')
    op.alter_column('emails', 'inhalt_text', new_column_name='body_text', schema='communication_service')
    op.alter_column('emails', 'in_warteschlange_am', new_column_name='queued_at', schema='communication_service')
    op.alter_column('emails', 'gesendet_am', new_column_name='sent_at', schema='communication_service')
    
    # Matching Service - therapeutenanfrage table
    op.alter_column('therapeutenanfrage', 'erstellt_datum', new_column_name='created_date', schema='matching_service')
    op.alter_column('therapeutenanfrage', 'gesendet_datum', new_column_name='sent_date', schema='matching_service')
    op.alter_column('therapeutenanfrage', 'antwort_datum', new_column_name='response_date', schema='matching_service')
    
    # ========== PHASE 3: ENUM CHANGES BACK TO ENGLISH ==========
    
    # Rename enum types back
    op.execute("ALTER TYPE suchstatus RENAME TO searchstatus;")
    op.execute("ALTER TYPE telefonanrufstatus RENAME TO phonecallstatus;")
    op.execute("ALTER TYPE therapeutgeschlechtspraeferenz RENAME TO therapistgenderpreference;")
    
    # Revert enum values to English (reversed order)
    op.execute("""
        -- Revert patientenergebnis to patientoutcome
        CREATE TYPE patientoutcome AS ENUM ('ACCEPTED', 'REJECTED_CAPACITY', 
            'REJECTED_NOT_SUITABLE', 'REJECTED_OTHER', 'NO_SHOW', 'IN_SESSIONS');
        DROP TYPE IF EXISTS patientenergebnis;
    """)
    
    op.execute("""
        -- Revert antworttyp to responsetype
        CREATE TYPE responsetype AS ENUM ('FULL_ACCEPTANCE', 'PARTIAL_ACCEPTANCE', 
            'FULL_REJECTION', 'NO_RESPONSE');
        DROP TYPE IF EXISTS antworttyp;
    """)
    
    op.execute("""
        -- Revert emailstatus values
        ALTER TYPE emailstatus RENAME TO emailstatus_old;
        CREATE TYPE emailstatus AS ENUM ('DRAFT', 'QUEUED', 'SENDING', 'SENT', 'FAILED');
        
        ALTER TABLE communication_service.emails 
            ALTER COLUMN status TYPE emailstatus 
            USING CASE status::text
                WHEN 'Entwurf' THEN 'DRAFT'::emailstatus
                WHEN 'In_Warteschlange' THEN 'QUEUED'::emailstatus
                WHEN 'Wird_gesendet' THEN 'SENDING'::emailstatus
                WHEN 'Gesendet' THEN 'SENT'::emailstatus
                WHEN 'Fehlgeschlagen' THEN 'FAILED'::emailstatus
            END;
        
        DROP TYPE emailstatus_old;
    """)
    
    op.execute("""
        -- Revert therapeutstatus
        CREATE TYPE therapiststatus AS ENUM ('ACTIVE', 'BLOCKED', 'INACTIVE');
        
        ALTER TABLE therapist_service.therapists ADD COLUMN status_temp therapiststatus;
        
        UPDATE therapist_service.therapists 
        SET status_temp = CASE status::text
            WHEN 'aktiv' THEN 'ACTIVE'::therapiststatus
            WHEN 'gesperrt' THEN 'BLOCKED'::therapiststatus
            WHEN 'inaktiv' THEN 'INACTIVE'::therapiststatus
        END;
        
        ALTER TABLE therapist_service.therapists DROP COLUMN status;
        ALTER TABLE therapist_service.therapists RENAME COLUMN status_temp TO status;
        
        DROP TYPE therapeutstatus;
    """)
    
    op.execute("""
        -- Revert patientenstatus to patientstatus
        CREATE TYPE patientstatus AS ENUM ('OPEN', 'SEARCHING', 'IN_THERAPY', 
            'THERAPY_COMPLETED', 'SEARCH_ABORTED', 'THERAPY_ABORTED');
        
        ALTER TABLE patient_service.patients ADD COLUMN status_temp patientstatus;
        
        UPDATE patient_service.patients 
        SET status_temp = CASE status::text
            WHEN 'offen' THEN 'OPEN'::patientstatus
            WHEN 'auf_der_Suche' THEN 'SEARCHING'::patientstatus
            WHEN 'in_Therapie' THEN 'IN_THERAPY'::patientstatus
            WHEN 'Therapie_abgeschlossen' THEN 'THERAPY_COMPLETED'::patientstatus
            WHEN 'Suche_abgebrochen' THEN 'SEARCH_ABORTED'::patientstatus
            WHEN 'Therapie_abgebrochen' THEN 'THERAPY_ABORTED'::patientstatus
        END;
        
        ALTER TABLE patient_service.patients DROP COLUMN status;
        ALTER TABLE patient_service.patients RENAME COLUMN status_temp TO status;
        
        DROP TYPE patientenstatus;
    """)
