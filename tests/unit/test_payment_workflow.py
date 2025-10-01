"""Unit tests for payment confirmation workflow in Phase 2 with VOUCHER SUPPORT.

Tests cover payment tracking, zahlungsreferenz extraction, automatic status transitions,
and voucher booking functionality.
"""
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date, datetime
import json

# The approved symptom list from implementation - kept as test data
VALID_SYMPTOMS = [
    "Depression / Niedergeschlagenheit",
    "Ängste / Panikattacken",
    "Burnout / Erschöpfung",
    "Schlafstörungen",
    "Stress / Überforderung",
    "Trauer / Verlust",
    "Reizbarkeit / Wutausbrüche",
    "Stimmungsschwankungen",
    "Innere Leere",
    "Einsamkeit",
    "Sorgen / Grübeln",
    "Selbstzweifel",
    "Konzentrationsprobleme",
    "Negative Gedanken",
    "Entscheidungsschwierigkeiten",
    "Psychosomatische Beschwerden",
    "Chronische Schmerzen",
    "Essstörungen",
    "Suchtprobleme (Alkohol/Drogen)",
    "Sexuelle Probleme",
    "Beziehungsprobleme",
    "Familienkonflikte",
    "Sozialer Rückzug",
    "Mobbing",
    "Trennungsschmerz",
    "Traumatische Erlebnisse",
    "Zwänge",
    "Selbstverletzung",
    "Suizidgedanken",
    "Identitätskrise"
]


@pytest.fixture
def mock_patient_dependencies():
    """Mock all dependencies before importing the code under test."""
    # Save original modules
    original_modules = {}
    modules_to_mock = [
        'imports',
        'imports.import_status',
        'models',
        'models.patient',
        'models.email',
        'models.phone_call',
        'shared',
        'shared.utils',
        'shared.utils.database',
        'shared.utils.object_storage',
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
        'requests.adapters',
        'requests.exceptions',
        'logging',
        'jinja2',
        'google',
        'google.cloud',
        'google.cloud.storage',
        'google.api_core',
        'google.api_core.exceptions',
    ]
    
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Mock all dependencies
    sys.modules['imports'] = MagicMock()
    sys.modules['imports.import_status'] = MagicMock()
    sys.modules['models'] = MagicMock()
    sys.modules['models.patient'] = MagicMock()
    sys.modules['models.email'] = MagicMock()
    sys.modules['models.phone_call'] = MagicMock()
    sys.modules['shared'] = MagicMock()
    sys.modules['shared.utils'] = MagicMock()
    sys.modules['shared.utils.database'] = MagicMock()
    sys.modules['shared.utils.object_storage'] = MagicMock()
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
    sys.modules['requests.adapters'] = MagicMock()
    sys.modules['requests.exceptions'] = MagicMock()
    sys.modules['logging'] = MagicMock()
    sys.modules['jinja2'] = MagicMock()
    sys.modules['google'] = MagicMock()
    sys.modules['google.cloud'] = MagicMock()
    sys.modules['google.cloud.storage'] = MagicMock()
    sys.modules['google.api_core'] = MagicMock()
    sys.modules['google.api_core.exceptions'] = MagicMock()
    
    # Set up ImportStatus in the imports module
    sys.modules['imports'].ImportStatus = MagicMock()
    
    # Create mock Patientenstatus enum
    from enum import Enum
    class MockPatientenstatus(str, Enum):
        offen = "offen"
        auf_der_Suche = "auf_der_Suche"  # Value with capital S
        in_Therapie = "in_Therapie"
        Therapie_abgeschlossen = "Therapie_abgeschlossen"
        Suche_abgebrochen = "Suche_abgebrochen"
        Therapie_abgebrochen = "Therapie_abgebrochen"
    
    # Set up the Patientenstatus in models.patient
    sys.modules['models.patient'].Patientenstatus = MockPatientenstatus
    
    # NOW import the actual functions after mocking
    from patient_service.api.patients import (
        validate_symptoms, 
        VALID_SYMPTOMS as PROD_VALID_SYMPTOMS,
        check_and_apply_payment_status_transition
    )
    from patient_service.imports.patient_importer import PatientImporter
    
    yield {
        'validate_symptoms': validate_symptoms,
        'VALID_SYMPTOMS': PROD_VALID_SYMPTOMS,
        'check_and_apply_payment_status_transition': check_and_apply_payment_status_transition,
        'PatientImporter': PatientImporter,
        'Patientenstatus': MockPatientenstatus
    }
    
    # Cleanup
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


