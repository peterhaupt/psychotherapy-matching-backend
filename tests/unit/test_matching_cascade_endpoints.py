"""Unit tests for Matching Service cascade endpoints.

Tests the cascade endpoints that handle patient deletion and therapist blocking.
Following the same mock strategy as test_payment_workflow.py and test_symptom_validation.py.

This version tests the REAL implementation from matching_service.api.cascade_operations.
"""
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from enum import Enum


@pytest.fixture
def mock_matching_dependencies():
    """Mock all dependencies before importing the code under test."""
    # Save original modules to restore later
    original_modules = {}
    modules_to_mock = [
        'flask',
        'flask_restful',
        'sqlalchemy',
        'sqlalchemy.exc',
        'sqlalchemy.orm',
        'db',
        'models',
        'models.platzsuche',
        'models.therapeutenanfrage',
        'models.therapeut_anfrage_patient',
        'services',
        'events',  # Added events module
        'events.producers',  # Added events.producers submodule
        'events.consumers',  # Added events.consumers submodule
        'algorithms',  # Added algorithms module
        'algorithms.anfrage_creator',  # Added algorithms.anfrage_creator submodule
        'shared',
        'shared.utils',
        'shared.utils.database',
        'shared.config',
        'logging',
    ]
    
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Create mock enums
    class MockSuchStatus(str, Enum):
        aktiv = "aktiv"
        erfolgreich = "erfolgreich"
        pausiert = "pausiert"
        abgebrochen = "abgebrochen"
    
    # Mock all dependencies
    sys.modules['flask'] = MagicMock()
    sys.modules['flask_restful'] = MagicMock()
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlalchemy.exc'] = MagicMock()
    sys.modules['sqlalchemy.orm'] = MagicMock()
    sys.modules['db'] = MagicMock()
    sys.modules['models'] = MagicMock()
    sys.modules['models.platzsuche'] = MagicMock()
    sys.modules['models.therapeutenanfrage'] = MagicMock()
    sys.modules['models.therapeut_anfrage_patient'] = MagicMock()
    sys.modules['services'] = MagicMock()
    sys.modules['events'] = MagicMock()  # Added mock for events module
    sys.modules['events.producers'] = MagicMock()  # Added mock for events.producers
    sys.modules['events.consumers'] = MagicMock()  # Added mock for events.consumers
    sys.modules['algorithms'] = MagicMock()  # Added mock for algorithms module
    sys.modules['algorithms.anfrage_creator'] = MagicMock()  # Added mock for algorithms.anfrage_creator
    sys.modules['shared'] = MagicMock()
    sys.modules['shared.utils'] = MagicMock()
    sys.modules['shared.utils.database'] = MagicMock()
    sys.modules['shared.config'] = MagicMock()
    sys.modules['logging'] = MagicMock()
    
    # Set up the SuchStatus enum in models.platzsuche
    sys.modules['models.platzsuche'].SuchStatus = MockSuchStatus
    
    # Mock logger
    mock_logger = MagicMock()
    sys.modules['logging'].getLogger = MagicMock(return_value=mock_logger)
    
    # NOW import the actual cascade resources after mocking
    from matching_service.api.cascade_operations import (
        PatientDeletedCascadeResource,
        TherapistBlockedCascadeResource,
        TherapistUnblockedCascadeResource
    )
    
    yield {
        'PatientDeletedCascadeResource': PatientDeletedCascadeResource,
        'TherapistBlockedCascadeResource': TherapistBlockedCascadeResource,
        'TherapistUnblockedCascadeResource': TherapistUnblockedCascadeResource,
        'SuchStatus': MockSuchStatus,
        'mock_logger': mock_logger
    }
    
    # Cleanup: restore original modules
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


