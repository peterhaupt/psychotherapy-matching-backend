"""Unit tests for symptom validation logic in Phase 2.

These tests will FAIL with the current codebase but will PASS after Phase 2 implementation.
Tests cover the new JSONB array symptom field validation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from typing import List

# The approved symptom list from Phase 2 requirements
APPROVED_SYMPTOMS = [
    # HÄUFIGSTE ANLIEGEN (Top 5)
    "Depression / Niedergeschlagenheit",
    "Ängste / Panikattacken",
    "Burnout / Erschöpfung",
    "Schlafstörungen",
    "Stress / Überforderung",
    # STIMMUNG & GEFÜHLE
    "Trauer / Verlust",
    "Reizbarkeit / Wutausbrüche",
    "Stimmungsschwankungen",
    "Innere Leere",
    "Einsamkeit",
    # DENKEN & GRÜBELN
    "Sorgen / Grübeln",
    "Selbstzweifel",
    "Konzentrationsprobleme",
    "Negative Gedanken",
    "Entscheidungsschwierigkeiten",
    # KÖRPER & GESUNDHEIT
    "Psychosomatische Beschwerden",
    "Chronische Schmerzen",
    "Essstörungen",
    "Suchtprobleme (Alkohol/Drogen)",
    "Sexuelle Probleme",
    # BEZIEHUNGEN & SOZIALES
    "Beziehungsprobleme",
    "Familienkonflikte",
    "Sozialer Rückzug",
    "Mobbing",
    "Trennungsschmerz",
    # BESONDERE BELASTUNGEN
    "Traumatische Erlebnisse",
    "Zwänge",
    "Selbstverletzung",
    "Suizidgedanken",
    "Identitätskrise"
]


class TestSymptomValidation:
    """Test symptom validation logic for Phase 2 JSONB array implementation."""
    
    @pytest.mark.parametrize("symptom", APPROVED_SYMPTOMS)
    def test_valid_symptoms_accepted(self, symptom):
        """Test that all 30 approved symptoms are individually accepted."""
        # This will test the validation function once it's implemented
        from patient_service.validation import validate_symptoms  # Will be implemented in Phase 2
        
        # Single valid symptom should pass
        result = validate_symptoms([symptom])
        assert result is True, f"Valid symptom '{symptom}' should be accepted"
    
    @pytest.mark.parametrize("invalid_symptom", [
        "Kopfschmerzen",  # Not in list
        "depression",  # Wrong case
        "Depression/Niedergeschlagenheit",  # Wrong separator
        "Depression  /  Niedergeschlagenheit",  # Extra spaces
        "Angst",  # Partial match
        "",  # Empty string
        "Unknown Symptom",
        "Test Symptom",
        123,  # Not a string
        None  # None value
    ])
    def test_invalid_symptom_rejected(self, invalid_symptom):
        """Test that various invalid symptom strings are rejected."""
        from patient_service.validation import validate_symptoms
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([invalid_symptom])
        
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_minimum_one_symptom_required(self):
        """Test that empty array should fail - at least 1 symptom required."""
        from patient_service.validation import validate_symptoms
        
        # Empty array should fail
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([])
        
        assert "Between 1 and 3 symptoms required" in str(exc_info.value)
    
    def test_maximum_three_symptoms_allowed(self):
        """Test that 4+ symptoms should fail - maximum 3 allowed."""
        from patient_service.validation import validate_symptoms
        
        # Select 4 valid symptoms
        four_symptoms = APPROVED_SYMPTOMS[:4]
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(four_symptoms)
        
        assert "Between 1 and 3 symptoms required" in str(exc_info.value)
    
    def test_exactly_one_symptom_valid(self):
        """Test that exactly one valid symptom passes."""
        from patient_service.validation import validate_symptoms
        
        result = validate_symptoms(["Depression / Niedergeschlagenheit"])
        assert result is True
    
    def test_exactly_two_symptoms_valid(self):
        """Test that exactly two valid symptoms pass."""
        from patient_service.validation import validate_symptoms
        
        result = validate_symptoms([
            "Depression / Niedergeschlagenheit",
            "Schlafstörungen"
        ])
        assert result is True
    
    def test_exactly_three_symptoms_valid(self):
        """Test that exactly three valid symptoms pass."""
        from patient_service.validation import validate_symptoms
        
        result = validate_symptoms([
            "Depression / Niedergeschlagenheit",
            "Schlafstörungen",
            "Ängste / Panikattacken"
        ])
        assert result is True
    
    def test_mixed_valid_invalid_symptoms(self):
        """Test that mix of valid and invalid symptoms should fail."""
        from patient_service.validation import validate_symptoms
        
        mixed = [
            "Depression / Niedergeschlagenheit",  # Valid
            "Invalid Symptom",  # Invalid
            "Schlafstörungen"  # Valid
        ]
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(mixed)
        
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_duplicate_symptoms_counted(self):
        """Test that same symptom twice counts as 2 symptoms."""
        from patient_service.validation import validate_symptoms
        
        # Same symptom twice should be allowed (counts as 2)
        result = validate_symptoms([
            "Depression / Niedergeschlagenheit",
            "Depression / Niedergeschlagenheit"
        ])
        assert result is True
        
        # But 3 of the same + 1 different should fail (4 total)
        with pytest.raises(ValueError):
            validate_symptoms([
                "Depression / Niedergeschlagenheit",
                "Depression / Niedergeschlagenheit",
                "Depression / Niedergeschlagenheit",
                "Schlafstörungen"
            ])
    
    def test_symptom_case_sensitive(self):
        """Test that exact case match is required."""
        from patient_service.validation import validate_symptoms
        
        # Wrong case should fail
        with pytest.raises(ValueError):
            validate_symptoms(["depression / niedergeschlagenheit"])  # lowercase
        
        with pytest.raises(ValueError):
            validate_symptoms(["DEPRESSION / NIEDERGESCHLAGENHEIT"])  # uppercase
    
    def test_symptom_with_extra_whitespace(self):
        """Test that symptoms with extra whitespace should be rejected."""
        from patient_service.validation import validate_symptoms
        
        # Extra spaces should fail
        with pytest.raises(ValueError):
            validate_symptoms(["  Depression / Niedergeschlagenheit  "])
        
        with pytest.raises(ValueError):
            validate_symptoms(["Depression  /  Niedergeschlagenheit"])
    
    def test_null_symptome_field(self):
        """Test that None should fail."""
        from patient_service.validation import validate_symptoms
        
        with pytest.raises(ValueError):
            validate_symptoms(None)
    
    def test_symptome_not_array(self):
        """Test that string instead of array should fail."""
        from patient_service.validation import validate_symptoms
        
        # String instead of array
        with pytest.raises(ValueError):
            validate_symptoms("Depression / Niedergeschlagenheit")
        
        # Dict instead of array
        with pytest.raises(ValueError):
            validate_symptoms({"symptom": "Depression / Niedergeschlagenheit"})


class TestPatientModelSymptoms:
    """Test Patient model handling of JSONB symptom field."""
    
    def test_patient_creation_with_symptom_array(self):
        """Test creating patient with symptom array."""
        from models.patient import Patient
        from shared.utils.database import SessionLocal
        
        db = SessionLocal()
        try:
            patient_data = {
                "anrede": "Herr",
                "geschlecht": "männlich",
                "vorname": "Test",
                "nachname": "Patient",
                "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"]  # JSONB array
            }
            
            patient = Patient(**patient_data)
            db.add(patient)
            db.commit()
            
            # Verify symptome is stored as array
            assert isinstance(patient.symptome, list)
            assert len(patient.symptome) == 2
            assert "Depression / Niedergeschlagenheit" in patient.symptome
            
        finally:
            db.rollback()
            db.close()
    
    def test_patient_update_symptom_validation(self):
        """Test that patient update validates symptoms."""
        from patient_service.api.patients import PatientResource
        
        resource = PatientResource()
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Mock existing patient
            mock_patient = Mock()
            mock_patient.id = 1
            mock_session.query().filter().first.return_value = mock_patient
            
            # Try to update with invalid symptoms (4 symptoms)
            response, status_code = resource.put(
                1,
                symptome=["Symptom1", "Symptom2", "Symptom3", "Symptom4"]
            )
            
            assert status_code == 400
            assert "Between 1 and 3 symptoms required" in response['message']


class TestAPIEndpointSymptoms:
    """Test API endpoints handle symptom arrays correctly."""
    
    def test_post_patient_with_symptom_array(self):
        """Test POST /api/patients with symptom array."""
        from patient_service.api.patients import PatientListResource
        
        resource = PatientListResource()
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            request_data = {
                "anrede": "Frau",
                "geschlecht": "weiblich",
                "vorname": "Maria",
                "nachname": "Muster",
                "symptome": [
                    "Ängste / Panikattacken",
                    "Schlafstörungen"
                ]
            }
            
            with patch('flask.request.get_json', return_value=request_data):
                response, status_code = resource.post()
                
                # Should succeed with valid symptoms
                assert status_code == 201
    
    def test_get_patient_returns_symptom_array(self):
        """Test GET /api/patients/<id> returns symptoms as array."""
        from patient_service.api.patients import PatientResource
        
        resource = PatientResource()
        
        with patch('shared.utils.database.SessionLocal') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            # Mock patient with symptom array
            mock_patient = Mock()
            mock_patient.id = 1
            mock_patient.symptome = ["Depression / Niedergeschlagenheit", "Burnout / Erschöpfung"]
            mock_session.query().filter().first.return_value = mock_patient
            
            response = resource.get(1)
            
            # Verify symptoms returned as array
            assert isinstance(response['symptome'], list)
            assert len(response['symptome']) == 2


class TestDatabaseMigration:
    """Test database migration from TEXT to JSONB."""
    
    def test_symptome_field_is_jsonb(self):
        """Test that symptome field is JSONB type in database."""
        from sqlalchemy import inspect
        from models.patient import Patient
        from shared.utils.database import engine
        
        inspector = inspect(engine)
        columns = inspector.get_columns('patienten', schema='patient_service')
        
        symptome_column = next(c for c in columns if c['name'] == 'symptome')
        
        # Should be JSONB type after migration
        assert str(symptome_column['type']) == 'JSONB'
    
    def test_diagnosis_field_removed(self):
        """Test that diagnose field has been removed."""
        from sqlalchemy import inspect
        from shared.utils.database import engine
        
        inspector = inspect(engine)
        columns = inspector.get_columns('patienten', schema='patient_service')
        
        column_names = [c['name'] for c in columns]
        
        # diagnose should not exist
        assert 'diagnose' not in column_names
    
    def test_ptv11_fields_removed(self):
        """Test that PTV11 fields have been removed."""
        from sqlalchemy import inspect
        from shared.utils.database import engine
        
        inspector = inspect(engine)
        columns = inspector.get_columns('patienten', schema='patient_service')
        
        column_names = [c['name'] for c in columns]
        
        # PTV11 fields should not exist
        assert 'hat_ptv11' not in column_names
        assert 'psychotherapeutische_sprechstunde' not in column_names