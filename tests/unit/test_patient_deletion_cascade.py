"""Unit tests for patient deletion cascade to Matching service.

Tests the REAL PatientResource.delete implementation from patient_service.api.patients.
Following the same mock strategy as test_payment_workflow.py.
"""
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date
from enum import Enum


@pytest.fixture
def mock_patient_dependencies():
    """Mock all dependencies before importing the code under test."""
    # Save original modules
    original_modules = {}
    modules_to_mock = [
        'events',
        'events.producers',
        'imports',
        'imports.import_status',
        'models',
        'models.patient',
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
        'sqlalchemy.orm',
        'sqlalchemy.dialects',
        'sqlalchemy.dialects.postgresql',
        'requests',
        'requests.exceptions',
        'logging',
    ]
    
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Mock all dependencies
    sys.modules['events'] = MagicMock()
    sys.modules['events.producers'] = MagicMock()
    sys.modules['imports'] = MagicMock()
    sys.modules['imports.import_status'] = MagicMock()
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
    sys.modules['sqlalchemy.dialects'] = MagicMock()
    sys.modules['sqlalchemy.dialects.postgresql'] = MagicMock()
    sys.modules['requests'] = MagicMock()
    sys.modules['requests.exceptions'] = MagicMock()
    sys.modules['logging'] = MagicMock()
    
    # Create mock Patientenstatus enum
    class MockPatientenstatus(str, Enum):
        offen = "offen"
        auf_der_Suche = "auf_der_Suche"
        in_Therapie = "in_Therapie"
        Therapie_abgeschlossen = "Therapie_abgeschlossen"
        Suche_abgebrochen = "Suche_abgebrochen"
        Therapie_abgebrochen = "Therapie_abgebrochen"
    
    # Set up the Patientenstatus in models.patient
    sys.modules['models.patient'].Patientenstatus = MockPatientenstatus
    sys.modules['models.patient'].Patient = MagicMock()
    
    # Mock SessionLocal
    mock_session_local = MagicMock()
    sys.modules['shared.utils.database'].SessionLocal = mock_session_local
    
    # Mock RetryAPIClient
    mock_retry_client = MagicMock()
    sys.modules['shared.api.retry_client'].RetryAPIClient = mock_retry_client
    
    # Mock get_config
    mock_config = MagicMock()
    mock_config.get_service_url = MagicMock(return_value="http://matching-service")
    sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)
    
    # Mock Flask-RESTful components
    sys.modules['flask_restful'].Resource = MagicMock()
    
    # Mock event publishers
    sys.modules['events.producers'].publish_patient_deleted = MagicMock()
    
    # Mock requests module
    mock_requests = MagicMock()
    mock_requests.RequestException = Exception
    sys.modules['requests'] = mock_requests
    
    # Mock logging
    mock_logger = MagicMock()
    sys.modules['logging'].getLogger = MagicMock(return_value=mock_logger)
    
    # NOW import the REAL PatientResource class after mocking
    from patient_service.api.patients import PatientResource
    
    yield {
        'PatientResource': PatientResource,
        'Patientenstatus': MockPatientenstatus,
        'mock_session_local': mock_session_local,
        'mock_retry_client': mock_retry_client,
        'mock_config': mock_config,
        'mock_requests': mock_requests,
        'mock_logger': mock_logger
    }
    
    # Cleanup
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