class TestPatientDeletedCascade:
    """Test the PatientDeletedCascadeResource."""
    
    def test_cancel_searches_for_patient(self, mock_matching_dependencies):
        """Test cancelling active searches when patient is deleted."""
        PatientDeletedCascadeResource = mock_matching_dependencies['PatientDeletedCascadeResource']
        SuchStatus = mock_matching_dependencies['SuchStatus']
        
        resource = PatientDeletedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'patient_id': 123}
        
        # Mock active searches
        mock_search1 = Mock()
        mock_search1.id = 1
        mock_search1.patient_id = 123
        mock_search1.status = SuchStatus.aktiv
        mock_search1.notizen = ""
        mock_search1.add_note = Mock()
        
        mock_search2 = Mock()
        mock_search2.id = 2
        mock_search2.patient_id = 123
        mock_search2.status = SuchStatus.aktiv
        mock_search2.notizen = ""
        mock_search2.add_note = Mock()
        
        # Mock database context
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_search1, mock_search2]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        from flask_restful import reqparse
        from db import get_db_context
        from models.platzsuche import Platzsuche
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            with patch.object(get_db_context, '__enter__', return_value=mock_db):
                with patch.object(get_db_context, '__exit__', return_value=None):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify searches were cancelled
        assert mock_search1.status == SuchStatus.abgebrochen
        assert mock_search2.status == SuchStatus.abgebrochen
        
        # Verify notes were added
        mock_search1.add_note.assert_called_once_with(
            "Cancelled: Patient deleted from system", 
            author="System"
        )
        mock_search2.add_note.assert_called_once_with(
            "Cancelled: Patient deleted from system", 
            author="System"
        )
        
        # Verify database commit
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
        assert result['cancelled_searches'] == 2
        assert result['patient_id'] == 123
    
    def test_no_active_searches_to_cancel(self, mock_matching_dependencies):
        """Test when patient has no active searches."""
        PatientDeletedCascadeResource = mock_matching_dependencies['PatientDeletedCascadeResource']
        
        resource = PatientDeletedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'patient_id': 123}
        
        # Mock no active searches
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []  # No active searches
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        from flask_restful import reqparse
        from db import get_db_context
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            with patch.object(get_db_context, '__enter__', return_value=mock_db):
                with patch.object(get_db_context, '__exit__', return_value=None):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify response
        assert status_code == 200
        assert result['cancelled_searches'] == 0
        assert result['patient_id'] == 123
        mock_db.commit.assert_called_once()
    
    def test_database_error_handling(self, mock_matching_dependencies):
        """Test error handling when database operation fails."""
        PatientDeletedCascadeResource = mock_matching_dependencies['PatientDeletedCascadeResource']
        mock_logger = mock_matching_dependencies['mock_logger']
        
        resource = PatientDeletedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'patient_id': 123}
        
        # Mock database error
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database connection failed")
        
        from flask_restful import reqparse
        from db import get_db_context
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            with patch.object(get_db_context, '__enter__', return_value=mock_db):
                with patch.object(get_db_context, '__exit__', return_value=None):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify error response
        assert status_code == 500
        assert "Failed to cancel searches" in result['message']
        assert result['patient_id'] == 123
        
        # Verify error was logged
        mock_logger.error.assert_called()


