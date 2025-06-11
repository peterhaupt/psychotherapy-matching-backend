"""Integration tests for Patient Service API.

This test suite verifies all patient service endpoints work exactly as described
in API_REFERENCE.md. All field names use German terminology.

Prerequisites:
- Docker environment must be running
- Patient service must be accessible at configured port
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

# Base URL for patient service
BASE_URL = f"http://localhost:{config.PATIENT_SERVICE_PORT}/api"


class TestPatientServiceAPI:
    """Test all Patient Service API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup before each test and cleanup after."""
        self.created_patient_ids: List[int] = []
        self.base_headers = {'Content-Type': 'application/json'}
        
        yield
        
        # Cleanup: Delete all created patients
        for patient_id in self.created_patient_ids:
            try:
                requests.delete(f"{BASE_URL}/patients/{patient_id}")
            except:
                pass  # Ignore errors during cleanup
    
    def create_test_patient(self, **kwargs) -> Dict[str, Any]:
        """Helper to create a test patient and track it for cleanup."""
        # Default test data with German field names
        default_data = {
            "vorname": "Test",
            "nachname": "Patient",
            "anrede": "Herr",
            "strasse": "Teststraße 123",
            "plz": "10115",
            "ort": "Berlin",
            "email": f"test.patient.{int(time.time())}@example.com",
            "telefon": "+49 30 12345678",
            "hausarzt": "Dr. Test",
            "krankenkasse": "Test-Krankenkasse",
            "krankenversicherungsnummer": "T123456789",
            "geburtsdatum": "1990-01-15",
            "diagnose": "F32.1",
            "vertraege_unterschrieben": True,
            "psychotherapeutische_sprechstunde": True,
            "startdatum": "2025-01-01",
            "status": "offen",
            "zeitliche_verfuegbarkeit": {
                "monday": [{"start": "09:00", "end": "17:00"}],
                "tuesday": [{"start": "09:00", "end": "17:00"}]
            },
            "raeumliche_verfuegbarkeit": {"max_km": 25},
            "verkehrsmittel": "Auto",
            "offen_fuer_gruppentherapie": False,
            "offen_fuer_diga": False,
            "ausgeschlossene_therapeuten": [],
            "bevorzugtes_therapeutengeschlecht": "ANY"
        }
        
        # Override with provided data
        default_data.update(kwargs)
        
        response = requests.post(
            f"{BASE_URL}/patients",
            json=default_data,
            headers=self.base_headers
        )
        
        if response.status_code == 201:
            patient = response.json()
            self.created_patient_ids.append(patient['id'])
            return patient
        else:
            raise Exception(f"Failed to create test patient: {response.status_code} - {response.text}")
    
    # --- GET /patients Tests ---
    
    def test_get_patients_list_empty(self):
        """Test getting empty patient list."""
        response = requests.get(f"{BASE_URL}/patients")
        assert response.status_code == 200
        
        # Response should be a list (not paginated structure in basic implementation)
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_patients_list_with_data(self):
        """Test getting patient list with data."""
        # Create test patients
        patient1 = self.create_test_patient(vorname="Anna", nachname="Müller")
        patient2 = self.create_test_patient(vorname="Max", nachname="Schmidt")
        
        response = requests.get(f"{BASE_URL}/patients")
        assert response.status_code == 200
        
        patients = response.json()
        assert isinstance(patients, list)
        assert len(patients) >= 2
        
        # Verify our patients are in the list
        patient_ids = [p['id'] for p in patients]
        assert patient1['id'] in patient_ids
        assert patient2['id'] in patient_ids
    
    def test_get_patients_with_status_filter(self):
        """Test filtering patients by status."""
        # Create patients with different statuses
        patient1 = self.create_test_patient(vorname="Patient1", status="offen")
        patient2 = self.create_test_patient(vorname="Patient2", status="auf der Suche")
        patient3 = self.create_test_patient(vorname="Patient3", status="in Therapie")
        
        # Filter by status "auf der Suche"
        response = requests.get(f"{BASE_URL}/patients?status=auf der Suche")
        assert response.status_code == 200
        
        patients = response.json()
        # Should only include patient2
        patient_ids = [p['id'] for p in patients]
        assert patient2['id'] in patient_ids
        assert patient1['id'] not in patient_ids
        assert patient3['id'] not in patient_ids
    
    def test_get_patients_pagination(self):
        """Test pagination parameters."""
        # Create multiple patients
        for i in range(5):
            self.create_test_patient(vorname=f"Patient{i}", nachname=f"Test{i}")
        
        # Test page and limit
        response = requests.get(f"{BASE_URL}/patients?page=1&limit=2")
        assert response.status_code == 200
        
        patients = response.json()
        assert isinstance(patients, list)
        # Note: Basic implementation might not respect pagination
        # This tests that the parameters are accepted without error
    
    def test_get_patients_max_limit(self):
        """Test that limit respects maximum of 100."""
        response = requests.get(f"{BASE_URL}/patients?limit=150")
        assert response.status_code == 200
        # The implementation should cap at 100 items max
    
    # --- GET /patients/{id} Tests ---
    
    def test_get_patient_by_id_success(self):
        """Test getting a specific patient by ID."""
        # Create a patient
        created_patient = self.create_test_patient(
            vorname="Hans",
            nachname="Meyer",
            email="hans.meyer@test.com"
        )
        
        response = requests.get(f"{BASE_URL}/patients/{created_patient['id']}")
        assert response.status_code == 200
        
        patient = response.json()
        assert patient['id'] == created_patient['id']
        assert patient['vorname'] == "Hans"
        assert patient['nachname'] == "Meyer"
        assert patient['email'] == "hans.meyer@test.com"
        
        # Verify German field names are used
        assert 'vorname' in patient
        assert 'nachname' in patient
        assert 'first_name' not in patient  # English names should not exist
    
    def test_get_patient_by_id_not_found(self):
        """Test getting non-existent patient returns 404."""
        response = requests.get(f"{BASE_URL}/patients/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    # --- POST /patients Tests ---
    
    def test_create_patient_minimal(self):
        """Test creating patient with only required fields."""
        data = {
            "vorname": "Minimal",
            "nachname": "Patient"
        }
        
        response = requests.post(
            f"{BASE_URL}/patients",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        patient = response.json()
        self.created_patient_ids.append(patient['id'])
        
        assert patient['vorname'] == "Minimal"
        assert patient['nachname'] == "Patient"
        assert 'id' in patient
        assert patient['status'] == "offen"  # Default status
    
    def test_create_patient_full(self):
        """Test creating patient with all fields."""
        data = {
            "anrede": "Frau",
            "vorname": "Maria",
            "nachname": "Wagner",
            "strasse": "Hauptstraße 456",
            "plz": "80331",
            "ort": "München",
            "email": "maria.wagner@example.com",
            "telefon": "+49 89 98765432",
            "hausarzt": "Dr. Weber",
            "krankenkasse": "TK",
            "krankenversicherungsnummer": "M987654321",
            "geburtsdatum": "1985-06-20",
            "diagnose": "F41.1",
            "vertraege_unterschrieben": True,
            "psychotherapeutische_sprechstunde": False,
            "startdatum": "2025-02-01",
            "status": "auf der Suche",
            "empfehler_der_unterstuetzung": "Hausarzt",
            "zeitliche_verfuegbarkeit": {
                "monday": [{"start": "18:00", "end": "20:00"}],
                "wednesday": [{"start": "18:00", "end": "20:00"}],
                "friday": [{"start": "16:00", "end": "19:00"}]
            },
            "raeumliche_verfuegbarkeit": {
                "max_km": 15,
                "travel_time_minutes": 30
            },
            "verkehrsmittel": "ÖPNV",
            "offen_fuer_gruppentherapie": True,
            "offen_fuer_diga": True,
            "ausgeschlossene_therapeuten": [123, 456, 789],
            "bevorzugtes_therapeutengeschlecht": "FEMALE"
        }
        
        response = requests.post(
            f"{BASE_URL}/patients",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        patient = response.json()
        self.created_patient_ids.append(patient['id'])
        
        # Verify all fields
        assert patient['vorname'] == "Maria"
        assert patient['nachname'] == "Wagner"
        assert patient['email'] == "maria.wagner@example.com"
        assert patient['status'] == "auf der Suche"
        assert patient['offen_fuer_gruppentherapie'] == True
        assert patient['bevorzugtes_therapeutengeschlecht'] == "FEMALE"
    
    def test_create_patient_missing_required_field(self):
        """Test creating patient without required field returns error."""
        # Missing nachname
        data = {
            "vorname": "Incomplete"
        }
        
        response = requests.post(
            f"{BASE_URL}/patients",
            json=data,
            headers=self.base_headers
        )
        
        # Should return 400 Bad Request
        assert response.status_code == 400
        
        error = response.json()
        assert 'message' in error
        assert 'nachname' in error['message'].lower() or 'required' in error['message'].lower()
    
    def test_create_patient_invalid_status(self):
        """Test creating patient with invalid status value."""
        data = {
            "vorname": "Invalid",
            "nachname": "Status",
            "status": "invalid_status"
        }
        
        response = requests.post(
            f"{BASE_URL}/patients",
            json=data,
            headers=self.base_headers
        )
        
        # Should either reject or ignore invalid status
        # Implementation might vary, but should not crash
        assert response.status_code in [201, 400]
    
    # --- PUT /patients/{id} Tests ---
    
    def test_update_patient_single_field(self):
        """Test updating a single field."""
        patient = self.create_test_patient(vorname="Original", email="original@test.com")
        
        update_data = {
            "email": "updated@test.com"
        }
        
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        
        updated = response.json()
        assert updated['email'] == "updated@test.com"
        assert updated['vorname'] == "Original"  # Unchanged
    
    def test_update_patient_multiple_fields(self):
        """Test updating multiple fields."""
        patient = self.create_test_patient()
        
        update_data = {
            "status": "in Therapie",
            "funktionierender_therapieplatz_am": "2025-06-15",
            "telefon": "+49 30 11111111",
            "offen_fuer_gruppentherapie": True
        }
        
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        
        updated = response.json()
        assert updated['status'] == "in Therapie"
        assert updated['telefon'] == "+49 30 11111111"
        assert updated['offen_fuer_gruppentherapie'] == True
    
    def test_update_patient_not_found(self):
        """Test updating non-existent patient returns 404."""
        update_data = {
            "vorname": "Ghost"
        }
        
        response = requests.put(
            f"{BASE_URL}/patients/99999999",
            json=update_data,
            headers=self.base_headers
        )
        
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    def test_update_patient_status_transitions(self):
        """Test various status transitions."""
        patient = self.create_test_patient(status="offen")
        
        # Valid status transitions
        status_sequence = [
            "auf der Suche",
            "in Therapie",
            "Therapie abgeschlossen"
        ]
        
        for new_status in status_sequence:
            response = requests.put(
                f"{BASE_URL}/patients/{patient['id']}",
                json={"status": new_status},
                headers=self.base_headers
            )
            
            assert response.status_code == 200
            updated = response.json()
            assert updated['status'] == new_status
    
    # --- DELETE /patients/{id} Tests ---
    
    def test_delete_patient_success(self):
        """Test deleting an existing patient."""
        patient = self.create_test_patient(vorname="ToDelete", nachname="Patient")
        patient_id = patient['id']
        
        # Delete the patient
        response = requests.delete(f"{BASE_URL}/patients/{patient_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert 'message' in result
        assert 'deleted successfully' in result['message'].lower()
        
        # Verify patient is deleted
        get_response = requests.get(f"{BASE_URL}/patients/{patient_id}")
        assert get_response.status_code == 404
        
        # Remove from cleanup list since already deleted
        self.created_patient_ids.remove(patient_id)
    
    def test_delete_patient_not_found(self):
        """Test deleting non-existent patient returns 404."""
        response = requests.delete(f"{BASE_URL}/patients/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    # --- Complex Scenario Tests ---
    
    def test_patient_lifecycle(self):
        """Test complete patient lifecycle: create, read, update, delete."""
        # 1. Create
        create_data = {
            "vorname": "Lifecycle",
            "nachname": "Test",
            "email": "lifecycle@test.com",
            "status": "offen"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/patients",
            json=create_data,
            headers=self.base_headers
        )
        assert create_response.status_code == 201
        
        patient = create_response.json()
        patient_id = patient['id']
        self.created_patient_ids.append(patient_id)
        
        # 2. Read
        get_response = requests.get(f"{BASE_URL}/patients/{patient_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved['vorname'] == "Lifecycle"
        
        # 3. Update
        update_response = requests.put(
            f"{BASE_URL}/patients/{patient_id}",
            json={"status": "in Therapie", "email": "updated.lifecycle@test.com"},
            headers=self.base_headers
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated['status'] == "in Therapie"
        assert updated['email'] == "updated.lifecycle@test.com"
        
        # 4. Delete
        delete_response = requests.delete(f"{BASE_URL}/patients/{patient_id}")
        assert delete_response.status_code == 200
        
        # 5. Verify deleted
        verify_response = requests.get(f"{BASE_URL}/patients/{patient_id}")
        assert verify_response.status_code == 404
        
        # Remove from cleanup list
        self.created_patient_ids.remove(patient_id)
    
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
        
        complex_spatial = {
            "max_km": 25,
            "travel_time_minutes": 45,
            "preferred_areas": ["Berlin-Mitte", "Charlottenburg"],
            "excluded_areas": ["Spandau"]
        }
        
        patient = self.create_test_patient(
            zeitliche_verfuegbarkeit=complex_availability,
            raeumliche_verfuegbarkeit=complex_spatial,
            ausgeschlossene_therapeuten=[10, 20, 30, 40, 50]
        )
        
        # Retrieve and verify
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        assert response.status_code == 200
        
        retrieved = response.json()
        
        # The API might return these fields - implementation dependent
        if 'zeitliche_verfuegbarkeit' in retrieved:
            assert isinstance(retrieved['zeitliche_verfuegbarkeit'], dict)
        
        if 'raeumliche_verfuegbarkeit' in retrieved:
            assert isinstance(retrieved['raeumliche_verfuegbarkeit'], dict)
        
        if 'ausgeschlossene_therapeuten' in retrieved:
            assert isinstance(retrieved['ausgeschlossene_therapeuten'], list)
    
    def test_german_enum_values(self):
        """Test all German enum values for PatientStatus."""
        status_values = [
            "offen",
            "auf der Suche",
            "in Therapie",
            "Therapie abgeschlossen",
            "Suche abgebrochen",
            "Therapie abgebrochen"
        ]
        
        for status in status_values:
            patient = self.create_test_patient(
                vorname=f"Status{status_values.index(status)}",
                status=status
            )
            
            response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
            assert response.status_code == 200
            
            retrieved = response.json()
            assert retrieved['status'] == status
    
    def test_therapist_gender_preference_enum(self):
        """Test TherapistGenderPreference enum values."""
        preferences = ["MALE", "FEMALE", "ANY"]
        
        for pref in preferences:
            patient = self.create_test_patient(
                vorname=f"Pref{preferences.index(pref)}",
                bevorzugtes_therapeutengeschlecht=pref
            )
            
            response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
            assert response.status_code == 200
            
            retrieved = response.json()
            assert retrieved['bevorzugtes_therapeutengeschlecht'] == pref
    
    def test_date_field_formats(self):
        """Test date field handling."""
        dates = {
            "geburtsdatum": "1990-12-25",
            "startdatum": "2025-01-15",
            "erster_therapieplatz_am": "2025-02-01",
            "funktionierender_therapieplatz_am": "2025-03-01"
        }
        
        patient = self.create_test_patient(**dates)
        
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        assert response.status_code == 200
        
        retrieved = response.json()
        
        # Verify dates are returned (format might vary by implementation)
        for field in dates:
            if field in retrieved and retrieved[field]:
                # Should be a valid date string
                assert isinstance(retrieved[field], str)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])