class TestZahlungsreferenzExtraction:
    """Test extraction of zahlungsreferenz from registration token."""
    
    def test_extract_zahlungsreferenz_from_token_in_import(self, mock_patient_dependencies):
        """Test extracting first 8 characters from token during import."""
        PatientImporter = mock_patient_dependencies['PatientImporter']
        
        importer = PatientImporter()
        
        # Test data with full token
        test_data = {
            'patient_data': {
                'anrede': 'Herr',
                'geschlecht': 'männlich',
                'vorname': 'Test',
                'nachname': 'Patient',
                'symptome': ['Depression / Niedergeschlagenheit']
            },
            'registration_token': 'a7f3e9b2c4d8f1a6e5b9c3d7f2a8e4b1c6d9f3a7e2b5c8d1f4a9e3b7c2d6f8a0'
        }
        
        # Mock the _create_patient_via_api to capture the data passed
        with patch.object(importer, '_create_patient_via_api') as mock_create:
            mock_create.return_value = (True, 1, None)
            
            # Mock email sending
            with patch.object(importer, '_send_patient_confirmation_email'):
                importer.import_patient(test_data)
            
            # Check that zahlungsreferenz was extracted
            call_args = mock_create.call_args[0][0]
            assert 'zahlungsreferenz' in call_args
            assert call_args['zahlungsreferenz'] == 'a7f3e9b2'


