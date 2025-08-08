"""Unit tests for payment confirmation workflow in Phase 2.

These tests will FAIL with the current codebase but will PASS after Phase 2 implementation.
Tests cover payment tracking, zahlungsreferenz extraction, and automatic status transitions.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session


class TestZahlungsreferenzExtraction:
    """Test extraction of zahlungsreferenz from registration token."""
    
    def test_extract_zahlungsreferenz_from_token(self):
        """Test extracting first 8 characters from 64-character token."""
        from patient_service.utils.payment import extract_zahlungsreferenz  # Will be implemented
        
        # Full 64-character token
        full_token = "a7f3e9b2c4d8f1a6e5b9c3d7f2a8e4b1c6d9f3a7e2b5c8d1f4a9e3b7c2d6f8a0"
        
        # Should extract first 8 characters
        zahlungsreferenz = extract_zahlungsreferenz(full_token)
        
        assert zahlungsreferenz == "a7f3e9b2"
        assert len(zahlungsreferenz) == 8
    
    def test_zahlungsreferenz_validation(self):
        """Test that zahlungsreferenz must be exactly 8 characters."""
        from patient_service.validation import validate_zahlungsreferenz  # Will be implemented
        
        # Valid 8-character reference
        assert validate_zahlungsreferenz("a7f3e9b2") is True
        
        # Too short
        with pytest.raises(ValueError) as exc_info:
            validate_zahlungsreferenz("a7f3e9")
        assert "must be exactly 8 characters" in str(exc_info.value)
        
        # Too long
        with pytest.raises(ValueError):
            validate_zahlungsreferenz("a7f3e9b2c")
        
        # Empty
        with pytest.raises(ValueError):
            validate_zahlungsreferenz("")
        
        # None
        with pytest.raises(ValueError):
            validate_zahlungsreferenz(None)
    
    def test_zahlungsreferenz_stored_in_patient(self):
        """Test that zahlungsreferenz is stored in patient record."""
        from models.patient import Patient
        
        patient = Patient(
            anrede="Herr",
            geschlecht="männlich",
            vorname="Test",
            nachname="Patient",
            zahlungsreferenz="a7f3e9b2"
        )
        
        assert patient.zahlungsreferenz == "a7f3e9b2"
        assert hasattr(patient, 'zahlungsreferenz')


class TestPaymentConfirmation:
    """Test payment confirmation and automatic status changes."""
    
    def test_payment_confirmation_triggers_status_change(self):
        """Test that confirming payment changes status from offen → auf_der_suche."""
        from patient_service.services import PaymentService  # Will be implemented
        from models.patient import Patient, Patientenstatus
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Create patient with contracts signed
            patient = Mock(spec=Patient)
            patient.id = 1
            patient.vertraege_unterschrieben = True
            patient.zahlung_eingegangen = False
            patient.status = Patientenstatus.offen
            patient.startdatum = None
            
            mock_session.query().filter().first.return_value = patient
            
            # Mock current date
            with patch('datetime.date.today', return_value=date(2025, 1, 15)):
                # Confirm payment
                service = PaymentService()
                result = service.confirm_payment(patient_id=1)
                
                # Verify changes
                assert patient.zahlung_eingegangen is True
                assert patient.status == Patientenstatus.auf_der_suche
                assert patient.startdatum == date(2025, 1, 15)
                assert result['status_changed'] is True
    
    def test_payment_confirmation_sets_startdatum(self):
        """Test that payment confirmation sets startdatum to today when conditions met."""
        from patient_service.services import PaymentService
        from models.patient import Patient
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            patient = Mock(spec=Patient)
            patient.vertraege_unterschrieben = True
            patient.zahlung_eingegangen = False
            patient.startdatum = None
            
            mock_session.query().filter().first.return_value = patient
            
            # Mock current date
            with patch('datetime.date.today', return_value=date(2025, 1, 15)):
                service = PaymentService()
                service.confirm_payment(patient_id=1)
                
                # startdatum should be set to today
                assert patient.startdatum == date(2025, 1, 15)
    
    def test_payment_without_contracts_no_status_change(self):
        """Test that payment without signed contracts doesn't change status."""
        from patient_service.services import PaymentService
        from models.patient import Patient, Patientenstatus
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            patient = Mock(spec=Patient)
            patient.vertraege_unterschrieben = False  # Contracts not signed
            patient.zahlung_eingegangen = False
            patient.status = Patientenstatus.offen
            patient.startdatum = None
            
            mock_session.query().filter().first.return_value = patient
            
            service = PaymentService()
            result = service.confirm_payment(patient_id=1)
            
            # Payment confirmed but status unchanged
            assert patient.zahlung_eingegangen is True
            assert patient.status == Patientenstatus.offen  # No change
            assert patient.startdatum is None  # Not set
            assert result['status_changed'] is False
    
    def test_payment_already_confirmed_idempotent(self):
        """Test that re-confirming payment doesn't change dates or status."""
        from patient_service.services import PaymentService
        from models.patient import Patient, Patientenstatus
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Patient with payment already confirmed
            patient = Mock(spec=Patient)
            patient.zahlung_eingegangen = True  # Already confirmed
            patient.status = Patientenstatus.auf_der_suche
            patient.startdatum = date(2025, 1, 10)  # Already set
            
            mock_session.query().filter().first.return_value = patient
            
            service = PaymentService()
            
            # Mock current date (different from startdatum)
            with patch('datetime.date.today', return_value=date(2025, 1, 15)):
                result = service.confirm_payment(patient_id=1)
            
            # Nothing should change
            assert patient.zahlung_eingegangen is True
            assert patient.status == Patientenstatus.auf_der_suche
            assert patient.startdatum == date(2025, 1, 10)  # Unchanged
            assert result['already_confirmed'] is True
    
    def test_startdatum_not_overwritten(self):
        """Test that if startdatum already set, it's not overwritten."""
        from patient_service.services import PaymentService
        from models.patient import Patient
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            original_date = date(2025, 1, 5)
            patient = Mock(spec=Patient)
            patient.vertraege_unterschrieben = True
            patient.zahlung_eingegangen = False
            patient.startdatum = original_date  # Already has a date
            
            mock_session.query().filter().first.return_value = patient
            
            service = PaymentService()
            
            # Mock current date (different from startdatum)
            with patch('datetime.date.today', return_value=date(2025, 1, 15)):
                service.confirm_payment(patient_id=1)
            
            # startdatum should remain unchanged
            assert patient.startdatum == original_date
    
    def test_status_transition_publishes_event(self):
        """Test that status change publishes Kafka event."""
        from patient_service.services import PaymentService
        from models.patient import Patient, Patientenstatus
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            with patch('events.producers.publish_patient_status_changed') as mock_publish:
                mock_session = Mock()
                mock_db.return_value = mock_session
                
                patient = Mock(spec=Patient)
                patient.id = 1
                patient.vertraege_unterschrieben = True
                patient.zahlung_eingegangen = False
                patient.status = Patientenstatus.offen
                
                mock_session.query().filter().first.return_value = patient
                
                service = PaymentService()
                service.confirm_payment(patient_id=1)
                
                # Verify event was published
                mock_publish.assert_called_once()
                call_args = mock_publish.call_args[0]
                assert call_args[0] == 1  # patient_id
                assert call_args[1] == "offen"  # old_status
                assert call_args[2] == "auf_der_suche"  # new_status
    
    def test_payment_confirmation_with_different_initial_statuses(self):
        """Test that only 'offen' status transitions to 'auf_der_suche'."""
        from patient_service.services import PaymentService
        from models.patient import Patient, Patientenstatus
        
        test_cases = [
            (Patientenstatus.offen, Patientenstatus.auf_der_suche, True),  # Should change
            (Patientenstatus.auf_der_suche, Patientenstatus.auf_der_suche, False),  # No change
            (Patientenstatus.in_Therapie, Patientenstatus.in_Therapie, False),  # No change
            (Patientenstatus.Suche_abgebrochen, Patientenstatus.Suche_abgebrochen, False),  # No change
        ]
        
        for initial_status, expected_status, should_change in test_cases:
            with patch('shared.utils.database.SessionLocal') as mock_db:
                mock_session = Mock()
                mock_db.return_value = mock_session
                
                patient = Mock(spec=Patient)
                patient.vertraege_unterschrieben = True
                patient.zahlung_eingegangen = False
                patient.status = initial_status
                
                mock_session.query().filter().first.return_value = patient
                
                service = PaymentService()
                result = service.confirm_payment(patient_id=1)
                
                assert patient.status == expected_status
                assert result['status_changed'] == should_change
    
    def test_concurrent_payment_confirmation(self):
        """Test handling of concurrent payment confirmations (race condition)."""
        from patient_service.services import PaymentService
        from sqlalchemy.exc import IntegrityError
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Simulate race condition with IntegrityError
            mock_session.commit.side_effect = IntegrityError("", "", "")
            
            service = PaymentService()
            
            with pytest.raises(IntegrityError):
                service.confirm_payment(patient_id=1)
            
            # Verify rollback was called
            mock_session.rollback.assert_called()


