"""rename remaining fields to german

Revision ID: gcfc02i5m6m6
Revises: fcfc01h4l5l5
Create Date: 2025-05-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'gcfc02i5m6m6'
down_revision: Union[str, None] = 'fcfc01h4l5l5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename remaining English fields to German across all tables."""
    
    # ========== COMMUNICATION SERVICE TABLES ==========
    
    # 1. Rename columns in emails table
    op.alter_column('emails', 'subject',
                    new_column_name='betreff',
                    schema='communication_service')
    
    op.alter_column('emails', 'recipient_email',
                    new_column_name='empfaenger_email',
                    schema='communication_service')
    
    op.alter_column('emails', 'recipient_name',
                    new_column_name='empfaenger_name',
                    schema='communication_service')
    
    op.alter_column('emails', 'sender_email',
                    new_column_name='absender_email',
                    schema='communication_service')
    
    op.alter_column('emails', 'sender_name',
                    new_column_name='absender_name',
                    schema='communication_service')
    
    op.alter_column('emails', 'response_received',
                    new_column_name='antwort_erhalten',
                    schema='communication_service')
    
    op.alter_column('emails', 'response_date',
                    new_column_name='antwortdatum',
                    schema='communication_service')
    
    op.alter_column('emails', 'response_content',
                    new_column_name='antwortinhalt',
                    schema='communication_service')
    
    op.alter_column('emails', 'follow_up_required',
                    new_column_name='nachverfolgung_erforderlich',
                    schema='communication_service')
    
    op.alter_column('emails', 'follow_up_notes',
                    new_column_name='nachverfolgung_notizen',
                    schema='communication_service')
    
    op.alter_column('emails', 'error_message',
                    new_column_name='fehlermeldung',
                    schema='communication_service')
    
    op.alter_column('emails', 'retry_count',
                    new_column_name='wiederholungsanzahl',
                    schema='communication_service')
    
    # 2. Rename columns in email_batches table
    op.alter_column('email_batches', 'response_outcome',
                    new_column_name='antwortergebnis',
                    schema='communication_service')
    
    op.alter_column('email_batches', 'response_notes',
                    new_column_name='antwortnotizen',
                    schema='communication_service')
    
    # 3. Rename columns in phone_calls table
    op.alter_column('phone_calls', 'scheduled_date',
                    new_column_name='geplantes_datum',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'scheduled_time',
                    new_column_name='geplante_zeit',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'duration_minutes',
                    new_column_name='dauer_minuten',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'actual_date',
                    new_column_name='tatsaechliches_datum',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'actual_time',
                    new_column_name='tatsaechliche_zeit',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'outcome',
                    new_column_name='ergebnis',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'notes',
                    new_column_name='notizen',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'retry_after',
                    new_column_name='wiederholen_nach',
                    schema='communication_service')
    
    # 4. Rename columns in phone_call_batches table
    op.alter_column('phone_call_batches', 'outcome',
                    new_column_name='ergebnis',
                    schema='communication_service')
    
    op.alter_column('phone_call_batches', 'follow_up_required',
                    new_column_name='nachverfolgung_erforderlich',
                    schema='communication_service')
    
    op.alter_column('phone_call_batches', 'follow_up_notes',
                    new_column_name='nachverfolgung_notizen',
                    schema='communication_service')
    
    # ========== MATCHING SERVICE TABLES ==========
    
    # 5. Rename columns in platzsuche table
    op.alter_column('platzsuche', 'excluded_therapists',
                    new_column_name='ausgeschlossene_therapeuten',
                    schema='matching_service')
    
    op.alter_column('platzsuche', 'total_requested_contacts',
                    new_column_name='gesamt_angeforderte_kontakte',
                    schema='matching_service')
    
    op.alter_column('platzsuche', 'successful_match_date',
                    new_column_name='erfolgreiche_vermittlung_datum',
                    schema='matching_service')
    
    op.alter_column('platzsuche', 'notes',
                    new_column_name='notizen',
                    schema='matching_service')
    
    # 6. Rename columns in therapeutenanfrage table
    op.alter_column('therapeutenanfrage', 'bundle_size',
                    new_column_name='buendelgroesse',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'accepted_count',
                    new_column_name='angenommen_anzahl',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'rejected_count',
                    new_column_name='abgelehnt_anzahl',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'no_response_count',
                    new_column_name='keine_antwort_anzahl',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'response_type',
                    new_column_name='antworttyp',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'notes',
                    new_column_name='notizen',
                    schema='matching_service')
    
    # 7. Rename columns in therapeut_anfrage_patient table
    op.alter_column('therapeut_anfrage_patient', 'position_in_bundle',
                    new_column_name='position_im_buendel',
                    schema='matching_service')
    
    op.alter_column('therapeut_anfrage_patient', 'response_outcome',
                    new_column_name='antwortergebnis',
                    schema='matching_service')
    
    op.alter_column('therapeut_anfrage_patient', 'response_notes',
                    new_column_name='antwortnotizen',
                    schema='matching_service')


