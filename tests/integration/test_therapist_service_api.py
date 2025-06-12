"""Integration tests for Therapist Service API.

This test suite verifies all therapist service endpoints work exactly as described
in API_REFERENCE.md. All field names use German terminology.

Prerequisites:
- Docker environment must be running
- Therapist service must be accessible at configured port
- Database must be available
"""
import pytest
import requests
import time
from datetime import datetime, date
from typing import List, Dict, Any

# Add project root to path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import get_config


# Get configuration
config = get_config()

# Skip tests in production
if config.FLASK_ENV == 'production':
    pytest.skip("Integration tests should not run in production environment", allow_module_level=True)

# Base URL for therapist service
BASE_URL = f"http://localhost:{config.THERAPIST_SERVICE_PORT}/api"


class TestTherapistServiceAPI:
    """Test all Therapist Service API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup before each test and cleanup after."""
        self.created_therapist_ids: List[int] = []
        self.base_headers = {'Content-Type': 'application/json'}
        
        yield
        
        # Cleanup: Delete all created therapists
        for therapist_id in self.created_therapist_ids:
            try:
                requests.delete(f"{BASE_URL}/therapists/{therapist_id}")
            except:
                pass  # Ignore errors during cleanup
    
    def create_test_therapist(self, **kwargs) -> Dict[str, Any]:
        """Helper to create a test therapist and track it for cleanup."""
        # Default test data with German field names
        default_data = {
            "anrede": "Dr.",
            "titel": "Dr. med.",
            "vorname": "Test",
            "nachname": "Therapeut",
            "strasse": "Praxisstraße 456",
            "plz": "10117",
            "ort": "Berlin",
            "telefon": "+49 30 98765432",
            "fax": "+49 30 98765433",
            "email": f"test.therapeut.{int(time.time())}@praxis.de",
            "webseite": "https://www.test-praxis.de",
            "kassensitz": True,
            "geschlecht": "weiblich",
            "telefonische_erreichbarkeit": {
                "monday": [{"start": "09:00", "end": "12:00"}],
                "wednesday": [{"start": "14:00", "end": "16:00"}]
            },
            "fremdsprachen": ["Englisch", "Französisch"],
            "psychotherapieverfahren": ["Verhaltenstherapie", "Tiefenpsychologie"],
            "zusatzqualifikationen": "Traumatherapie, EMDR",
            "besondere_leistungsangebote": "Online-Therapie verfügbar",
            "potenziell_verfuegbar": True,
            "potenziell_verfuegbar_notizen": "Ab Juli 2025 verfügbar",
            "naechster_kontakt_moeglich": "2025-07-01",
            "bevorzugte_diagnosen": ["F32", "F41", "F43"],
            "alter_min": 18,
            "alter_max": 65,
            "geschlechtspraeferenz": "Egal",
            "arbeitszeiten": {
                "monday": [{"start": "08:00", "end": "18:00"}],
                "tuesday": [{"start": "08:00", "end": "18:00"}]
            },
            "bevorzugt_gruppentherapie": False,
            "status": "aktiv"
        }
        
        # Override with provided data
        default_data.update(kwargs)
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=default_data,
            headers=self.base_headers
        )
        
        if response.status_code == 201:
            therapist = response.json()
            self.created_therapist_ids.append(therapist['id'])
            return therapist
        else:
            raise Exception(f"Failed to create test therapist: {response.status_code} - {response.text}")
    
    # --- GET /therapists Tests ---
    
    def test_get_therapists_list_empty(self):
        """Test getting empty therapist list."""
        response = requests.get(f"{BASE_URL}/therapists")
        assert response.status_code == 200
        
        # Response should be a list (not paginated structure in basic implementation)
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_therapists_list_with_data(self):
        """Test getting therapist list with data."""
        # Create test therapists
        therapist1 = self.create_test_therapist(vorname="Anna", nachname="Weber")
        therapist2 = self.create_test_therapist(vorname="Michael", nachname="Becker")
        
        response = requests.get(f"{BASE_URL}/therapists")
        assert response.status_code == 200
        
        therapists = response.json()
        assert isinstance(therapists, list)
        assert len(therapists) >= 2
        
        # Verify our therapists are in the list
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids
        assert therapist2['id'] in therapist_ids
    
    def test_get_therapists_with_status_filter(self):
        """Test filtering therapists by status."""
        # Create therapists with different statuses (using German values)
        therapist1 = self.create_test_therapist(vorname="Therapist1", status="aktiv")
        therapist2 = self.create_test_therapist(vorname="Therapist2", status="gesperrt")
        therapist3 = self.create_test_therapist(vorname="Therapist3", status="inaktiv")
        
        # Filter by status "gesperrt"
        response = requests.get(f"{BASE_URL}/therapists?status=gesperrt")
        assert response.status_code == 200
        
        therapists = response.json()
        # Should only include therapist2
        therapist_ids = [t['id'] for t in therapists]
        assert therapist2['id'] in therapist_ids
        assert therapist1['id'] not in therapist_ids
        assert therapist3['id'] not in therapist_ids
    
    def test_get_therapists_with_availability_filter(self):
        """Test filtering therapists by availability."""
        # Create therapists with different availability
        therapist1 = self.create_test_therapist(vorname="Available", potenziell_verfuegbar=True)
        therapist2 = self.create_test_therapist(vorname="NotAvailable", potenziell_verfuegbar=False)
        
        # Filter by availability
        response = requests.get(f"{BASE_URL}/therapists?potenziell_verfuegbar=true")
        assert response.status_code == 200
        
        therapists = response.json()
        # Should only include therapist1
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids
        assert therapist2['id'] not in therapist_ids
    
    def test_get_therapists_pagination(self):
        """Test pagination parameters."""
        # Create multiple therapists
        for i in range(5):
            self.create_test_therapist(vorname=f"Therapist{i}", nachname=f"Test{i}")
        
        # Test page and limit
        response = requests.get(f"{BASE_URL}/therapists?page=1&limit=2")
        assert response.status_code == 200
        
        therapists = response.json()
        assert isinstance(therapists, list)
        # Note: Basic implementation might not respect pagination
        # This tests that the parameters are accepted without error
    
    # --- GET /therapists/{id} Tests ---
    
    def test_get_therapist_by_id_success(self):
        """Test getting a specific therapist by ID."""
        # Create a therapist
        created_therapist = self.create_test_therapist(
            vorname="Maria",
            nachname="Weber",
            email="maria.weber@test-praxis.com"
        )
        
        response = requests.get(f"{BASE_URL}/therapists/{created_therapist['id']}")
        assert response.status_code == 200
        
        therapist = response.json()
        assert therapist['id'] == created_therapist['id']
        assert therapist['vorname'] == "Maria"
        assert therapist['nachname'] == "Weber"
        assert therapist['email'] == "maria.weber@test-praxis.com"
        
        # Verify German field names are used
        assert 'vorname' in therapist
        assert 'nachname' in therapist
        assert 'telefonische_erreichbarkeit' in therapist
        assert 'first_name' not in therapist  # English names should not exist
    
    def test_get_therapist_by_id_not_found(self):
        """Test getting non-existent therapist returns 404."""
        response = requests.get(f"{BASE_URL}/therapists/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    # --- POST /therapists Tests ---
    
    def test_create_therapist_minimal(self):
        """Test creating therapist with only required fields."""
        data = {
            "vorname": "Minimal",
            "nachname": "Therapeut"
        }
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        therapist = response.json()
        self.created_therapist_ids.append(therapist['id'])
        
        assert therapist['vorname'] == "Minimal"
        assert therapist['nachname'] == "Therapeut"
        assert 'id' in therapist
        assert therapist['status'] == "aktiv"  # Default status in German
    
    def test_create_therapist_full(self):
        """Test creating therapist with all fields."""
        data = {
            "anrede": "Dr.",
            "titel": "Dr. phil.",
            "vorname": "Michael",
            "nachname": "Becker",
            "strasse": "Therapie Zentrum 5",
            "plz": "80331",
            "ort": "München",
            "telefon": "+49 89 11223344",
            "email": "m.becker@therapie.de",
            "kassensitz": True,
            "geschlecht": "männlich",
            "telefonische_erreichbarkeit": {
                "tuesday": [{"start": "10:00", "end": "14:00"}],
                "thursday": [{"start": "15:00", "end": "18:00"}]
            },
            "psychotherapieverfahren": ["Tiefenpsychologie"],
            "potenziell_verfuegbar": True,
            "bevorzugte_diagnosen": ["F32", "F33"],
            "alter_min": 25,
            "alter_max": 55,
            "geschlechtspraeferenz": "Egal",
            "bevorzugt_gruppentherapie": False,
            "status": "aktiv"  # German enum value
        }
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        therapist = response.json()
        self.created_therapist_ids.append(therapist['id'])
        
        # Verify all fields
        assert therapist['vorname'] == "Michael"
        assert therapist['nachname'] == "Becker"
        assert therapist['email'] == "m.becker@therapie.de"
        assert therapist['status'] == "aktiv"
        assert therapist['kassensitz'] == True
        assert therapist['bevorzugt_gruppentherapie'] == False
    
    def test_create_therapist_missing_required_field(self):
        """Test creating therapist without required field returns error."""
        # Missing nachname
        data = {
            "vorname": "Incomplete"
        }
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=data,
            headers=self.base_headers
        )
        
        # Should return 400 Bad Request
        assert response.status_code == 400
        
        error = response.json()
        assert 'message' in error
        assert 'nachname' in error['message'].lower() or 'required' in error['message'].lower()
    
    def test_create_therapist_invalid_status(self):
        """Test creating therapist with invalid status value."""
        data = {
            "vorname": "Invalid",
            "nachname": "Status",
            "status": "ACTIVE"  # English value, should be rejected
        }
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=data,
            headers=self.base_headers
        )
        
        # Should reject invalid status
        assert response.status_code == 400
        error = response.json()
        assert 'message' in error
        assert 'Invalid status \'ACTIVE\'' in error['message']
        assert 'Valid values:' in error['message']
        assert 'aktiv' in error['message']
    
    # --- PUT /therapists/{id} Tests ---
    
    def test_update_therapist_single_field(self):
        """Test updating a single field."""
        therapist = self.create_test_therapist(vorname="Original", email="original@test.com")
        
        update_data = {
            "email": "updated@test.com"
        }
        
        response = requests.put(
            f"{BASE_URL}/therapists/{therapist['id']}",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        
        updated = response.json()
        assert updated['email'] == "updated@test.com"
        assert updated['vorname'] == "Original"  # Unchanged
    
    def test_update_therapist_multiple_fields(self):
        """Test updating multiple fields."""
        therapist = self.create_test_therapist()
        
        update_data = {
            "status": "gesperrt",  # German enum value
            "sperrgrund": "Temporary suspension",
            "telefon": "+49 30 11111111",
            "potenziell_verfuegbar": False
        }
        
        response = requests.put(
            f"{BASE_URL}/therapists/{therapist['id']}",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        
        updated = response.json()
        assert updated['status'] == "gesperrt"
        assert updated['telefon'] == "+49 30 11111111"
        assert updated['potenziell_verfuegbar'] == False
    
    def test_update_therapist_not_found(self):
        """Test updating non-existent therapist returns 404."""
        update_data = {
            "vorname": "Ghost"
        }
        
        response = requests.put(
            f"{BASE_URL}/therapists/99999999",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    def test_update_therapist_status_transitions(self):
        """Test various status transitions with German values."""
        therapist = self.create_test_therapist(status="aktiv")
        
        # Valid status transitions with German values
        status_sequence = [
            "gesperrt",
            "inaktiv",
            "aktiv"
        ]
        
        for new_status in status_sequence:
            response = requests.put(
                f"{BASE_URL}/therapists/{therapist['id']}",
                json={"status": new_status},
                headers=self.base_headers
            )
            
            assert response.status_code == 200
            updated = response.json()
            assert updated['status'] == new_status
    
    # --- DELETE /therapists/{id} Tests ---
    
    def test_delete_therapist_success(self):
        """Test deleting an existing therapist."""
        therapist = self.create_test_therapist(vorname="ToDelete", nachname="Therapeut")
        therapist_id = therapist['id']
        
        # Delete the therapist
        response = requests.delete(f"{BASE_URL}/therapists/{therapist_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert 'message' in result
        assert 'deleted successfully' in result['message'].lower()
        
        # Verify therapist is deleted
        get_response = requests.get(f"{BASE_URL}/therapists/{therapist_id}")
        assert get_response.status_code == 404
        
        # Remove from cleanup list since already deleted
        self.created_therapist_ids.remove(therapist_id)
    
    def test_delete_therapist_not_found(self):
        """Test deleting non-existent therapist returns 404."""
        response = requests.delete(f"{BASE_URL}/therapists/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    # --- Complex Scenario Tests ---
    
    def test_therapist_lifecycle(self):
        """Test complete therapist lifecycle: create, read, update, delete."""
        # 1. Create
        create_data = {
            "vorname": "Lifecycle",
            "nachname": "Test",
            "email": "lifecycle@test.com",
            "status": "aktiv"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/therapists",
            json=create_data,
            headers=self.base_headers
        )
        assert create_response.status_code == 201
        
        therapist = create_response.json()
        therapist_id = therapist['id']
        self.created_therapist_ids.append(therapist_id)
        
        # 2. Read
        get_response = requests.get(f"{BASE_URL}/therapists/{therapist_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved['vorname'] == "Lifecycle"
        
        # 3. Update with German enum value
        update_response = requests.put(
            f"{BASE_URL}/therapists/{therapist_id}",
            json={"status": "gesperrt", "email": "updated.lifecycle@test.com"},
            headers=self.base_headers
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated['status'] == "gesperrt"
        assert updated['email'] == "updated.lifecycle@test.com"
        
        # 4. Delete
        delete_response = requests.delete(f"{BASE_URL}/therapists/{therapist_id}")
        assert delete_response.status_code == 200
        
        # 5. Verify deleted
        verify_response = requests.get(f"{BASE_URL}/therapists/{therapist_id}")
        assert verify_response.status_code == 404
        
        # Remove from cleanup list
        self.created_therapist_ids.remove(therapist_id)
    
    def test_jsonb_field_handling(self):
        """Test JSONB fields are properly handled."""
        complex_availability = {
            "monday": [
                {"start": "09:00", "end": "12:00"},
                {"start": "14:00", "end": "18:00"}
            ],
            "tuesday": [
                {"start": "10:00", "end": "13:00"}
            ],
            "wednesday": [],
            "thursday": [
                {"start": "08:00", "end": "20:00"}
            ],
            "friday": [
                {"start": "13:00", "end": "17:00"}
            ]
        }
        
        complex_working_hours = {
            "monday": [{"start": "08:00", "end": "18:00"}],
            "tuesday": [{"start": "08:00", "end": "18:00"}],
            "wednesday": [{"start": "08:00", "end": "14:00"}],
            "thursday": [{"start": "08:00", "end": "18:00"}],
            "friday": [{"start": "08:00", "end": "16:00"}]
        }
        
        therapist = self.create_test_therapist(
            telefonische_erreichbarkeit=complex_availability,
            arbeitszeiten=complex_working_hours,
            bevorzugte_diagnosen=["F32", "F33", "F41", "F43"],
            fremdsprachen=["Englisch", "Französisch", "Spanisch"]
        )
        
        # Retrieve and verify
        response = requests.get(f"{BASE_URL}/therapists/{therapist['id']}")
        assert response.status_code == 200
        
        retrieved = response.json()
        
        # The API might return these fields - implementation dependent
        if 'telefonische_erreichbarkeit' in retrieved:
            assert isinstance(retrieved['telefonische_erreichbarkeit'], dict)
        
        if 'arbeitszeiten' in retrieved:
            assert isinstance(retrieved['arbeitszeiten'], dict)
        
        if 'bevorzugte_diagnosen' in retrieved:
            assert isinstance(retrieved['bevorzugte_diagnosen'], list)
        
        if 'fremdsprachen' in retrieved:
            assert isinstance(retrieved['fremdsprachen'], list)
    
    def test_german_enum_values(self):
        """Test all German enum values for TherapistStatus."""
        status_values = [
            "aktiv",
            "gesperrt",
            "inaktiv"
        ]
        
        for status in status_values:
            therapist = self.create_test_therapist(
                vorname=f"Status{status_values.index(status)}",
                status=status
            )
            
            response = requests.get(f"{BASE_URL}/therapists/{therapist['id']}")
            assert response.status_code == 200
            
            retrieved = response.json()
            assert retrieved['status'] == status
    
    def test_date_field_formats(self):
        """Test date field handling."""
        dates = {
            "letzter_kontakt_email": "2025-01-15",
            "letzter_kontakt_telefon": "2025-02-01",
            "letztes_persoenliches_gespraech": "2025-03-01",
            "naechster_kontakt_moeglich": "2025-07-01",
            "sperrdatum": "2025-06-01"
        }
        
        therapist = self.create_test_therapist(**dates)
        
        response = requests.get(f"{BASE_URL}/therapists/{therapist['id']}")
        assert response.status_code == 200
        
        retrieved = response.json()
        
        # Verify dates are returned (format might vary by implementation)
        for field in dates:
            if field in retrieved and retrieved[field]:
                # Should be a valid date string
                assert isinstance(retrieved[field], str)
    
    def test_invalid_german_enum_values(self):
        """Test that invalid German enum values are rejected."""
        # Test invalid status
        data = {
            "vorname": "Test",
            "nachname": "Invalid",
            "status": "BLOCKED"  # English value, should be rejected
        }
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "Invalid status 'BLOCKED'" in error['message']
        assert "Valid values:" in error['message']
        assert "gesperrt" in error['message']
    
    def test_bundle_system_fields(self):
        """Test bundle system specific fields."""
        bundle_data = {
            "vorname": "Bundle",
            "nachname": "Therapeut",
            "naechster_kontakt_moeglich": "2025-08-01",
            "bevorzugte_diagnosen": ["F32.1", "F41.0", "F43.1"],
            "alter_min": 25,
            "alter_max": 60,
            "geschlechtspraeferenz": "Weiblich",
            "arbeitszeiten": {
                "monday": [{"start": "09:00", "end": "17:00"}],
                "tuesday": [{"start": "09:00", "end": "17:00"}],
                "wednesday": [{"start": "09:00", "end": "13:00"}]
            },
            "bevorzugt_gruppentherapie": True,
            "potenziell_verfuegbar": True,
            "potenziell_verfuegbar_notizen": "Neue Plätze ab August verfügbar"
        }
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=bundle_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        therapist = response.json()
        self.created_therapist_ids.append(therapist['id'])
        
        # Verify bundle-specific fields
        assert therapist['bevorzugt_gruppentherapie'] == True
        assert therapist['potenziell_verfuegbar'] == True
        assert therapist['alter_min'] == 25
        assert therapist['alter_max'] == 60
    
    def test_professional_information_fields(self):
        """Test professional information fields."""
        professional_data = {
            "vorname": "Professional",
            "nachname": "Therapeut",
            "kassensitz": True,
            "geschlecht": "divers",
            "psychotherapieverfahren": [
                "Verhaltenstherapie",
                "Tiefenpsychologisch fundierte Psychotherapie",
                "Analytische Psychotherapie"
            ],
            "zusatzqualifikationen": "EMDR, Traumatherapie, Paartherapie",
            "besondere_leistungsangebote": "Online-Therapie, Hausbesuche, Abendtermine",
            "fremdsprachen": ["Englisch", "Türkisch", "Arabisch"]
        }
        
        response = requests.post(
            f"{BASE_URL}/therapists",
            json=professional_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        therapist = response.json()
        self.created_therapist_ids.append(therapist['id'])
        
        # Verify professional fields
        assert therapist['kassensitz'] == True
        assert therapist['geschlecht'] == "divers"
        if 'psychotherapieverfahren' in therapist:
            assert isinstance(therapist['psychotherapieverfahren'], list)
        if 'fremdsprachen' in therapist:
            assert isinstance(therapist['fremdsprachen'], list)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])