class TestTherapistBlockedCascade:
    """Test the TherapistBlockedCascadeResource."""
    
    def test_cancel_unsent_anfragen(self, mock_matching_dependencies):
        """Test cancelling unsent anfragen when therapist is blocked."""
        TherapistBlockedCascadeResource = mock_matching_dependencies['TherapistBlockedCascadeResource']
        
        resource = TherapistBlockedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'therapist_id': 456,
            'reason': 'License suspended'
        }
        
        # Mock unsent anfragen
        mock_anfrage1 = Mock()
        mock_anfrage1.id = 1
        mock_anfrage1.therapist_id = 456
        mock_anfrage1.gesendet_datum = None
        mock_anfrage1.notizen = ""
        mock_anfrage1.add_note = Mock()
        
        mock_anfrage2 = Mock()
        mock_anfrage2.id = 2
        mock_anfrage2.therapist_id = 456
        mock_anfrage2.gesendet_datum = None
        mock_anfrage2.notizen = ""
        mock_anfrage2.add_note = Mock()
        
        # Mock sent but unanswered anfragen with patients
        mock_anfrage3 = Mock()
        mock_anfrage3.id = 3
        mock_anfrage3.therapist_id = 456
        mock_anfrage3.gesendet_datum = datetime.utcnow()
        mock_anfrage3.antwort_datum = None
        
        # Mock patient search entries
        mock_search = Mock()
        mock_search.status = mock_matching_dependencies['SuchStatus'].aktiv
        mock_search.exclude_therapist = Mock()
        
        mock_anfrage_patient = Mock()
        mock_anfrage_patient.platzsuche = mock_search
        mock_anfrage_patient.platzsuche_id = 1
        
        mock_anfrage3.anfrage_patients = [mock_anfrage_patient]
        
        # Mock database context
        mock_db = Mock()
        
        # First query for unsent anfragen
        mock_query1 = Mock()
        mock_filter1 = Mock()
        mock_filter1.all.return_value = [mock_anfrage1, mock_anfrage2]
        mock_query1.filter.return_value = mock_filter1
        
        # Second query for sent but unanswered anfragen
        mock_query2 = Mock()
        mock_filter2 = Mock()
        mock_filter2.all.return_value = [mock_anfrage3]
        mock_query2.filter.return_value = mock_filter2
        
        # Configure db.query to return different results for each call
        mock_db.query.side_effect = [mock_query1, mock_query2]
        
        from flask_restful import reqparse
        from db import get_db_context
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            with patch.object(get_db_context, '__enter__', return_value=mock_db):
                with patch.object(get_db_context, '__exit__', return_value=None):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify anfragen notes were added
        mock_anfrage1.add_note.assert_called_once_with(
            "Cancelled: License suspended",
            author="System"
        )
        mock_anfrage2.add_note.assert_called_once_with(
            "Cancelled: License suspended",
            author="System"
        )
        
        # Verify therapist was added to exclusion list
        mock_search.exclude_therapist.assert_called_once_with(
            456,
            reason="Therapist blocked: License suspended"
        )
        
        # Verify database commit
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
        assert result['cancelled_anfragen'] == 2
        assert result['updated_exclusion_lists'] == 1
        assert result['therapist_id'] == 456
    
    def test_no_anfragen_to_cancel(self, mock_matching_dependencies):
        """Test when therapist has no anfragen to process."""
        TherapistBlockedCascadeResource = mock_matching_dependencies['TherapistBlockedCascadeResource']
        
        resource = TherapistBlockedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'therapist_id': 456,
            'reason': None
        }
        
        # Mock database context with no anfragen
        mock_db = Mock()
        
        # First query returns empty list
        mock_query1 = Mock()
        mock_filter1 = Mock()
        mock_filter1.all.return_value = []
        mock_query1.filter.return_value = mock_filter1
        
        # Second query returns empty list
        mock_query2 = Mock()
        mock_filter2 = Mock()
        mock_filter2.all.return_value = []
        mock_query2.filter.return_value = mock_filter2
        
        mock_db.query.side_effect = [mock_query1, mock_query2]
        
        from flask_restful import reqparse
        from db import get_db_context
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            with patch.object(get_db_context, '__enter__', return_value=mock_db):
                with patch.object(get_db_context, '__exit__', return_value=None):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify response
        assert status_code == 200
        assert result['cancelled_anfragen'] == 0
        assert result['updated_exclusion_lists'] == 0
        mock_db.commit.assert_called_once()


class TestTherapistUnblockedCascade:
    """Test the TherapistUnblockedCascadeResource."""
    
    def test_minimal_unblocking_implementation(self, mock_matching_dependencies):
        """Test minimal implementation of therapist unblocking."""
        TherapistUnblockedCascadeResource = mock_matching_dependencies['TherapistUnblockedCascadeResource']
        mock_logger = mock_matching_dependencies['mock_logger']
        
        resource = TherapistUnblockedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'therapist_id': 456}
        
        from flask_restful import reqparse
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            # Execute
            result, status_code = resource.post()
        
        # Verify response
        assert status_code == 200
        assert result['message'] == "Therapist unblocking processed"
        assert result['therapist_id'] == 456
        assert result['note'] == "Exclusion lists not automatically updated - requires manual review"
        
        # Verify it was logged
        mock_logger.info.assert_called_with(
            "Therapist unblocking processed for therapist 456 (no automatic exclusion removal)"
        )


