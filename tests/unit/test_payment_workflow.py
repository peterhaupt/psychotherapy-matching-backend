"""Unit tests for payment confirmation workflow in Phase 2.

Tests cover payment tracking, zahlungsreferenz extraction, and automatic status transitions.
Uses the same strategy as test_gcs_file_import.py - mock dependencies then import real code.
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date, datetime
import json

# Add project root to path so we can import patient_service as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock all the dependencies BEFORE importing - same strategy as test_gcs_file_import.py
# The key is these modules import as "from models.patient" not "from patient_service.models.patient"
sys.modules['models'] = MagicMock()
sys.modules['models.patient'] = MagicMock()
sys.modules['events'] = MagicMock()
sys.modules['events.producers'] = MagicMock()
sys.modules['events.consumers'] = MagicMock()
sys.modules['shared'] = MagicMock()
sys.modules['shared.utils'] = MagicMock()
sys.modules['shared.utils.database'] = MagicMock()
sys.modules['shared.config'] = MagicMock()
sys.modules['shared.api'] = MagicMock()
sys.modules['shared.api.base_resource'] = MagicMock()
sys.modules['shared.kafka'] = MagicMock()
sys.modules['shared.kafka.robust_producer'] = MagicMock()
sys.modules['imports'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['flask_restful'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.exc'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['jinja2'] = MagicMock()

# Create mock enums - must match the real ones
from enum import Enum

class MockPatientenstatus(str, Enum):
    offen = "offen"
    auf_der_suche = "auf_der_suche"
    in_Therapie = "in_Therapie"
    Therapie_abgeschlossen = "Therapie_abgeschlossen"
    Suche_abgebrochen = "Suche_abgebrochen"
    Therapie_abgebrochen = "Therapie_abgebrochen"

class MockAnrede(str, Enum):
    Herr = "Herr"
    Frau = "Frau"

class MockGeschlecht(str, Enum):
    männlich = "männlich"
    weiblich = "weiblich"
    divers = "divers"
    keine_Angabe = "keine_Angabe"

# Mock the Patient model and enums
MockPatient = MagicMock()
sys.modules['models.patient'].Patient = MockPatient
sys.modules['models.patient'].Patientenstatus = MockPatientenstatus
sys.modules['models.patient'].Anrede = MockAnrede
sys.modules['models.patient'].Geschlecht = MockGeschlecht
sys.modules['models.patient'].Therapeutgeschlechtspraeferenz = MagicMock()
sys.modules['models.patient'].Therapieverfahren = MagicMock()

# Mock database components
MockSessionLocal = MagicMock()
sys.modules['shared.utils.database'].SessionLocal = MockSessionLocal
sys.modules['shared.utils.database'].Base = MagicMock()

# Mock Flask components
mock_request = MagicMock()
sys.modules['flask'].request = mock_request
sys.modules['flask'].jsonify = MagicMock()
sys.modules['flask_restful'].Resource = MagicMock()
sys.modules['flask_restful'].reqparse = MagicMock()
sys.modules['flask_restful'].fields = MagicMock()
sys.modules['flask_restful'].marshal = MagicMock(side_effect=lambda obj, fields: {})
sys.modules['flask_restful'].marshal_with = MagicMock(side_effect=lambda fields: lambda f: f)

# Mock PaginatedListResource base class
sys.modules['shared.api.base_resource'].PaginatedListResource = MagicMock()

# Mock config
mock_config = MagicMock()
mock_config.get_service_url = MagicMock(return_value="http://test-service")
sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)

# Mock ImportStatus
sys.modules['imports'].ImportStatus = MagicMock()

# Mock event producers
mock_publish_patient_created = MagicMock()
mock_publish_patient_updated = MagicMock()
mock_publish_patient_status_changed = MagicMock()
sys.modules['events.producers'].publish_patient_created = mock_publish_patient_created
sys.modules['events.producers'].publish_patient_updated = mock_publish_patient_updated
sys.modules['events.producers'].publish_patient_status_changed = mock_publish_patient_status_changed
sys.modules['events.producers'].publish_patient_deleted = MagicMock()
sys.modules['events.producers'].publish_patient_excluded_therapist = MagicMock()

# Mock Jinja2
mock_env = MagicMock()
mock_template = MagicMock()
mock_template.render = MagicMock(return_value="Email content")
mock_env.get_template = MagicMock(return_value=mock_template)
sys.modules['jinja2'].Environment = MagicMock(return_value=mock_env)
sys.modules['jinja2'].FileSystemLoader = MagicMock()

# Now import the REAL implementation - just like test_gcs_file_import.py does
from patient_service.api.patients import check_and_apply_payment_status_transition, validate_symptoms, patient_fields
from patient_service.imports.patient_importer import PatientImporter

# The approved symptom list from implementation
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


class TestZahlungsreferenzExtraction:
    """Test extraction of zahlungsreferenz from registration token."""
    
    def test_extract_zahlungsreferenz_from_token_in_import(self):
        """Test extracting first 8 characters from token during import."""
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
    
    def test_payment_confirmation_triggers_status_change(self):
        """Test that confirming payment changes status from offen → auf_der_suche."""
        # Create a mock patient
        patient = Mock()
        patient.id = 1
        patient.vertraege_unterschrieben = True
        patient.zahlung_eingegangen = True  # Payment just confirmed
        patient.status = MockPatientenstatus.offen
        patient.startdatum = None
        
        # Mock database session
        mock_db = Mock()
        
        # Mock date.today()
        with patch('patient_service.api.patients.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 15)
            
            # Mock publish event
            with patch('patient_service.api.patients.publish_patient_status_changed') as mock_publish:
                with patch('patient_service.api.patients.marshal') as mock_marshal:
                    mock_marshal.return_value = {'id': 1}
                    
                    # Call the actual function
                    check_and_apply_payment_status_transition(
                        patient, 
                        old_payment_status=False,  # Was not paid
                        db=mock_db
                    )
        
        # Verify the changes
        assert patient.status == MockPatientenstatus.auf_der_suche
        assert patient.startdatum == date(2025, 1, 15)
        
        # Verify event was published
        mock_publish.assert_called_once()
        mock_db.commit.assert_called()
    
    def test_payment_without_contracts_no_status_change(self):
        """Test that payment without signed contracts doesn't change status."""
        patient = Mock()
        patient.id = 1
        patient.vertraege_unterschrieben = False  # Contracts NOT signed
        patient.zahlung_eingegangen = True
        patient.status = MockPatientenstatus.offen
        patient.startdatum = None
        
        mock_db = Mock()
        
        check_and_apply_payment_status_transition(
            patient,
            old_payment_status=False,
            db=mock_db
        )
        
        # Status should remain unchanged
        assert patient.status == MockPatientenstatus.offen
        assert patient.startdatum is None
        
        # No event should be published
        mock_db.commit.assert_not_called()
    
    def test_payment_already_confirmed_idempotent(self):
        """Test that re-confirming payment doesn't change dates or status."""
        patient = Mock()
        patient.id = 1
        patient.zahlung_eingegangen = True  # Already paid
        patient.status = MockPatientenstatus.auf_der_suche
        patient.startdatum = date(2025, 1, 10)
        
        mock_db = Mock()
        
        # This should not trigger any changes (old_payment_status=True means already paid)
        check_and_apply_payment_status_transition(
            patient,
            old_payment_status=True,  # Was already paid
            db=mock_db
        )
        
        # Nothing should change
        assert patient.status == MockPatientenstatus.auf_der_suche
        assert patient.startdatum == date(2025, 1, 10)
        
        # No database commit needed
        mock_db.commit.assert_not_called()
    
    def test_startdatum_not_overwritten(self):
        """Test that if startdatum already set, it's not overwritten."""
        original_date = date(2025, 1, 5)
        patient = Mock()
        patient.id = 1
        patient.vertraege_unterschrieben = True
        patient.zahlung_eingegangen = True
        patient.status = MockPatientenstatus.offen
        patient.startdatum = original_date  # Already has a date
        
        mock_db = Mock()
        
        with patch('patient_service.api.patients.date') as mock_date:
            mock_date.today.return_value = date(2025, 1, 15)
            
            with patch('patient_service.api.patients.publish_patient_status_changed'):
                with patch('patient_service.api.patients.marshal'):
                    check_and_apply_payment_status_transition(
                        patient,
                        old_payment_status=False,
                        db=mock_db
                    )
        
        # startdatum should remain unchanged (not overwritten)
        assert patient.startdatum == original_date


