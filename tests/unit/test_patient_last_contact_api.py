"""Unit tests for new Patient Service last contact update endpoint.

Tests the PATCH /patients/{id}/last-contact endpoint that will be called by Communication service.
Following the same mock strategy as test_payment_workflow.py.
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date, datetime
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

# Create mock enums
from enum import Enum

class MockPatientenstatus(str, Enum):
    offen = "offen"
    auf_der_Suche = "auf_der_Suche"
    in_Therapie = "in_Therapie"
    Therapie_abgeschlossen = "Therapie_abgeschlossen"

# Mock the Patient model
MockPatient = MagicMock()
sys.modules['models.patient'].Patient = MockPatient
sys.modules['models.patient'].Patientenstatus = MockPatientenstatus

# Mock database components
MockSessionLocal = MagicMock()
sys.modules['shared.utils.database'].SessionLocal = MockSessionLocal

# Mock Flask components
mock_request = MagicMock()
mock_reqparse = MagicMock()
mock_parser = MagicMock()
mock_reqparse.RequestParser = MagicMock(return_value=mock_parser)
sys.modules['flask'].request = mock_request
sys.modules['flask'].jsonify = MagicMock()
sys.modules['flask_restful'].Resource = MagicMock()
sys.modules['flask_restful'].reqparse = mock_reqparse

# Mock config
mock_config = MagicMock()
sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)

# Now import the REAL implementation (assuming it exists after Phase 2)
# For now, we'll define the expected implementation
class PatientLastContactResource:
    """Expected implementation of the new endpoint."""
    def patch(self, patient_id):
        from flask_restful import reqparse
        from shared.utils.database import SessionLocal
        from models.patient import Patient
        
        parser = reqparse.RequestParser()
        parser.add_argument('date', type=str, required=False)
        args = parser.parse_args()
        
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {"message": "Patient not found"}, 404
            
            # Use provided date or today
            contact_date = args.get('date') or date.today().isoformat()
            patient.letzter_kontakt = contact_date
            
            db.commit()
            return {"message": "Last contact updated", "letzter_kontakt": contact_date}, 200
        finally:
            db.close()


class TestPatientLastContactAPI:
    """Test the new PATCH endpoint for updating patient last contact."""
    
    def test_update_last_contact_success(self):
        """Test successful update of patient last contact."""
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
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {'date': '2025-01-15'}
        
        # Execute
        result, status_code = resource.patch(123)
        
        # Verify
        assert status_code == 200
        assert result['message'] == "Last contact updated"
        assert result['letzter_kontakt'] == '2025-01-15'
        assert mock_patient.letzter_kontakt == '2025-01-15'
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_patient_not_found(self):
        """Test update when patient doesn't exist."""
        resource = PatientLastContactResource()
        
        # Mock database session - no patient found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None  # Patient not found
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Execute
        result, status_code = resource.patch(999)
        
        # Verify
        assert status_code == 404
        assert result['message'] == "Patient not found"
        mock_db.commit.assert_not_called()
        mock_db.close.assert_called_once()
    
    def test_update_last_contact_uses_today_if_no_date(self):
        """Test that endpoint uses today's date if no date provided."""
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
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser - no date provided
        mock_parser.parse_args.return_value = {'date': None}
        
        # Mock date.today()
        with patch('__main__.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 20)
            mock_date.today.return_value.isoformat.return_value = '2025-01-20'
            
            # Execute
            result, status_code = resource.patch(123)
        
        # Verify
        assert status_code == 200
        assert mock_patient.letzter_kontakt == '2025-01-20'
    
    def test_update_last_contact_idempotent(self):
        """Test that updating with same date is idempotent."""
        resource = PatientLastContactResource()
        
        # Mock patient with existing date
        mock_patient = Mock()
        mock_patient.id = 123
        mock_patient.letzter_kontakt = '2025-01-15'
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_patient
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        MockSessionLocal.return_value = mock_db
        
        # Mock request parser - same date
        mock_parser.parse_args.return_value = {'date': '2025-01-15'}
        
        # Execute twice
        result1, status1 = resource.patch(123)
        result2, status2 = resource.patch(123)
        
        # Verify both succeed
        assert status1 == 200
        assert status2 == 200
        assert mock_patient.letzter_kontakt == '2025-01-15'
        assert mock_db.commit.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
