"""Unit tests for therapist blocking cascade to Matching service.

Tests that blocking/unblocking a therapist calls the Matching service cascade endpoints.
Following the same mock strategy as test_payment_workflow.py.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date
import json


# Expected implementation after Phase 2
class TherapistResource:
    """Expected implementation of therapist update with cascade."""
    
    def put(self, therapist_id):
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from models.therapist import Therapist
        from shared.api.retry_client import RetryAPIClient
        from shared.config import get_config
        import requests
        
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, required=False)
        parser.add_argument('sperrgrund', type=str, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
            if not therapist:
                return {"message": "Therapist not found"}, 404
            
            config = get_config()
            
            # Check if status is changing to "gesperrt"
            if args.get('status') == 'gesperrt' and therapist.status != 'gesperrt':
                # Call Matching service BEFORE updating status
                matching_url = f"{config.get_service_url('matching')}/api/matching/cascade/therapist-blocked"
                
                try:
                    response = RetryAPIClient.call_with_retry(
                        method="POST",
                        url=matching_url,
                        json={
                            "therapist_id": therapist_id,
                            "reason": args.get('sperrgrund', 'Status changed to blocked')
                        }
                    )
                    
                    if response.status_code != 200:
                        return {
                            "message": f"Cannot block therapist: Matching service error: {response.text}"
                        }, 500
                        
                except requests.RequestException as e:
                    return {
                        "message": f"Cannot block therapist: Matching service unavailable: {str(e)}"
                    }, 503
            
            # Check if status is changing from "gesperrt" to "aktiv"
            elif args.get('status') == 'aktiv' and therapist.status == 'gesperrt':
                # Call Matching service for unblocking
                matching_url = f"{config.get_service_url('matching')}/api/matching/cascade/therapist-unblocked"
                
                try:
                    response = RetryAPIClient.call_with_retry(
                        method="POST",
                        url=matching_url,
                        json={"therapist_id": therapist_id}
                    )
                except:
                    pass  # Unblocking cascade is non-critical
            
            # Update therapist
            if args.get('status'):
                therapist.status = args['status']
            if args.get('sperrgrund'):
                therapist.sperrgrund = args['sperrgrund']
            
            db.commit()
            return {"message": "Therapist updated successfully", "id": therapist_id}, 200
            
        except Exception as e:
            db.rollback()
            return {"message": f"Database error: {str(e)}"}, 500
        finally:
            db.close()


class TestTherapistBlockingCascade:
    """Test therapist blocking/unblocking with cascade to Matching service."""
    
    def test_block_therapist_calls_matching_api(self):
        """Test that blocking therapist calls Matching service cascade endpoint."""
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from shared.api.retry_client import RetryAPIClient
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = 'aktiv'  # Currently active
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        SessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'status': 'gesperrt',
            'sperrgrund': 'Test reason'
        }
        reqparse.RequestParser.return_value = mock_parser
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"cancelled_anfragen": 3}'
        
        with patch.object(RetryAPIClient, 'call_with_retry', return_value=mock_response) as mock_call:
            # Execute
            result, status_code = resource.put(456)
        
        # Verify API was called
        mock_call.assert_called_once_with(
            method="POST",
            url="http://matching-service/api/matching/cascade/therapist-blocked",
            json={
                "therapist_id": 456,
                "reason": "Test reason"
            }
        )
        
        # Verify therapist was updated
        assert mock_therapist.status == 'gesperrt'
        assert mock_therapist.sperrgrund == 'Test reason'
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
        assert result['message'] == "Therapist updated successfully"
    
    def test_block_therapist_rollback_on_matching_failure(self):
        """Test that therapist blocking is rolled back if Matching service fails."""
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from shared.api.retry_client import RetryAPIClient
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = 'aktiv'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        SessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'status': 'gesperrt',
            'sperrgrund': 'Test reason'
        }
        reqparse.RequestParser.return_value = mock_parser
        
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        
        with patch.object(RetryAPIClient, 'call_with_retry', return_value=mock_response):
            # Execute
            result, status_code = resource.put(456)
        
        # Verify therapist was NOT updated
        assert mock_therapist.status == 'aktiv'  # Still active
        mock_db.commit.assert_not_called()
        
        # Verify error response
        assert status_code == 500
        assert "Cannot block therapist: Matching service error" in result['message']
    
    def test_unblock_therapist_calls_matching_api(self):
        """Test that unblocking therapist calls Matching service cascade endpoint."""
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from shared.api.retry_client import RetryAPIClient
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = 'gesperrt'  # Currently blocked
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        SessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'status': 'aktiv',
            'sperrgrund': None
        }
        reqparse.RequestParser.return_value = mock_parser
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(RetryAPIClient, 'call_with_retry', return_value=mock_response) as mock_call:
            # Execute
            result, status_code = resource.put(456)
        
        # Verify API was called
        mock_call.assert_called_once_with(
            method="POST",
            url="http://matching-service/api/matching/cascade/therapist-unblocked",
            json={"therapist_id": 456}
        )
        
        # Verify therapist was updated
        assert mock_therapist.status == 'aktiv'
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200
    
    def test_unblock_therapist_non_critical_failure(self):
        """Test that unblocking continues even if cascade fails (non-critical)."""
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from shared.api.retry_client import RetryAPIClient
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = 'gesperrt'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        SessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'status': 'aktiv',
            'sperrgrund': None
        }
        reqparse.RequestParser.return_value = mock_parser
        
        # Mock API failure (but non-critical for unblocking)
        with patch.object(RetryAPIClient, 'call_with_retry', 
                         side_effect=Exception("Connection error")):
            # Execute
            result, status_code = resource.put(456)
        
        # Verify therapist was still updated (non-critical failure)
        assert mock_therapist.status == 'aktiv'
        mock_db.commit.assert_called_once()
        
        # Verify success response
        assert status_code == 200
    
    def test_status_change_not_to_gesperrt_no_cascade(self):
        """Test that changing status to something other than gesperrt doesn't trigger cascade."""
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from shared.api.retry_client import RetryAPIClient
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = 'aktiv'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        SessionLocal.return_value = mock_db
        
        # Mock request parser - changing to inaktiv (not gesperrt)
        mock_parser = Mock()
        mock_parser.parse_args.return_value = {
            'status': 'inaktiv',
            'sperrgrund': None
        }
        reqparse.RequestParser.return_value = mock_parser
        
        with patch.object(RetryAPIClient, 'call_with_retry') as mock_call:
            # Execute
            result, status_code = resource.put(456)
            
            # Verify NO API call was made
            mock_call.assert_not_called()
        
        # Verify therapist was updated
        assert mock_therapist.status == 'inaktiv'
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])