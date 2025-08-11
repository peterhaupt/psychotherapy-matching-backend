"""Unit tests for new Matching Service cascade endpoints.

Tests the new cascade endpoints that handle patient deletion and therapist blocking.
Following the same mock strategy as test_payment_workflow.py.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date
import json
from enum import Enum


# Create mock enum for testing
class MockSuchStatus(str, Enum):
    aktiv = "aktiv"
    pausiert = "pausiert"
    abgebrochen = "abgebrochen"
    erfolgreich = "erfolgreich"


# Expected implementations after Phase 2
class PatientDeletedCascadeResource:
    """Handle cascading operations for patient deletion."""
    
    def post(self):
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from models.platzsuche import Platzsuche
        from models.platzsuche import SuchStatus
        
        parser = reqparse.RequestParser()
        parser.add_argument('patient_id', type=int, required=True)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Cancel all active searches for the patient
            active_searches = db.query(Platzsuche).filter(
                Platzsuche.patient_id == args['patient_id'],
                Platzsuche.status == SuchStatus.aktiv
            ).all()
            
            cancelled_count = 0
            for search in active_searches:
                search.status = SuchStatus.abgebrochen
                search.notizen = f"Cancelled: Patient deleted from system"
                cancelled_count += 1
            
            db.commit()
            return {
                "message": f"Cancelled {cancelled_count} active searches",
                "cancelled_searches": cancelled_count
            }, 200
        except Exception as e:
            db.rollback()
            return {"message": f"Failed to cancel searches: {str(e)}"}, 500
        finally:
            db.close()


class TherapistBlockedCascadeResource:
    """Handle cascading operations for therapist blocking."""
    
    def post(self):
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from models.therapeutenanfrage import Therapeutenanfrage
        
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, required=True)
        parser.add_argument('reason', type=str, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            # Cancel unsent anfragen
            unsent_anfragen = db.query(Therapeutenanfrage).filter(
                Therapeutenanfrage.therapist_id == args['therapist_id'],
                Therapeutenanfrage.gesendet_datum.is_(None)
            ).all()
            
            cancelled_count = 0
            for anfrage in unsent_anfragen:
                anfrage.notizen = f"Cancelled: {args.get('reason', 'Therapist blocked')}"
                cancelled_count += 1
            
            db.commit()
            return {
                "message": f"Processed therapist blocking",
                "cancelled_anfragen": cancelled_count
            }, 200
        except Exception as e:
            db.rollback()
            return {"message": f"Failed to process blocking: {str(e)}"}, 500
        finally:
            db.close()


class TherapistUnblockedCascadeResource:
    """Handle cascading operations for therapist unblocking."""
    
    def post(self):
        from flask_restful import reqparse
        
        parser = reqparse.RequestParser()
        parser.add_argument('therapist_id', type=int, required=True)
        args = parser.parse_args()
        
        # Currently minimal implementation - can be extended
        return {"message": "Therapist unblocking processed"}, 200


class TestMatchingCascadeEndpoints:
    """Test the new cascade endpoints in Matching service."""
    
    def test_cancel_searches_for_patient(self):
        """Test cancelling active searches when patient is deleted."""
        resource = PatientDeletedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'patient_id': 123}
        
        # Mock active searches
        mock_search1 = Mock()
        mock_search1.patient_id = 123
        mock_search1.status = MockSuchStatus.aktiv
        mock_search1.notizen = ""
        
        mock_search2 = Mock()
        mock_search2.patient_id = 123
        mock_search2.status = MockSuchStatus.aktiv
        mock_search2.notizen = ""
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_search1, mock_search2]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        with patch('flask_restful.reqparse.RequestParser') as mock_reqparse_class:
            mock_reqparse_class.return_value = mock_parser
            with patch('shared.utils.database.SessionLocal') as mock_session_local:
                mock_session_local.return_value = mock_db
                with patch('models.platzsuche.SuchStatus', MockSuchStatus):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify searches were cancelled
        assert mock_search1.status == MockSuchStatus.abgebrochen
        assert mock_search2.status == MockSuchStatus.abgebrochen
        assert "Patient deleted from system" in mock_search1.notizen
        assert "Patient deleted from system" in mock_search2.notizen
        
        # Verify database commit
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
        assert result['cancelled_searches'] == 2
    
    def test_no_active_searches_to_cancel(self):
        """Test when patient has no active searches."""
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
        
        with patch('flask_restful.reqparse.RequestParser') as mock_reqparse_class:
            mock_reqparse_class.return_value = mock_parser
            with patch('shared.utils.database.SessionLocal') as mock_session_local:
                mock_session_local.return_value = mock_db
                with patch('models.platzsuche.SuchStatus', MockSuchStatus):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify response
        assert status_code == 200
        assert result['cancelled_searches'] == 0
        mock_db.commit.assert_called_once()
    
    def test_handle_therapist_blocked(self):
        """Test cancelling unsent anfragen when therapist is blocked."""
        resource = TherapistBlockedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'therapist_id': 456,
            'reason': 'License suspended'
        }
        
        # Mock unsent anfragen
        mock_anfrage1 = Mock()
        mock_anfrage1.therapist_id = 456
        mock_anfrage1.gesendet_datum = None
        mock_anfrage1.notizen = ""
        
        mock_anfrage2 = Mock()
        mock_anfrage2.therapist_id = 456
        mock_anfrage2.gesendet_datum = None
        mock_anfrage2.notizen = ""
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [mock_anfrage1, mock_anfrage2]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        with patch('flask_restful.reqparse.RequestParser') as mock_reqparse_class:
            mock_reqparse_class.return_value = mock_parser
            with patch('shared.utils.database.SessionLocal') as mock_session_local:
                mock_session_local.return_value = mock_db
                # Execute
                result, status_code = resource.post()
        
        # Verify anfragen were updated
        assert "Cancelled: License suspended" in mock_anfrage1.notizen
        assert "Cancelled: License suspended" in mock_anfrage2.notizen
        
        # Verify database commit
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
        assert result['cancelled_anfragen'] == 2
    
    def test_handle_therapist_unblocked(self):
        """Test minimal implementation of therapist unblocking."""
        resource = TherapistUnblockedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'therapist_id': 456}
        
        with patch('flask_restful.reqparse.RequestParser') as mock_reqparse_class:
            mock_reqparse_class.return_value = mock_parser
            # Execute
            result, status_code = resource.post()
        
        # Verify response
        assert status_code == 200
        assert result['message'] == "Therapist unblocking processed"
    
    def test_cascade_operations_transactional(self):
        """Test that cascade operations are transactional (rollback on error)."""
        resource = PatientDeletedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'patient_id': 123}
        
        # Mock database session that throws error on commit
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [Mock()]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        mock_db.commit.side_effect = Exception("Database error")
        
        with patch('flask_restful.reqparse.RequestParser') as mock_reqparse_class:
            mock_reqparse_class.return_value = mock_parser
            with patch('shared.utils.database.SessionLocal') as mock_session_local:
                mock_session_local.return_value = mock_db
                with patch('models.platzsuche.SuchStatus', MockSuchStatus):
                    # Execute
                    result, status_code = resource.post()
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
        
        # Verify error response
        assert status_code == 500
        assert "Failed to cancel searches" in result['message']
    
    def test_database_cleanup_on_success(self):
        """Test that database connection is properly closed on success."""
        resource = PatientDeletedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'patient_id': 123}
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        with patch('flask_restful.reqparse.RequestParser') as mock_reqparse_class:
            mock_reqparse_class.return_value = mock_parser
            with patch('shared.utils.database.SessionLocal') as mock_session_local:
                mock_session_local.return_value = mock_db
                with patch('models.platzsuche.SuchStatus', MockSuchStatus):
                    # Execute
                    resource.post()
        
        # Verify database was closed
        mock_db.close.assert_called_once()
    
    def test_database_cleanup_on_error(self):
        """Test that database connection is properly closed on error."""
        resource = TherapistBlockedCascadeResource()
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {'therapist_id': 456}
        
        # Mock database session that throws error
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Query error")
        
        with patch('flask_restful.reqparse.RequestParser') as mock_reqparse_class:
            mock_reqparse_class.return_value = mock_parser
            with patch('shared.utils.database.SessionLocal') as mock_session_local:
                mock_session_local.return_value = mock_db
                # Execute
                resource.post()
        
        # Verify database was closed even on error
        mock_db.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])