class TestSymptomValidation:
    """Test symptom validation with new JSONB array format."""
    
    def test_validate_symptoms_function(self):
        """Test the validate_symptoms function."""
        # Valid case: 1-3 symptoms from the list
        valid_symptoms = ["Depression / Niedergeschlagenheit", "Ängste / Panikattacken"]
        try:
            validate_symptoms(valid_symptoms)  # Should not raise
        except ValueError:
            pytest.fail("Valid symptoms should not raise ValueError")
        
        # Invalid: empty list
        with pytest.raises(ValueError, match="At least one symptom is required"):
            validate_symptoms([])
        
        # Invalid: too many symptoms
        with pytest.raises(ValueError, match="Between 1 and 3 symptoms"):
            validate_symptoms([
                "Depression / Niedergeschlagenheit",
                "Ängste / Panikattacken", 
                "Burnout / Erschöpfung",
                "Schlafstörungen"
            ])
        
        # Invalid: wrong symptom
        with pytest.raises(ValueError, match="Invalid symptom"):
            validate_symptoms(["Not a valid symptom"])
        
        # Invalid: not a list
        with pytest.raises(ValueError, match="must be provided as an array"):
            validate_symptoms("Depression / Niedergeschlagenheit")
    
    def test_all_valid_symptoms_accepted(self):
        """Test that all 30 approved symptoms are accepted."""
        for symptom in VALID_SYMPTOMS:
            try:
                validate_symptoms([symptom])
            except ValueError:
                pytest.fail(f"Valid symptom '{symptom}' should be accepted")


class TestPatientImporter:
    """Test patient import functionality with payment fields."""
    
    def test_import_extracts_zahlungsreferenz(self):
        """Test that import extracts zahlungsreferenz from registration token."""
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
        assert call_args['zahlung_eingegangen'] == False  # Default for new imports
    
    def test_import_sends_confirmation_email(self):
        """Test that successful import sends confirmation email."""
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
        
        # Verify email was sent
        mock_send.assert_called_once_with(123, mock_create.call_args[0][0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])