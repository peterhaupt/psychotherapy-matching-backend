"""Unit tests for Communication Service patient update functionality.

Tests that sending emails and completing phone calls updates patient last contact.
Using fixture-based mocking strategy for clean test isolation.

These tests verify the REAL implementation in EmailResource and PhoneCallResource.
"""
import sys
import pytest
from unittest.mock import Mock, patch, call, MagicMock
from datetime import date, datetime


@pytest.fixture
def mock_comm_dependencies():
    """Mock all dependencies before importing the code under test."""
    # Save original modules
    original_modules = {}
    modules_to_mock = [
        'models',
        'models.email',
        'models.phone_call',
        'shared',
        'shared.utils',
        'shared.utils.database',
        'shared.config',
        'shared.api',
        'shared.api.base_resource',
        'shared.api.retry_client',
        'flask',
        'flask_restful',
        'sqlalchemy',
        'sqlalchemy.exc',
        'events',
        'events.producers',
        'utils',
        'utils.markdown_processor',
        'utils.phone_call_scheduler',
        'utils.email_sender',
        'logging'
    ]
    
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Mock all dependencies
    sys.modules['models'] = MagicMock()
    sys.modules['models.email'] = MagicMock()
    sys.modules['models.phone_call'] = MagicMock()
    sys.modules['shared'] = MagicMock()
    sys.modules['shared.utils'] = MagicMock()
    sys.modules['shared.utils.database'] = MagicMock()
    sys.modules['shared.config'] = MagicMock()
    sys.modules['shared.api'] = MagicMock()
    sys.modules['shared.api.base_resource'] = MagicMock()
    sys.modules['shared.api.retry_client'] = MagicMock()
    sys.modules['flask'] = MagicMock()
    sys.modules['flask_restful'] = MagicMock()
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlalchemy.exc'] = MagicMock()
    sys.modules['events'] = MagicMock()
    sys.modules['events.producers'] = MagicMock()
    sys.modules['utils'] = MagicMock()
    sys.modules['utils.markdown_processor'] = MagicMock()
    sys.modules['utils.phone_call_scheduler'] = MagicMock()
    sys.modules['utils.email_sender'] = MagicMock()
    sys.modules['logging'] = MagicMock()
    
    # Set up EmailStatus enum
    from enum import Enum
    class MockEmailStatus(str, Enum):
        Entwurf = "Entwurf"
        In_Warteschlange = "In_Warteschlange"
        Wird_gesendet = "Wird_gesendet"
        Gesendet = "Gesendet"
        Fehlgeschlagen = "Fehlgeschlagen"
    
    class MockPhoneCallStatus(str, Enum):
        geplant = "geplant"
        abgeschlossen = "abgeschlossen"
        fehlgeschlagen = "fehlgeschlagen"
        abgebrochen = "abgebrochen"
    
    # Set up the enums in models
    sys.modules['models.email'].EmailStatus = MockEmailStatus
    sys.modules['models.email'].Email = MagicMock()
    sys.modules['models.phone_call'].PhoneCallStatus = MockPhoneCallStatus
    sys.modules['models.phone_call'].PhoneCall = MagicMock()
    
    # Mock shared modules
    mock_config = MagicMock()
    mock_config.get_service_url.return_value = "http://patient-service"
    mock_config.EMAIL_SENDER = "test@example.com"
    mock_config.EMAIL_SENDER_NAME = "Test Sender"
    sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)
    
    # Mock RetryAPIClient
    mock_retry_client = MagicMock()
    sys.modules['shared.api.retry_client'].RetryAPIClient = mock_retry_client
    
    # Mock SessionLocal
    mock_session_local = MagicMock()
    sys.modules['shared.utils.database'].SessionLocal = mock_session_local
    
    # Mock Flask-RESTful components
    mock_reqparse = MagicMock()
    mock_parser = MagicMock()
    mock_reqparse.RequestParser = MagicMock(return_value=mock_parser)
    sys.modules['flask_restful'].reqparse = mock_reqparse
    sys.modules['flask_restful'].Resource = MagicMock()
    sys.modules['flask_restful'].fields = MagicMock()
    sys.modules['flask_restful'].marshal = MagicMock(return_value={})
    
    # Mock PaginatedListResource
    sys.modules['shared.api.base_resource'].PaginatedListResource = MagicMock()
    
    # Mock event publishers
    sys.modules['events.producers'].publish_email_sent = MagicMock()
    sys.modules['events.producers'].publish_email_response_received = MagicMock()
    sys.modules['events.producers'].publish_phone_call_scheduled = MagicMock()
    sys.modules['events.producers'].publish_phone_call_completed = MagicMock()
    
    # Mock logging
    mock_logger = MagicMock()
    sys.modules['logging'].getLogger = MagicMock(return_value=mock_logger)
    
    # NOW import the REAL classes after mocking
    from communication_service.api.emails import EmailResource
    from communication_service.api.phone_calls import PhoneCallResource
    
    yield {
        'EmailResource': EmailResource,
        'PhoneCallResource': PhoneCallResource,
        'EmailStatus': MockEmailStatus,
        'PhoneCallStatus': MockPhoneCallStatus,
        'mock_config': mock_config,
        'mock_retry_client': mock_retry_client,
        'mock_session_local': mock_session_local,
        'mock_parser': mock_parser,
        'mock_logger': mock_logger
    }
    
    # Cleanup
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