class TestPaymentAPIEndpoints:
    """Test API endpoints for payment functionality."""
    
    def test_payment_confirmation_endpoint(self):
        """Test PUT /api/patients/<id>/payment endpoint."""
        from patient_service.api.patients import PatientPaymentResource  # Will be implemented
        
        resource = PatientPaymentResource()
        
        with patch('patient_service.services.PaymentService') as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.confirm_payment.return_value = {
                'success': True,
                'status_changed': True,
                'new_status': 'auf_der_suche'
            }
            
            response, status_code = resource.put(patient_id=1)
            
            assert status_code == 200
            assert response['success'] is True
            assert response['status_changed'] is True
    
    def test_get_payment_status_endpoint(self):
        """Test GET /api/patients/<id>/payment endpoint."""
        from patient_service.api.patients import PatientPaymentResource
        
        resource = PatientPaymentResource()
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            patient = Mock()
            patient.zahlung_eingegangen = True
            patient.zahlungsreferenz = "a7f3e9b2"
            patient.startdatum = date(2025, 1, 15)
            
            mock_session.query().filter().first.return_value = patient
            
            response = resource.get(patient_id=1)
            
            assert response['zahlung_eingegangen'] is True
            assert response['zahlungsreferenz'] == "a7f3e9b2"
            assert response['startdatum'] == "2025-01-15"


