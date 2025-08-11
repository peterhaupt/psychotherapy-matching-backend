"""Unit tests for patient deletion cascade to Matching service.

Tests that deleting a patient calls the Matching service to cancel active searches.
Following the same mock strategy as test_payment_workflow.py.
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date
import json

# Add project root to path so we can import patient_service as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock all the dependencies BEFORE importing
sys.modules['models'] = MagicMock()
sys.modules['models.patient'] = MagicMock()
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

# Mock the Patient model
MockPatient = MagicMock()
sys.modules['models.patient'].Patient = MockPatient

# Mock database components
MockSessionLocal = MagicMock()
sys.modules['shared.utils.database'].SessionLocal = MockSessionLocal

# Mock Flask components
sys.modules['flask_restful'].Resource = MagicMock()

# Mock config
mock_config = MagicMock()
mock_config.get_service_url = MagicMock(return_value="http://matching-service")
sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)

# Mock RetryAPIClient
class MockRetryAPIClient:
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    @classmethod
    def call_with_retry(cls, method, url, json=None, timeout=10):
        # This will be mocked in tests
        pass

sys.modules['shared.api.retry_client'].RetryAPIClient = MockRetryAPIClient

# Mock requests module for the implementation
mock_requests = MagicMock()
sys.modules['requests'] = mock_requests

# Expected implementation after Phase 2
class PatientResource:
    """Expected implementation of patient deletion with cascade."""
    
    def delete(self, patient_id):
        from shared.utils.database import SessionLocal
        from models.patient import Patient
        from shared.api.retry_client import RetryAPIClient
        from shared.config import get_config
        import requests
        
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {"message": "Patient not found"}, 404
            
            # Call Matching service BEFORE deleting patient
            config = get_config()
            matching_url = f"{config.get_service_url('matching')}/api/matching/cascade/patient-deleted"
            
            try:
                response = RetryAPIClient.call_with_retry(
                    method="POST",
                    url=matching_url,
                    json={"patient_id": patient_id}
                )
                
                if response.status_code != 200:
                    # Matching service couldn't process cascade
                    return {
                        "message": f"Cannot delete patient: Matching service error: {response.text}"
                    }, 500
                    
            except requests.RequestException as e:
                # Network or timeout error after retries
                return {
                    "message": f"Cannot delete patient: Matching service unavailable: {str(e)}"
                }, 503
            
            # Now safe to delete patient
            db.delete(patient)
            db.commit()
            
            return {"message": "Patient deleted successfully"}, 200
            
        except Exception as e:
            db.rollback()
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            db.close()


class TestPatientDeletionCascade:
    """Test patient deletion with cascade to Matching service."""
    
    def test_delete_patient_calls_matching_api(self):
        """Test that deleting patient calls Matching service cascade endpoint."""
        resource = PatientResource()
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.id = 123
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"cancelled_searches": 2}'
        
        with patch.object(MockRetryAPIClient, 'call_with_retry', return_value=mock_response) as mock_call:
            # Execute
            result, status_code = resource.delete(123)
        
        # Verify API was called
        mock_call.assert_called_once_with(
            method="POST",
            url="http://matching-service/api/matching/cascade/patient-deleted",
            json={"patient_id": 123}
        )
        
        # Verify patient was deleted
        mock_db.delete.assert_called_once_with(mock_patient)
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
        assert result['message'] == "Patient deleted successfully"
    
    def test_delete_patient_rollback_on_matching_failure(self):
        """Test that patient deletion is rolled back if Matching service fails."""
        resource = PatientResource()
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.id = 123
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        
        with patch.object(MockRetryAPIClient, 'call_with_retry', return_value=mock_response):
            # Execute
            result, status_code = resource.delete(123)
        
        # Verify patient was NOT deleted
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
        
        # Verify error response
        assert status_code == 500
        assert "Cannot delete patient: Matching service error" in result['message']
    
    def test_delete_patient_retries_on_network_error(self):
        """Test that deletion retries on network errors."""
        resource = PatientResource()
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.id = 123
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock network error
        mock_requests.RequestException = Exception
        
        with patch.object(MockRetryAPIClient, 'call_with_retry', 
                         side_effect=Exception("Connection timeout")):
            # Execute
            result, status_code = resource.delete(123)
        
        # Verify patient was NOT deleted
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
        
        # Verify service unavailable response
        assert status_code == 503
        assert "Matching service unavailable" in result['message']
    
    def test_delete_nonexistent_patient(self):
        """Test deleting a patient that doesn't exist."""
        resource = PatientResource()
        
        # Mock database session - no patient found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Execute
        result, status_code = resource.delete(999)
        
        # Verify
        assert status_code == 404
        assert result['message'] == "Patient not found"
        
        # Verify no API call was made
        with patch.object(MockRetryAPIClient, 'call_with_retry') as mock_call:
            mock_call.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