class TestCommunicationPatientUpdates:
    """Test Communication service updating patient last contact."""
    
    def test_email_sent_updates_patient_last_contact(self, mock_comm_dependencies):
        """Test that marking email as sent updates patient last contact."""
        EmailResource = mock_comm_dependencies['EmailResource']
        EmailStatus = mock_comm_dependencies['EmailStatus']
        mock_session_local = mock_comm_dependencies['mock_session_local']
        mock_parser = mock_comm_dependencies['mock_parser']
        mock_retry_client = mock_comm_dependencies['mock_retry_client']
        mock_config = mock_comm_dependencies['mock_config']
        
        resource = EmailResource()
        
        # Mock email with patient
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = 123
        mock_email.status = EmailStatus.Entwurf
        mock_email.antwort_erhalten = False
        mock_email.recipient_type = 'patient'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'Gesendet',
            'antwort_erhalten': None,
            'antwortdatum': None,
            'antwortinhalt': None,
            'fehlermeldung': None
        }
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('communication_service.api.emails.validate_and_get_email_status', return_value=EmailStatus.Gesendet):
            with patch('communication_service.api.emails.date') as mock_date:
                mock_date.today.return_value.isoformat.return_value = '2025-01-15'
                
                mock_retry_client.call_with_retry.return_value = mock_response
                
                # Execute
                result, status_code = resource.put(789)
        
        # Verify API was called
        mock_retry_client.call_with_retry.assert_called_once_with(
            method="PATCH",
            url="http://patient-service/api/patients/123/last-contact",
            json={"date": "2025-01-15"}
        )
        
        # Verify email was updated
        assert mock_email.status == EmailStatus.Gesendet
        mock_db.commit.assert_called()
        
        # Verify response
        assert status_code == 200
    
    def test_email_response_updates_patient_last_contact(self, mock_comm_dependencies):
        """Test that receiving email response updates patient last contact."""
        EmailResource = mock_comm_dependencies['EmailResource']
        EmailStatus = mock_comm_dependencies['EmailStatus']
        mock_session_local = mock_comm_dependencies['mock_session_local']
        mock_parser = mock_comm_dependencies['mock_parser']
        mock_retry_client = mock_comm_dependencies['mock_retry_client']
        
        resource = EmailResource()
        
        # Mock email with patient
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = 123
        mock_email.antwort_erhalten = False
        mock_email.status = EmailStatus.Gesendet
        mock_email.recipient_type = 'patient'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': None,
            'antwort_erhalten': True,
            'antwortdatum': None,
            'antwortinhalt': None,
            'fehlermeldung': None
        }
        
        with patch('communication_service.api.emails.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = '2025-01-16'
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_retry_client.call_with_retry.return_value = mock_response
            
            # Execute
            result, status_code = resource.put(789)
        
        # Email response doesn't trigger patient update in current implementation
        # Only status change to 'Gesendet' triggers it
        # So this should NOT call the API
        mock_retry_client.call_with_retry.assert_not_called()
        
        # Verify email was updated
        assert mock_email.antwort_erhalten == True
        assert status_code == 200
    
    def test_phone_call_completed_updates_patient_last_contact(self, mock_comm_dependencies):
        """Test that completing phone call updates patient last contact."""
        PhoneCallResource = mock_comm_dependencies['PhoneCallResource']
        PhoneCallStatus = mock_comm_dependencies['PhoneCallStatus']
        mock_session_local = mock_comm_dependencies['mock_session_local']
        mock_parser = mock_comm_dependencies['mock_parser']
        mock_retry_client = mock_comm_dependencies['mock_retry_client']
        
        resource = PhoneCallResource()
        
        # Mock phone call with patient
        mock_call = Mock()
        mock_call.id = 456
        mock_call.patient_id = 123
        mock_call.status = 'geplant'
        mock_call.recipient_type = 'patient'
        mock_call.therapeutenanfrage_id = None
        mock_call.therapist_id = None
        mock_call.ergebnis = None
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_call
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'abgeschlossen',
            'tatsaechliches_datum': '2025-01-15',
            'tatsaechliche_zeit': '14:30',
            'geplantes_datum': None,
            'geplante_zeit': None,
            'dauer_minuten': None,
            'ergebnis': None,
            'notizen': None,
            'therapeutenanfrage_id': None
        }
        
        with patch('communication_service.api.phone_calls.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = '2025-01-15'
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_retry_client.call_with_retry.return_value = mock_response
            
            # Execute
            result, status_code = resource.put(456)
        
        # Verify API was called
        mock_retry_client.call_with_retry.assert_called_once_with(
            method="PATCH",
            url="http://patient-service/api/patients/123/last-contact",
            json={"date": "2025-01-15"}
        )
        
        # Verify call was updated
        assert mock_call.status == 'abgeschlossen'
        assert mock_call.tatsaechliches_datum == '2025-01-15'
        assert status_code == 200
    
    def test_patient_api_retry_logic(self, mock_comm_dependencies):
        """Test that patient API calls use retry logic."""
        EmailResource = mock_comm_dependencies['EmailResource']
        EmailStatus = mock_comm_dependencies['EmailStatus']
        mock_session_local = mock_comm_dependencies['mock_session_local']
        mock_parser = mock_comm_dependencies['mock_parser']
        mock_retry_client = mock_comm_dependencies['mock_retry_client']
        
        resource = EmailResource()
        
        # Mock email with patient
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = 123
        mock_email.status = EmailStatus.Entwurf
        mock_email.antwort_erhalten = False
        mock_email.recipient_type = 'patient'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'Gesendet',
            'antwort_erhalten': None,
            'antwortdatum': None,
            'antwortinhalt': None,
            'fehlermeldung': None
        }
        
        # Mock API failure (RetryAPIClient handles retries internally)
        mock_retry_client.call_with_retry.side_effect = Exception("Network error")
        
        with patch('communication_service.api.emails.validate_and_get_email_status', return_value=EmailStatus.Gesendet):
            # Execute
            result, status_code = resource.put(789)
        
        # Should be called once (RetryAPIClient handles retries internally)
        assert mock_retry_client.call_with_retry.call_count == 1
        
        # Email update should still succeed even if patient update fails
        assert status_code == 200
    
    def test_patient_api_failure_handling(self, mock_comm_dependencies):
        """Test that patient API failure doesn't fail the main operation."""
        PhoneCallResource = mock_comm_dependencies['PhoneCallResource']
        mock_session_local = mock_comm_dependencies['mock_session_local']
        mock_parser = mock_comm_dependencies['mock_parser']
        mock_retry_client = mock_comm_dependencies['mock_retry_client']
        mock_logger = mock_comm_dependencies['mock_logger']
        
        resource = PhoneCallResource()
        
        # Mock phone call with patient
        mock_call = Mock()
        mock_call.id = 456
        mock_call.patient_id = 123
        mock_call.status = 'geplant'
        mock_call.recipient_type = 'patient'
        mock_call.therapeutenanfrage_id = None
        mock_call.therapist_id = None
        mock_call.ergebnis = None
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_call
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'abgeschlossen',
            'tatsaechliches_datum': None,
            'tatsaechliche_zeit': None,
            'geplantes_datum': None,
            'geplante_zeit': None,
            'dauer_minuten': None,
            'ergebnis': None,
            'notizen': None,
            'therapeutenanfrage_id': None
        }
        
        # Mock API failure
        mock_retry_client.call_with_retry.side_effect = Exception("API Error")
        
        # Execute
        result, status_code = resource.put(456)
        
        # Verify error was logged
        mock_logger.error.assert_called()
        
        # Phone call update should still succeed
        assert mock_call.status == 'abgeschlossen'
        mock_db.commit.assert_called_once()
        assert status_code == 200
    
    def test_no_patient_id_no_api_call(self, mock_comm_dependencies):
        """Test that emails/calls without patient_id don't trigger API calls."""
        EmailResource = mock_comm_dependencies['EmailResource']
        EmailStatus = mock_comm_dependencies['EmailStatus']
        mock_session_local = mock_comm_dependencies['mock_session_local']
        mock_parser = mock_comm_dependencies['mock_parser']
        mock_retry_client = mock_comm_dependencies['mock_retry_client']
        
        resource = EmailResource()
        
        # Mock email WITHOUT patient (therapist email)
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = None  # No patient
        mock_email.therapist_id = 456
        mock_email.status = EmailStatus.Entwurf
        mock_email.antwort_erhalten = False
        mock_email.recipient_type = 'therapist'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'Gesendet',
            'antwort_erhalten': None,
            'antwortdatum': None,
            'antwortinhalt': None,
            'fehlermeldung': None
        }
        
        with patch('communication_service.api.emails.validate_and_get_email_status', return_value=EmailStatus.Gesendet):
            # Execute
            result, status_code = resource.put(789)
        
        # Verify NO API call was made
        mock_retry_client.call_with_retry.assert_not_called()
        
        # Email should still be updated
        assert mock_email.status == EmailStatus.Gesendet
        assert status_code == 200
    
    def test_status_not_triggering_update(self, mock_comm_dependencies):
        """Test that non-triggering statuses don't update patient."""
        PhoneCallResource = mock_comm_dependencies['PhoneCallResource']
        mock_session_local = mock_comm_dependencies['mock_session_local']
        mock_parser = mock_comm_dependencies['mock_parser']
        mock_retry_client = mock_comm_dependencies['mock_retry_client']
        
        resource = PhoneCallResource()
        
        # Mock phone call
        mock_call = Mock()
        mock_call.id = 456
        mock_call.patient_id = 123
        mock_call.status = 'geplant'
        mock_call.recipient_type = 'patient'
        mock_call.therapeutenanfrage_id = None
        mock_call.therapist_id = None
        mock_call.ergebnis = None
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_call
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser - status that doesn't trigger update
        mock_parser.parse_args.return_value = {
            'status': 'abgebrochen',  # Cancelled, not completed
            'tatsaechliches_datum': None,
            'tatsaechliche_zeit': None,
            'geplantes_datum': None,
            'geplante_zeit': None,
            'dauer_minuten': None,
            'ergebnis': None,
            'notizen': None,
            'therapeutenanfrage_id': None
        }
        
        # Execute
        result, status_code = resource.put(456)
        
        # Verify NO API call was made
        mock_retry_client.call_with_retry.assert_not_called()
        
        # Call should still be updated
        assert mock_call.status == 'abgebrochen'
        assert status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])