def downgrade() -> None:
    """Rename fields back to English."""
    
    # ========== MATCHING SERVICE TABLES (reverse order) ==========
    
    # 7. Rename columns back in therapeut_anfrage_patient table
    op.alter_column('therapeut_anfrage_patient', 'antwortnotizen',
                    new_column_name='response_notes',
                    schema='matching_service')
    
    op.alter_column('therapeut_anfrage_patient', 'antwortergebnis',
                    new_column_name='response_outcome',
                    schema='matching_service')
    
    op.alter_column('therapeut_anfrage_patient', 'position_im_buendel',
                    new_column_name='position_in_bundle',
                    schema='matching_service')
    
    # 6. Rename columns back in therapeutenanfrage table
    op.alter_column('therapeutenanfrage', 'notizen',
                    new_column_name='notes',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'antworttyp',
                    new_column_name='response_type',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'keine_antwort_anzahl',
                    new_column_name='no_response_count',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'abgelehnt_anzahl',
                    new_column_name='rejected_count',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'angenommen_anzahl',
                    new_column_name='accepted_count',
                    schema='matching_service')
    
    op.alter_column('therapeutenanfrage', 'buendelgroesse',
                    new_column_name='bundle_size',
                    schema='matching_service')
    
    # 5. Rename columns back in platzsuche table
    op.alter_column('platzsuche', 'notizen',
                    new_column_name='notes',
                    schema='matching_service')
    
    op.alter_column('platzsuche', 'erfolgreiche_vermittlung_datum',
                    new_column_name='successful_match_date',
                    schema='matching_service')
    
    op.alter_column('platzsuche', 'gesamt_angeforderte_kontakte',
                    new_column_name='total_requested_contacts',
                    schema='matching_service')
    
    op.alter_column('platzsuche', 'ausgeschlossene_therapeuten',
                    new_column_name='excluded_therapists',
                    schema='matching_service')
    
    # ========== COMMUNICATION SERVICE TABLES (reverse order) ==========
    
    # 4. Rename columns back in phone_call_batches table
    op.alter_column('phone_call_batches', 'nachverfolgung_notizen',
                    new_column_name='follow_up_notes',
                    schema='communication_service')
    
    op.alter_column('phone_call_batches', 'nachverfolgung_erforderlich',
                    new_column_name='follow_up_required',
                    schema='communication_service')
    
    op.alter_column('phone_call_batches', 'ergebnis',
                    new_column_name='outcome',
                    schema='communication_service')
    
    # 3. Rename columns back in phone_calls table
    op.alter_column('phone_calls', 'wiederholen_nach',
                    new_column_name='retry_after',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'notizen',
                    new_column_name='notes',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'ergebnis',
                    new_column_name='outcome',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'tatsaechliche_zeit',
                    new_column_name='actual_time',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'tatsaechliches_datum',
                    new_column_name='actual_date',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'dauer_minuten',
                    new_column_name='duration_minutes',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'geplante_zeit',
                    new_column_name='scheduled_time',
                    schema='communication_service')
    
    op.alter_column('phone_calls', 'geplantes_datum',
                    new_column_name='scheduled_date',
                    schema='communication_service')
    
    # 2. Rename columns back in email_batches table
    op.alter_column('email_batches', 'antwortnotizen',
                    new_column_name='response_notes',
                    schema='communication_service')
    
    op.alter_column('email_batches', 'antwortergebnis',
                    new_column_name='response_outcome',
                    schema='communication_service')
    
    # 1. Rename columns back in emails table
    op.alter_column('emails', 'wiederholungsanzahl',
                    new_column_name='retry_count',
                    schema='communication_service')
    
    op.alter_column('emails', 'fehlermeldung',
                    new_column_name='error_message',
                    schema='communication_service')
    
    op.alter_column('emails', 'nachverfolgung_notizen',
                    new_column_name='follow_up_notes',
                    schema='communication_service')
    
    op.alter_column('emails', 'nachverfolgung_erforderlich',
                    new_column_name='follow_up_required',
                    schema='communication_service')
    
    op.alter_column('emails', 'antwortinhalt',
                    new_column_name='response_content',
                    schema='communication_service')
    
    op.alter_column('emails', 'antwortdatum',
                    new_column_name='response_date',
                    schema='communication_service')
    
    op.alter_column('emails', 'antwort_erhalten',
                    new_column_name='response_received',
                    schema='communication_service')
    
    op.alter_column('emails', 'absender_name',
                    new_column_name='sender_name',
                    schema='communication_service')
    
    op.alter_column('emails', 'absender_email',
                    new_column_name='sender_email',
                    schema='communication_service')
    
    op.alter_column('emails', 'empfaenger_name',
                    new_column_name='recipient_name',
                    schema='communication_service')
    
    op.alter_column('emails', 'empfaenger_email',
                    new_column_name='recipient_email',
                    schema='communication_service')
    
    op.alter_column('emails', 'betreff',
                    new_column_name='subject',
                    schema='communication_service')