class TestIntegrationScenarios:
    """Test more complex integration scenarios."""
    
    def test_patient_deletion_with_mixed_search_statuses(self, mock_matching_dependencies):
        """Test patient deletion when patient has searches in different statuses."""
        PatientDeletedCascadeResource = mock_matching_dependencies['PatientDeletedCascadeResource']
        SuchStatus = mock_matching_dependencies['SuchStatus']
        
        resource = PatientDeletedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'patient_id': 789}
        
        # Mock searches with different statuses
        mock_search_active = Mock()
        mock_search_active.id = 1
        mock_search_active.status = SuchStatus.aktiv
        mock_search_active.add_note = Mock()
        
        mock_search_paused = Mock()
        mock_search_paused.id = 2
        mock_search_paused.status = SuchStatus.pausiert
        
        mock_search_successful = Mock()
        mock_search_successful.id = 3
        mock_search_successful.status = SuchStatus.erfolgreich
        
        # Only active searches should be returned by the query
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_search_active]  # Only active
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        from flask_restful import reqparse
        from db import get_db_context
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            with patch.object(get_db_context, '__enter__', return_value=mock_db):
                with patch.object(get_db_context, '__exit__', return_value=None):
                    # Execute
                    result, status_code = resource.post()
        
        # Only active search should be cancelled
        assert mock_search_active.status == SuchStatus.abgebrochen
        assert result['cancelled_searches'] == 1
        
        # Paused and successful searches shouldn't be touched
        # (they weren't in the query results)
        assert mock_search_paused.status == SuchStatus.pausiert
        assert mock_search_successful.status == SuchStatus.erfolgreich
    
    def test_therapist_blocking_with_inactive_searches(self, mock_matching_dependencies):
        """Test that inactive patient searches are not updated when therapist is blocked."""
        TherapistBlockedCascadeResource = mock_matching_dependencies['TherapistBlockedCascadeResource']
        SuchStatus = mock_matching_dependencies['SuchStatus']
        
        resource = TherapistBlockedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'therapist_id': 999,
            'reason': 'Test blocking'
        }
        
        # Mock anfrage with patient in inactive search
        mock_anfrage = Mock()
        mock_anfrage.id = 1
        mock_anfrage.therapist_id = 999
        mock_anfrage.gesendet_datum = datetime.utcnow()
        mock_anfrage.antwort_datum = None
        
        # Mock patient search that is NOT active
        mock_search_cancelled = Mock()
        mock_search_cancelled.status = SuchStatus.abgebrochen  # Not active!
        mock_search_cancelled.exclude_therapist = Mock()
        
        mock_anfrage_patient = Mock()
        mock_anfrage_patient.platzsuche = mock_search_cancelled
        
        mock_anfrage.anfrage_patients = [mock_anfrage_patient]
        
        # Mock database
        mock_db = Mock()
        
        # First query (unsent) returns empty
        mock_query1 = Mock()
        mock_filter1 = Mock()
        mock_filter1.all.return_value = []
        mock_query1.filter.return_value = mock_filter1
        
        # Second query (sent but unanswered) returns the anfrage
        mock_query2 = Mock()
        mock_filter2 = Mock()
        mock_filter2.all.return_value = [mock_anfrage]
        mock_query2.filter.return_value = mock_filter2
        
        mock_db.query.side_effect = [mock_query1, mock_query2]
        
        from flask_restful import reqparse
        from db import get_db_context
        
        with patch.object(reqparse, 'RequestParser', return_value=mock_parser):
            with patch.object(get_db_context, '__enter__', return_value=mock_db):
                with patch.object(get_db_context, '__exit__', return_value=None):
                    # Execute
                    result, status_code = resource.post()
        
        # Should NOT update exclusion list for cancelled search
        mock_search_cancelled.exclude_therapist.assert_not_called()
        
        # Verify response shows no updates
        assert result['updated_exclusion_lists'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])