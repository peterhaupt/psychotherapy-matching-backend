"""Unit tests for new Patient Service last contact update endpoint.

Tests the REAL PatientLastContactResource.patch implementation from patient_service.api.patients.
Following the same mock strategy as test_payment_workflow.py.
"""
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date, datetime
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
    
    # Mock get_config
    mock_config = MagicMock()
    sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)
    
    # Mock Flask-RESTful components
    sys.modules['flask_restful'].Resource = MagicMock()
    
    # Mock reqparse
    mock_reqparse = MagicMock()
    mock_parser = MagicMock()
    mock_reqparse.RequestParser = MagicMock(return_value=mock_parser)
    sys.modules['flask_restful'].reqparse = mock_reqparse
    
    # Mock logging
    mock_logger = MagicMock()
    sys.modules['logging'].getLogger = MagicMock(return_value=mock_logger)
    
    # Mock SQLAlchemyError
    sys.modules['sqlalchemy.exc'].SQLAlchemyError = Exception
    
    # NOW import the REAL PatientLastContactResource class after mocking
    from patient_service.api.patients import PatientLastContactResource
    
    yield {
        'PatientLastContactResource': PatientLastContactResource,
        'Patientenstatus': MockPatientenstatus,
        'mock_session_local': mock_session_local,
        'mock_config': mock_config,
        'mock_parser': mock_parser,
        'mock_logger': mock_logger
    }
    
    # Cleanup
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


class TestPatientLastContactAPI:
    """Test the PATCH endpoint for updating patient last contact."""
    
    def test_update_last_contact_success_with_date(self, mock_patient_dependencies):
        """Test successful update of patient last contact with specific date."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.id = 123
        mock_patient.letzter_kontakt = None
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser - with specific date
        mock_parser.parse_args.return_value = {'date': '2025-01-15'}
        
        # Execute
        result = resource.patch(123)
        
        # Verify
        assert result['message'] == "Last contact updated"
        assert result['letzter_kontakt'] == '2025-01-15'
        
        # Verify the patient's letzter_kontakt was updated
        assert mock_patient.letzter_kontakt == date(2025, 1, 15)
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_success_without_date(self, mock_patient_dependencies):
        """Test successful update using today's date when no date provided."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.id = 123
        mock_patient.letzter_kontakt = None
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser - no date provided
        mock_parser.parse_args.return_value = {'date': None}
        
        # Mock date.today()
        with patch('patient_service.api.patients.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 20)
            
            # Execute
            result = resource.patch(123)
        
        # Verify
        assert result['message'] == "Last contact updated"
        assert result['letzter_kontakt'] == '2025-01-20'
        
        # Verify the patient's letzter_kontakt was updated to today
        assert mock_patient.letzter_kontakt == date(2025, 1, 20)
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_patient_not_found(self, mock_patient_dependencies):
        """Test update when patient doesn't exist."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
        # Mock database session - no patient found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None  # Patient not found
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'date': '2025-01-15'}
        
        # Execute
        result, status_code = resource.patch(999)
        
        # Verify
        assert status_code == 404
        assert result['message'] == "Patient not found"
        
        # Verify no commit was called
        mock_db.commit.assert_not_called()
        
        # Verify database was still closed
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_with_invalid_date_format(self, mock_patient_dependencies):
        """Test update with invalid date format."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
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
        
        # Mock request parser - invalid date format
        mock_parser.parse_args.return_value = {'date': 'invalid-date'}
        
        # Execute
        result, status_code = resource.patch(123)
        
        # Verify error response
        assert status_code == 400
        assert "Invalid date format" in result['message']
        
        # Verify no commit was called
        mock_db.commit.assert_not_called()
        
        # Verify database was still closed
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_idempotent(self, mock_patient_dependencies):
        """Test that updating with same date is idempotent."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
        # Mock patient with existing date
        mock_patient = Mock()
        mock_patient.id = 123
        mock_patient.letzter_kontakt = date(2025, 1, 15)
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser - same date
        mock_parser.parse_args.return_value = {'date': '2025-01-15'}
        
        # Execute twice
        result1 = resource.patch(123)
        
        # Reset mock for second call
        mock_db.reset_mock()
        mock_session_local.return_value = mock_db
        
        result2 = resource.patch(123)
        
        # Verify both succeed with same result
        assert result1['message'] == "Last contact updated"
        assert result2['message'] == "Last contact updated"
        assert result1['letzter_kontakt'] == '2025-01-15'
        assert result2['letzter_kontakt'] == '2025-01-15'
        
        # Date should remain the same
        assert mock_patient.letzter_kontakt == date(2025, 1, 15)
    
    def test_update_last_contact_database_error(self, mock_patient_dependencies):
        """Test handling of database errors during update."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
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
        
        # Mock database error on commit
        mock_db.commit.side_effect = Exception("Database connection lost")
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'date': '2025-01-15'}
        
        # Execute
        result, status_code = resource.patch(123)
        
        # Verify error response
        assert status_code == 500
        assert "Database error" in result['message']
        assert "Database connection lost" in result['message']
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
        
        # Verify database was still closed
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_closes_db_on_success(self, mock_patient_dependencies):
        """Test that database connection is properly closed on success."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
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
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'date': '2025-01-15'}
        
        # Execute
        resource.patch(123)
        
        # Verify database was closed
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_closes_db_on_error(self, mock_patient_dependencies):
        """Test that database connection is properly closed on error."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
        # Mock database session - no patient found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'date': None}
        
        # Execute
        resource.patch(999)
        
        # Verify database was closed even on error
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_with_empty_date_string(self, mock_patient_dependencies):
        """Test update with empty date string uses today's date."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
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
        
        # Mock request parser - empty string date
        mock_parser.parse_args.return_value = {'date': ''}
        
        # Mock date.today()
        with patch('patient_service.api.patients.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 25)
            
            # Execute
            result = resource.patch(123)
        
        # Verify - empty string should be treated as None and use today's date
        assert result['message'] == "Last contact updated"
        assert result['letzter_kontakt'] == '2025-01-25'
        assert mock_patient.letzter_kontakt == date(2025, 1, 25)
    
    def test_update_overwrites_existing_date(self, mock_patient_dependencies):
        """Test that updating overwrites an existing last contact date."""
        PatientLastContactResource = mock_patient_dependencies['PatientLastContactResource']
        mock_session_local = mock_patient_dependencies['mock_session_local']
        mock_parser = mock_patient_dependencies['mock_parser']
        
        resource = PatientLastContactResource()
        
        # Mock patient with existing old date
        mock_patient = Mock()
        mock_patient.id = 123
        mock_patient.letzter_kontakt = date(2024, 12, 1)  # Old date
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser - new date
        mock_parser.parse_args.return_value = {'date': '2025-01-30'}
        
        # Execute
        result = resource.patch(123)
        
        # Verify the date was updated
        assert result['message'] == "Last contact updated"
        assert result['letzter_kontakt'] == '2025-01-30'
        assert mock_patient.letzter_kontakt == date(2025, 1, 30)
        
        # Verify database operations
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])