class TestPatientDeletionCascade:
    """Test patient deletion with cascade to Matching service."""
    
    def test_delete_patient_calls_matching_api(self, mock_patient_dependencies):
        """Test that deleting patient calls Matching service cascade endpoint."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_retry_client = mock_patient_dependencies['mock_retry_client']
        mock_config = mock_patient_dependencies['mock_config']
        
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
        
        mock_session_local.return_value = mock_db
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"cancelled_searches": 2}'
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        # Mock publish_patient_deleted
        with patch('patient_service.api.patients.publish_patient_deleted') as mock_publish:
            # Execute
            result, status_code = resource.delete(123)
        
        # Verify API was called with correct URL
        mock_retry_client.call_with_retry.assert_called_once_with(
            method="POST",
            url="http://matching-service/api/matching/cascade/patient-deleted",
            json={"patient_id": 123}
        )
        
        # Verify patient was deleted
        mock_db.delete.assert_called_once_with(mock_patient)
        mock_db.commit.assert_called_once()
        
        # Verify event was published
        mock_publish.assert_called_once_with(123, {'id': 123})
        
        # Verify response
        assert status_code == 200
        assert result['message'] == "Patient deleted successfully"
    
    def test_delete_patient_rollback_on_matching_failure(self, mock_patient_dependencies):
        """Test that patient deletion is rolled back if Matching service fails."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_retry_client = mock_patient_dependencies['mock_retry_client']
        
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
        
        mock_session_local.return_value = mock_db
        
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        # Execute
        result, status_code = resource.delete(123)
        
        # Verify patient was NOT deleted
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
        
        # Verify error response
        assert status_code == 500
        assert "Cannot delete patient: Matching service error" in result['message']
        assert "Internal server error" in result['message']
    
    def test_delete_patient_retries_on_network_error(self, mock_patient_dependencies):
        """Test that deletion retries on network errors."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_retry_client = mock_patient_dependencies['mock_retry_client']
        mock_requests = mock_patient_dependencies['mock_requests']
        
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
        
        mock_session_local.return_value = mock_db
        
        # Mock network error (RequestException)
        mock_retry_client.call_with_retry.side_effect = mock_requests.RequestException("Connection timeout")
        
        # Execute
        result, status_code = resource.delete(123)
        
        # Verify patient was NOT deleted
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
        
        # Verify service unavailable response
        assert status_code == 503
        assert "Cannot delete patient: Matching service unavailable" in result['message']
        assert "Connection timeout" in result['message']
    
    def test_delete_nonexistent_patient(self, mock_patient_dependencies):
        """Test deleting a patient that doesn't exist."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_retry_client = mock_patient_dependencies['mock_retry_client']
        
        resource = PatientResource()
        
        # Mock database session - no patient found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Execute
        result, status_code = resource.delete(999)
        
        # Verify
        assert status_code == 404
        assert result['message'] == "Patient not found"
        
        # Verify no API call was made
        mock_retry_client.call_with_retry.assert_not_called()
        
        # Verify no delete was attempted
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
    
    def test_delete_patient_database_error(self, mock_patient_dependencies):
        """Test handling of database errors during deletion."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_retry_client = mock_patient_dependencies['mock_retry_client']
        
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
        
        mock_session_local.return_value = mock_db
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        # Mock database error on delete
        mock_db.delete.side_effect = Exception("Database constraint violation")
        
        # Execute
        result, status_code = resource.delete(123)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
        
        # Verify error response
        assert status_code == 500
        assert "Database error" in result['message']
        assert "Database constraint violation" in result['message']
    
    def test_delete_patient_closes_db_on_success(self, mock_patient_dependencies):
        """Test that database connection is properly closed on success."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_retry_client = mock_patient_dependencies['mock_retry_client']
        
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
        
        mock_session_local.return_value = mock_db
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        with patch('patient_service.api.patients.publish_patient_deleted'):
            # Execute
            resource.delete(123)
        
        # Verify database was closed
        mock_db.close.assert_called_once()
    
    def test_delete_patient_closes_db_on_error(self, mock_patient_dependencies):
        """Test that database connection is properly closed on error."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        
        resource = PatientResource()
        
        # Mock database session - no patient found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Execute
        resource.delete(999)
        
        # Verify database was closed even on error
        mock_db.close.assert_called_once()
    
    def test_matching_service_url_configuration(self, mock_patient_dependencies):
        """Test that the correct matching service URL is used."""
        PatientResource = mock_patient_dependencies['PatientResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_retry_client = mock_patient_dependencies['mock_retry_client']
        mock_config = mock_patient_dependencies['mock_config']
        
        # Test with different URL configurations
        mock_config.get_service_url.return_value = "http://custom-matching:8080"
        
        resource = PatientResource()
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.id = 456
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        with patch('patient_service.api.patients.publish_patient_deleted'):
            # Execute
            resource.delete(456)
        
        # Verify the correct URL was used
        mock_config.get_service_url.assert_called_with('matching', internal=True)
        mock_retry_client.call_with_retry.assert_called_once_with(
            method="POST",
            url="http://custom-matching:8080/api/matching/cascade/patient-deleted",
            json={"patient_id": 456}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])