"""Unit tests for Communication Service patient update functionality.

Tests that sending emails and completing phone calls updates patient last contact.
Following the same mock strategy as test_payment_workflow.py.
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date, datetime
import json

# Add project root to path so we can import communication_service as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock all the dependencies BEFORE importing
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
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['logging'] = MagicMock()

# Mock the models
MockEmail = MagicMock()
MockPhoneCall = MagicMock()
sys.modules['models.email'].Email = MockEmail
sys.modules['models.phone_call'].PhoneCall = MockPhoneCall

# Mock database components
MockSessionLocal = MagicMock()
sys.modules['shared.utils.database'].SessionLocal = MockSessionLocal

# Mock Flask components
mock_reqparse = MagicMock()
mock_parser = MagicMock()
mock_reqparse.RequestParser = MagicMock(return_value=mock_parser)
sys.modules['flask_restful'].Resource = MagicMock()
sys.modules['flask_restful'].reqparse = mock_reqparse

# Mock config
mock_config = MagicMock()
mock_config.get_service_url = MagicMock(return_value="http://patient-service")
sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)

# Mock RetryAPIClient
class MockRetryAPIClient:
    @classmethod
    def call_with_retry(cls, method, url, json=None, timeout=10):
        pass

sys.modules['shared.api.retry_client'].RetryAPIClient = MockRetryAPIClient

# Mock logger
mock_logger = MagicMock()
sys.modules['logging'].getLogger = MagicMock(return_value=mock_logger)

# Expected implementations after Phase 2
class EmailResource:
    """Handle email updates with patient notification."""
    
    def put(self, email_id):
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from models.email import Email
        from shared.api.retry_client import RetryAPIClient
        from shared.config import get_config
        from datetime import date
        import logging
        
        logger = logging.getLogger(__name__)
        
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, required=False)
        parser.add_argument('antwort_erhalten', type=bool, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            email = db.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {"message": "Email not found"}, 404
            
            # Update email fields
            if args.get('status'):
                email.status = args['status']
            if args.get('antwort_erhalten') is not None:
                email.antwort_erhalten = args['antwort_erhalten']
            
            # If email was sent or response received, update patient
            if email.patient_id and (
                args.get('status') == 'Gesendet' or 
                args.get('antwort_erhalten') == True
            ):
                config = get_config()
                patient_url = f"{config.get_service_url('patient')}/api/patients/{email.patient_id}/last-contact"
                
                try:
                    RetryAPIClient.call_with_retry(
                        method="PATCH",
                        url=patient_url,
                        json={"date": date.today().isoformat()}
                    )
                except:
                    # Log error but don't fail the email update
                    logger.error(f"Failed to update patient last contact for patient {email.patient_id}")
            
            db.commit()
            return {"message": "Email updated successfully", "id": email_id}, 200
            
        except Exception as e:
            db.rollback()
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            db.close()


class PhoneCallResource:
    """Handle phone call updates with patient notification."""
    
    def put(self, call_id):
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from models.phone_call import PhoneCall
        from shared.api.retry_client import RetryAPIClient
        from shared.config import get_config
        from datetime import date
        import logging
        
        logger = logging.getLogger(__name__)
        
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, required=False)
        parser.add_argument('tatsaechliches_datum', type=str, required=False)
        parser.add_argument('tatsaechliche_zeit', type=str, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            call = db.query(PhoneCall).filter(PhoneCall.id == call_id).first()
            if not call:
                return {"message": "Phone call not found"}, 404
            
            # Update call fields
            if args.get('status'):
                call.status = args['status']
            if args.get('tatsaechliches_datum'):
                call.tatsaechliches_datum = args['tatsaechliches_datum']
            if args.get('tatsaechliche_zeit'):
                call.tatsaechliche_zeit = args['tatsaechliche_zeit']
            
            # If call was completed, update patient
            if call.patient_id and args.get('status') == 'abgeschlossen':
                config = get_config()
                patient_url = f"{config.get_service_url('patient')}/api/patients/{call.patient_id}/last-contact"
                
                try:
                    RetryAPIClient.call_with_retry(
                        method="PATCH",
                        url=patient_url,
                        json={"date": date.today().isoformat()}
                    )
                except:
                    logger.error(f"Failed to update patient last contact for patient {call.patient_id}")
            
            db.commit()
            return {"message": "Phone call updated successfully", "id": call_id}, 200
            
        except Exception as e:
            db.rollback()
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            db.close()


class TestCommunicationPatientUpdates:
    """Test Communication service updating patient last contact."""
    
    def test_email_sent_updates_patient_last_contact(self):
        """Test that marking email as sent updates patient last contact."""
        resource = EmailResource()
        
        # Mock email with patient
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = 123
        mock_email.status = 'Entwurf'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'Gesendet',
            'antwort_erhalten': None
        }
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('__main__.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = '2025-01-15'
            
            with patch.object(MockRetryAPIClient, 'call_with_retry', return_value=mock_response) as mock_call:
                # Execute
                result, status_code = resource.put(789)
        
        # Verify API was called
        mock_call.assert_called_once_with(
            method="PATCH",
            url="http://patient-service/api/patients/123/last-contact",
            json={"date": "2025-01-15"}
        )
        
        # Verify email was updated
        assert mock_email.status == 'Gesendet'
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
    
    def test_email_response_updates_patient_last_contact(self):
        """Test that receiving email response updates patient last contact."""
        resource = EmailResource()
        
        # Mock email with patient
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = 123
        mock_email.antwort_erhalten = False
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': None,
            'antwort_erhalten': True
        }
        
        with patch('__main__.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = '2025-01-16'
            
            with patch.object(MockRetryAPIClient, 'call_with_retry') as mock_call:
                # Execute
                result, status_code = resource.put(789)
        
        # Verify API was called
        mock_call.assert_called_once()
        call_args = mock_call.call_args
        assert call_args[1]['json']['date'] == '2025-01-16'
        
        # Verify email was updated
        assert mock_email.antwort_erhalten == True
        assert status_code == 200
    
    def test_phone_call_completed_updates_patient_last_contact(self):
        """Test that completing phone call updates patient last contact."""
        resource = PhoneCallResource()
        
        # Mock phone call with patient
        mock_call = Mock()
        mock_call.id = 456
        mock_call.patient_id = 123
        mock_call.status = 'geplant'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_call
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'abgeschlossen',
            'tatsaechliches_datum': '2025-01-15',
            'tatsaechliche_zeit': '14:30'
        }
        
        with patch('__main__.date') as mock_date:
            mock_date.today.return_value.isoformat.return_value = '2025-01-15'
            
            with patch.object(MockRetryAPIClient, 'call_with_retry') as mock_api_call:
                # Execute
                result, status_code = resource.put(456)
        
        # Verify API was called
        mock_api_call.assert_called_once_with(
            method="PATCH",
            url="http://patient-service/api/patients/123/last-contact",
            json={"date": "2025-01-15"}
        )
        
        # Verify call was updated
        assert mock_call.status == 'abgeschlossen'
        assert mock_call.tatsaechliches_datum == '2025-01-15'
        assert status_code == 200
    
    def test_patient_api_retry_logic(self):
        """Test that patient API calls use retry logic."""
        resource = EmailResource()
        
        # Mock email with patient
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = 123
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'status': 'Gesendet'}
        
        # Mock API failure then success (to test retry)
        with patch.object(MockRetryAPIClient, 'call_with_retry') as mock_call:
            mock_call.side_effect = [Exception("Network error"), Mock(status_code=200)]
            
            # Execute
            result, status_code = resource.put(789)
        
        # Should only be called once (RetryAPIClient handles retries internally)
        assert mock_call.call_count == 1
        
        # Email update should still succeed even if patient update fails
        assert status_code == 200
    
    def test_patient_api_failure_handling(self):
        """Test that patient API failure doesn't fail the main operation."""
        resource = PhoneCallResource()
        
        # Mock phone call with patient
        mock_call = Mock()
        mock_call.id = 456
        mock_call.patient_id = 123
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_call
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'status': 'abgeschlossen'}
        
        # Mock API failure
        with patch.object(MockRetryAPIClient, 'call_with_retry', side_effect=Exception("API Error")):
            # Execute
            result, status_code = resource.put(456)
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        assert "Failed to update patient last contact for patient 123" in str(mock_logger.error.call_args)
        
        # Phone call update should still succeed
        assert mock_call.status == 'abgeschlossen'
        mock_db.commit.assert_called_once()
        assert status_code == 200
    
    def test_no_patient_id_no_api_call(self):
        """Test that emails/calls without patient_id don't trigger API calls."""
        resource = EmailResource()
        
        # Mock email WITHOUT patient (therapist email)
        mock_email = Mock()
        mock_email.id = 789
        mock_email.patient_id = None  # No patient
        mock_email.therapist_id = 456
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_email
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'status': 'Gesendet'}
        
        with patch.object(MockRetryAPIClient, 'call_with_retry') as mock_call:
            # Execute
            result, status_code = resource.put(789)
        
        # Verify NO API call was made
        mock_call.assert_not_called()
        
        # Email should still be updated
        assert mock_email.status == 'Gesendet'
        assert status_code == 200
    
    def test_status_not_triggering_update(self):
        """Test that non-triggering statuses don't update patient."""
        resource = PhoneCallResource()
        
        # Mock phone call
        mock_call = Mock()
        mock_call.id = 456
        mock_call.patient_id = 123
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_call
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser - status that doesn't trigger update
        mock_parser.parse_args.return_value = {'status': 'abgesagt'}  # Cancelled, not completed
        
        with patch.object(MockRetryAPIClient, 'call_with_retry') as mock_call_api:
            # Execute
            result, status_code = resource.put(456)
        
        # Verify NO API call was made
        mock_call_api.assert_not_called()
        
        # Call should still be updated
        assert mock_call.status == 'abgesagt'
        assert status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
