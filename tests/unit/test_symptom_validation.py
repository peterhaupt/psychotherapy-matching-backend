"""Unit tests for symptom validation logic in Phase 2.

Tests the validate_symptoms function from patient_service.api.patients.
This file contains ONLY unit tests - no integration or API endpoint tests.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock
from datetime import date

# Add project root to path so we can import patient_service as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock all the dependencies BEFORE importing - same strategy as test_gcs_file_import.py
sys.modules['models'] = MagicMock()
sys.modules['models.patient'] = MagicMock()
sys.modules['events'] = MagicMock()
sys.modules['events.producers'] = MagicMock()
sys.modules['shared'] = MagicMock()
sys.modules['shared.utils'] = MagicMock()
sys.modules['shared.utils.database'] = MagicMock()
sys.modules['shared.api'] = MagicMock()
sys.modules['shared.api.base_resource'] = MagicMock()
sys.modules['shared.config'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['flask_restful'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.exc'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Create mock enums - minimal setup just for imports to work
from enum import Enum

class MockPatientenstatus(str, Enum):
    offen = "offen"

class MockAnrede(str, Enum):
    Herr = "Herr"
    Frau = "Frau"

class MockGeschlecht(str, Enum):
    männlich = "männlich"
    weiblich = "weiblich"
    divers = "divers"
    keine_Angabe = "keine_Angabe"

# Mock the minimal required modules
sys.modules['models.patient'].Patient = MagicMock()
sys.modules['models.patient'].Patientenstatus = MockPatientenstatus
sys.modules['models.patient'].Anrede = MockAnrede
sys.modules['models.patient'].Geschlecht = MockGeschlecht
sys.modules['models.patient'].Therapeutgeschlechtspraeferenz = MagicMock()
sys.modules['models.patient'].Therapieverfahren = MagicMock()
sys.modules['shared.utils.database'].SessionLocal = MagicMock()
sys.modules['shared.config'].get_config = MagicMock()
sys.modules['shared.api.base_resource'].PaginatedListResource = MagicMock()
sys.modules['events.producers'].publish_patient_created = MagicMock()
sys.modules['events.producers'].publish_patient_updated = MagicMock()
sys.modules['events.producers'].publish_patient_deleted = MagicMock()
sys.modules['events.producers'].publish_patient_status_changed = MagicMock()
sys.modules['events.producers'].publish_patient_excluded_therapist = MagicMock()
sys.modules['imports'] = MagicMock()

# Now import ONLY what we're actually testing
from patient_service.api.patients import validate_symptoms, VALID_SYMPTOMS


class TestSymptomValidation:
    """Unit tests for the validate_symptoms function."""
    
    @pytest.mark.parametrize("symptom", VALID_SYMPTOMS)
    def test_valid_symptoms_accepted(self, symptom):
        """Test that all 30 approved symptoms are individually accepted."""
        try:
            validate_symptoms([symptom])
            # If no exception, test passes
        except ValueError as e:
            pytest.fail(f"Valid symptom '{symptom}' should be accepted, but got: {e}")
    
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
    ])
    def test_invalid_symptom_rejected(self, invalid_symptom):
        """Test that various invalid symptom strings are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([invalid_symptom])
        
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_minimum_one_symptom_required(self):
        """Test that empty array should fail - at least 1 symptom required."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([])
        
        assert "At least one symptom is required" in str(exc_info.value)
    
    def test_maximum_three_symptoms_allowed(self):
        """Test that 4+ symptoms should fail - maximum 3 allowed."""
        # Select 4 valid symptoms
        four_symptoms = VALID_SYMPTOMS[:4]
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(four_symptoms)
        
        assert "Between 1 and 3 symptoms must be selected" in str(exc_info.value)
    
    def test_exactly_one_symptom_valid(self):
        """Test that exactly one valid symptom passes."""
        try:
            validate_symptoms(["Depression / Niedergeschlagenheit"])
            # Should not raise
        except ValueError as e:
            pytest.fail(f"One valid symptom should pass, but got: {e}")
    
    def test_exactly_two_symptoms_valid(self):
        """Test that exactly two valid symptoms pass."""
        try:
            validate_symptoms([
                "Depression / Niedergeschlagenheit",
                "Schlafstörungen"
            ])
            # Should not raise
        except ValueError as e:
            pytest.fail(f"Two valid symptoms should pass, but got: {e}")
    
    def test_exactly_three_symptoms_valid(self):
        """Test that exactly three valid symptoms pass."""
        try:
            validate_symptoms([
                "Depression / Niedergeschlagenheit",
                "Schlafstörungen",
                "Ängste / Panikattacken"
            ])
            # Should not raise
        except ValueError as e:
            pytest.fail(f"Three valid symptoms should pass, but got: {e}")
    
    def test_mixed_valid_invalid_symptoms(self):
        """Test that mix of valid and invalid symptoms should fail."""
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
        # Same symptom twice should be allowed (counts as 2)
        try:
            validate_symptoms([
                "Depression / Niedergeschlagenheit",
                "Depression / Niedergeschlagenheit"
            ])
            # Should not raise
        except ValueError as e:
            pytest.fail(f"Duplicate symptoms should be allowed, but got: {e}")
        
        # But 4 of the same should fail (exceeds max of 3)
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([
                "Depression / Niedergeschlagenheit",
                "Depression / Niedergeschlagenheit",
                "Depression / Niedergeschlagenheit",
                "Depression / Niedergeschlagenheit"
            ])
        assert "Between 1 and 3 symptoms must be selected" in str(exc_info.value)
    
    def test_symptom_case_sensitive(self):
        """Test that exact case match is required."""
        # Wrong case should fail
        with pytest.raises(ValueError):
            validate_symptoms(["depression / niedergeschlagenheit"])  # lowercase
        
        with pytest.raises(ValueError):
            validate_symptoms(["DEPRESSION / NIEDERGESCHLAGENHEIT"])  # uppercase
    
    def test_symptom_with_extra_whitespace(self):
        """Test that symptoms with extra whitespace should be rejected."""
        # Extra spaces should fail
        with pytest.raises(ValueError):
            validate_symptoms(["  Depression / Niedergeschlagenheit  "])
        
        with pytest.raises(ValueError):
            validate_symptoms(["Depression  /  Niedergeschlagenheit"])
    
    def test_symptome_not_array(self):
        """Test that non-array inputs should fail appropriately."""
        # String instead of array
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms("Depression / Niedergeschlagenheit")
        assert "Symptoms must be provided as an array" in str(exc_info.value)
        
        # Dict instead of array
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms({"symptom": "Depression / Niedergeschlagenheit"})
        assert "Symptoms must be provided as an array" in str(exc_info.value)
        
        # None instead of array - treated as "empty" not "wrong type"
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(None)
        assert "At least one symptom is required" in str(exc_info.value)
    
    def test_complete_symptom_list(self):
        """Test that all 30 symptoms are present in VALID_SYMPTOMS."""
        expected_symptoms = [
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
        
        # Check that all expected symptoms are in VALID_SYMPTOMS
        for symptom in expected_symptoms:
            assert symptom in VALID_SYMPTOMS, f"Missing symptom: {symptom}"
        
        # Check count
        assert len(VALID_SYMPTOMS) == 30, f"Expected 30 symptoms, got {len(VALID_SYMPTOMS)}"
    
    def test_none_values_in_list(self):
        """Test that None values within the symptom list are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([None])
        assert "Invalid symptom" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(["Depression / Niedergeschlagenheit", None])
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_empty_strings_in_list(self):
        """Test that empty strings within the symptom list are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([""])
        assert "Invalid symptom" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(["Depression / Niedergeschlagenheit", ""])
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_whitespace_only_strings(self):
        """Test that whitespace-only strings are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(["   "])
        assert "Invalid symptom" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(["\t"])
        assert "Invalid symptom" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(["\n"])
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_numeric_values_in_list(self):
        """Test that numeric values in the list are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([123])
        assert "Invalid symptom" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([3.14])
        assert "Invalid symptom" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms(["Depression / Niedergeschlagenheit", 42])
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_boolean_values_in_list(self):
        """Test that boolean values in the list are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([True])
        assert "Invalid symptom" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([False])
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_list_values_in_list(self):
        """Test that nested lists are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([["Depression / Niedergeschlagenheit"]])
        assert "Invalid symptom" in str(exc_info.value)
    
    def test_dict_values_in_list(self):
        """Test that dict values in the list are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_symptoms([{"symptom": "Depression / Niedergeschlagenheit"}])
        assert "Invalid symptom" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])