class TestReactFrontendIntegration:
    """Test React frontend payment features."""
    
    def test_payment_checkbox_updates_patient(self):
        """Test that React frontend payment checkbox triggers backend update."""
        # This is more of an integration test placeholder
        # Real implementation would test the React component
        pass
    
    def test_zahlungsreferenz_displayed_in_ui(self):
        """Test that zahlungsreferenz is displayed in React UI."""
        # Placeholder for React component test
        pass


class TestDatabaseSchema:
    """Test database schema changes for payment fields."""
    
    def test_zahlungsreferenz_field_exists(self):
        """Test that zahlungsreferenz field exists in database."""
        from sqlalchemy import inspect
        from shared.utils.database import engine
        
        inspector = inspect(engine)
        columns = inspector.get_columns('patienten', schema='patient_service')
        
        column_names = [c['name'] for c in columns]
        
        # zahlungsreferenz should exist
        assert 'zahlungsreferenz' in column_names
        
        # Check type and length
        zr_column = next(c for c in columns if c['name'] == 'zahlungsreferenz')
        assert 'VARCHAR' in str(zr_column['type'])
        assert zr_column['type'].length == 8
    
    def test_zahlung_eingegangen_field_exists(self):
        """Test that zahlung_eingegangen field exists in database."""
        from sqlalchemy import inspect
        from shared.utils.database import engine
        
        inspector = inspect(engine)
        columns = inspector.get_columns('patienten', schema='patient_service')
        
        column_names = [c['name'] for c in columns]
        
        # zahlung_eingegangen should exist
        assert 'zahlung_eingegangen' in column_names
        
        # Check type and default
        ze_column = next(c for c in columns if c['name'] == 'zahlung_eingegangen')
        assert 'BOOLEAN' in str(ze_column['type'])
        assert ze_column['default'] == 'false'


class TestMatchingServiceIntegration:
    """Test integration with matching service on payment confirmation."""
    
    def test_payment_triggers_platzsuche_creation(self):
        """Test that payment confirmation triggers search creation in matching service."""
        from patient_service.services import PaymentService
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            with patch('requests.post') as mock_post:
                mock_session = Mock()
                mock_db.return_value = mock_session
                
                patient = Mock()
                patient.id = 1
                patient.vertraege_unterschrieben = True
                patient.zahlung_eingegangen = False
                patient.status = "offen"
                
                mock_session.query().filter().first.return_value = patient
                
                # Mock matching service response
                mock_post.return_value.status_code = 201
                mock_post.return_value.json.return_value = {'search_id': 123}
                
                service = PaymentService()
                service.confirm_payment(patient_id=1)
                
                # Verify matching service was called
                mock_post.assert_called()
                call_args = mock_post.call_args
                assert 'platzsuchen' in call_args[0][0]  # URL contains platzsuchen
                assert call_args[1]['json']['patient_id'] == 1