class TestPaymentConfirmation:
    """Test payment confirmation and automatic status changes."""
    
    def test_payment_confirmation_triggers_status_change(self, mock_patient_dependencies):
        """Test that confirming payment changes status from offen → auf_der_Suche."""
        check_and_apply_payment_status_transition = mock_patient_dependencies['check_and_apply_payment_status_transition']
        Patientenstatus = mock_patient_dependencies['Patientenstatus']
        
        # Create a mock patient
        patient = Mock()
        patient.id = 1
        patient.vertraege_unterschrieben = True
        patient.zahlung_eingegangen = True  # Payment just confirmed
        patient.status = Patientenstatus.offen
        patient.startdatum = None
        patient.zahlungsreferenz = 'a7f3e9b2'  # Regular (non-voucher) reference
        patient.email = 'test@example.com'
        patient.vorname = 'Test'
        patient.nachname = 'Patient'
        patient.offen_fuer_gruppentherapie = False
        
        # Mock database session
        mock_db = Mock()
        
        # Mock date.today()
        with patch('patient_service.api.patients.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 15)
            
            # Mock the email sending function
            with patch('patient_service.api.patients._send_payment_confirmation_email') as mock_send_email:
                # Call the actual function
                check_and_apply_payment_status_transition(
                    patient, 
                    old_payment_status=False,  # Was not paid
                    db=mock_db
                )
                
                # Verify email was sent for regular payment
                mock_send_email.assert_called_once_with(1, mock_db)
        
        # Verify the changes
        assert patient.status == Patientenstatus.auf_der_Suche
        assert patient.startdatum == date(2025, 1, 15)
    
    def test_voucher_payment_skips_confirmation_email(self, mock_patient_dependencies):
        """Test that voucher bookings skip payment confirmation email."""
        check_and_apply_payment_status_transition = mock_patient_dependencies['check_and_apply_payment_status_transition']
        Patientenstatus = mock_patient_dependencies['Patientenstatus']
        
        # Create a mock voucher patient
        patient = Mock()
        patient.id = 2
        patient.vertraege_unterschrieben = True
        patient.zahlung_eingegangen = True  # Payment auto-confirmed for voucher
        patient.status = Patientenstatus.offen
        patient.startdatum = None
        patient.zahlungsreferenz = 'VOUCHER_a7f3e9b2'  # VOUCHER prefix
        
        mock_db = Mock()
        
        with patch('patient_service.api.patients.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 15)
            
            with patch('patient_service.api.patients._send_payment_confirmation_email') as mock_send_email:
                check_and_apply_payment_status_transition(
                    patient,
                    old_payment_status=False,  # Was not paid (but auto-confirmed for voucher)
                    db=mock_db
                )
                
                # Verify NO email was sent for voucher payment
                mock_send_email.assert_not_called()
        
        # Verify status still changed
        assert patient.status == Patientenstatus.auf_der_Suche
        assert patient.startdatum == date(2025, 1, 15)
    
    def test_payment_without_contracts_no_status_change(self, mock_patient_dependencies):
        """Test that payment without signed contracts doesn't change status."""
        check_and_apply_payment_status_transition = mock_patient_dependencies['check_and_apply_payment_status_transition']
        Patientenstatus = mock_patient_dependencies['Patientenstatus']
        
        patient = Mock()
        patient.id = 1
        patient.vertraege_unterschrieben = False  # Contracts NOT signed
        patient.zahlung_eingegangen = True
        patient.status = Patientenstatus.offen
        patient.startdatum = None
        patient.zahlungsreferenz = 'a7f3e9b2'
        
        mock_db = Mock()
        
        check_and_apply_payment_status_transition(
            patient,
            old_payment_status=False,
            db=mock_db
        )
        
        # Status should remain unchanged
        assert patient.status == Patientenstatus.offen
        assert patient.startdatum is None
        
        # No database commit should be called
        mock_db.commit.assert_not_called()
    
    def test_payment_already_confirmed_idempotent(self, mock_patient_dependencies):
        """Test that re-confirming payment doesn't change dates or status."""
        check_and_apply_payment_status_transition = mock_patient_dependencies['check_and_apply_payment_status_transition']
        Patientenstatus = mock_patient_dependencies['Patientenstatus']
        
        patient = Mock()
        patient.id = 1
        patient.zahlung_eingegangen = True  # Already paid
        patient.status = Patientenstatus.auf_der_Suche
        patient.startdatum = date(2025, 1, 10)
        
        mock_db = Mock()
        
        # This should not trigger any changes (old_payment_status=True means already paid)
        check_and_apply_payment_status_transition(
            patient,
            old_payment_status=True,  # Was already paid
            db=mock_db
        )
        
        # Nothing should change
        assert patient.status == Patientenstatus.auf_der_Suche
        assert patient.startdatum == date(2025, 1, 10)
        
        # No database commit needed
        mock_db.commit.assert_not_called()
    
    def test_startdatum_not_overwritten(self, mock_patient_dependencies):
        """Test that if startdatum already set, it's not overwritten."""
        check_and_apply_payment_status_transition = mock_patient_dependencies['check_and_apply_payment_status_transition']
        Patientenstatus = mock_patient_dependencies['Patientenstatus']
        
        original_date = date(2025, 1, 5)
        patient = Mock()
        patient.id = 1
        patient.vertraege_unterschrieben = True
        patient.zahlung_eingegangen = True
        patient.status = Patientenstatus.offen
        patient.startdatum = original_date  # Already has a date
        patient.zahlungsreferenz = 'a7f3e9b2'
        patient.email = 'test@example.com'
        patient.vorname = 'Test'
        patient.nachname = 'Patient'
        patient.offen_fuer_gruppentherapie = False
        
        mock_db = Mock()
        
        with patch('patient_service.api.patients.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 15)
            
            with patch('patient_service.api.patients._send_payment_confirmation_email'):
                check_and_apply_payment_status_transition(
                    patient,
                    old_payment_status=False,
                    db=mock_db
                )
        
        # startdatum should remain unchanged (not overwritten)
        assert patient.startdatum == original_date
        # Status should have changed to auf_der_Suche
        assert patient.status == Patientenstatus.auf_der_Suche


class TestSymptomValidation:
    """Test symptom validation with new JSONB array format."""
    
    def test_validate_symptoms_function(self, mock_patient_dependencies):
        """Test the validate_symptoms function."""
        validate_symptoms = mock_patient_dependencies['validate_symptoms']
        
        # Valid case: 1-6 symptoms from the list
        valid_symptoms = ["Depression / Niedergeschlagenheit", "Ängste / Panikattacken"]
        try:
            validate_symptoms(valid_symptoms)  # Should not raise
        except ValueError:
            pytest.fail("Valid symptoms should not raise ValueError")
        
        # Invalid: empty list
        with pytest.raises(ValueError, match="At least one symptom is required"):
            validate_symptoms([])
        
        # Invalid: too many symptoms
        with pytest.raises(ValueError, match="Between 1 and 6 symptoms"):
            validate_symptoms([
                "Depression / Niedergeschlagenheit",
                "Ängste / Panikattacken", 
                "Burnout / Erschöpfung",
                "Schlafstörungen",
                "Stress / Überforderung",
                "Trauer / Verlust",
                "Reizbarkeit / Wutausbrüche"
            ])
        
        # Invalid: wrong symptom
        with pytest.raises(ValueError, match="Invalid symptom"):
            validate_symptoms(["Not a valid symptom"])
        
        # Invalid: not a list
        with pytest.raises(ValueError, match="must be provided as an array"):
            validate_symptoms("Depression / Niedergeschlagenheit")
    
    def test_all_valid_symptoms_accepted(self, mock_patient_dependencies):
        """Test that all 30 approved symptoms are accepted."""
        validate_symptoms = mock_patient_dependencies['validate_symptoms']
        
        for symptom in VALID_SYMPTOMS:
            try:
                validate_symptoms([symptom])
            except ValueError:
                pytest.fail(f"Valid symptom '{symptom}' should be accepted")


class TestPatientImporter:
    """Test patient import functionality with payment fields."""
    
    def test_import_extracts_zahlungsreferenz(self, mock_patient_dependencies):
        """Test that import extracts zahlungsreferenz from registration token."""
        PatientImporter = mock_patient_dependencies['PatientImporter']
        
        importer = PatientImporter()
        
        test_data = {
            'patient_data': {
                'anrede': 'Herr',
                'geschlecht': 'männlich', 
                'vorname': 'Test',
                'nachname': 'Patient',
                'symptome': ['Depression / Niedergeschlagenheit']
            },
            'registration_token': 'a7f3e9b2c4d8f1a6e5b9c3d7f2a8e4b1'
        }
        
        with patch.object(importer, '_create_patient_via_api') as mock_create:
            mock_create.return_value = (True, 1, None)
            
            with patch.object(importer, '_send_patient_confirmation_email'):
                success, message = importer.import_patient(test_data)
        
        # Check the data passed to create_patient
        call_args = mock_create.call_args[0][0]
        assert call_args['zahlungsreferenz'] == 'a7f3e9b2'
        assert call_args['zahlung_eingegangen'] == False  # Default for non-voucher imports
    
    def test_import_sends_confirmation_email(self, mock_patient_dependencies):
        """Test that successful import sends confirmation email with voucher parameters."""
        PatientImporter = mock_patient_dependencies['PatientImporter']
        
        importer = PatientImporter()
        
        test_data = {
            'patient_data': {
                'anrede': 'Frau',
                'geschlecht': 'weiblich',
                'vorname': 'Test',
                'nachname': 'Patient',
                'email': 'test@example.com',
                'symptome': ['Stress / Überforderung']
            },
            'registration_token': 'b2c4d8f1a6e5b9c3'
        }
        
        with patch.object(importer, '_create_patient_via_api') as mock_create:
            mock_create.return_value = (True, 123, None)
            
            with patch.object(importer, '_send_patient_confirmation_email') as mock_send:
                success, message = importer.import_patient(test_data)
        
        assert success == True
        assert "Patient created with ID: 123" in message
        
        # UPDATED: Verify email was sent with new voucher parameters
        mock_send.assert_called_once_with(
            123,
            mock_create.call_args[0][0],
            False,  # is_voucher (default for non-voucher)
            0       # price_paid (default)
        )
    
    def test_voucher_import_marks_payment_and_prefix(self, mock_patient_dependencies):
        """Test that voucher imports mark payment as received with VOUCHER_ prefix."""
        PatientImporter = mock_patient_dependencies['PatientImporter']
        
        importer = PatientImporter()
        
        # Test data with voucher metadata
        test_data = {
            'patient_data': {
                'anrede': 'Herr',
                'geschlecht': 'männlich',
                'vorname': 'Voucher',
                'nachname': 'User',
                'email': 'voucher@example.com',
                'symptome': ['Burnout / Erschöpfung']
            },
            'registration_token': 'c3d4e5f6a7b8c9d0',
            'consent_metadata': {
                'voucher_booking': True,
                'price_paid': 0
            }
        }
        
        with patch.object(importer, '_create_patient_via_api') as mock_create:
            mock_create.return_value = (True, 456, None)
            
            with patch.object(importer, '_send_patient_confirmation_email') as mock_send:
                success, message = importer.import_patient(test_data)
        
        # Check the data passed to create_patient
        call_args = mock_create.call_args[0][0]
        assert call_args['zahlungsreferenz'] == 'VOUCHER_c3d4e5f6'  # With VOUCHER_ prefix
        assert call_args['zahlung_eingegangen'] == True  # Auto-confirmed for voucher
        
        # Verify email was sent with voucher parameters
        mock_send.assert_called_once_with(
            456,
            mock_create.call_args[0][0],
            True,  # is_voucher
            0      # price_paid
        )
    
    def test_voucher_import_with_missing_token(self, mock_patient_dependencies):
        """Test voucher import handles missing registration token gracefully."""
        PatientImporter = mock_patient_dependencies['PatientImporter']
        
        importer = PatientImporter()
        
        # Test data without registration token
        test_data = {
            'patient_data': {
                'anrede': 'Frau',
                'geschlecht': 'weiblich',
                'vorname': 'No',
                'nachname': 'Token',
                'email': 'notoken@example.com',
                'symptome': ['Ängste / Panikattacken']
            },
            'consent_metadata': {
                'voucher_booking': True,
                'price_paid': 0
            }
        }
        
        with patch.object(importer, '_create_patient_via_api') as mock_create:
            mock_create.return_value = (True, 789, None)
            
            with patch.object(importer, '_send_patient_confirmation_email'):
                success, message = importer.import_patient(test_data)
        
        # Check the data passed to create_patient
        call_args = mock_create.call_args[0][0]
        assert call_args['zahlungsreferenz'] == 'VOUCHER_NOREF'  # Default when no token
        assert call_args['zahlung_eingegangen'] == True  # Still auto-confirmed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])