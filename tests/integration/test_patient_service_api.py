"""Integration tests for Patient Service API with pagination support."""
import pytest
import requests
import time
from datetime import date

# Base URL for the Patient Service
BASE_URL = "http://localhost:8001/api"


class TestPatientServiceAPI:
    """Test class for Patient Service API endpoints."""

    @classmethod
    def setup_class(cls):
        """Setup test class - wait for service to be ready."""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/patients")
                if response.status_code == 200:
                    print("Patient service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Patient service did not start in time")

    def create_test_patient(self, **kwargs):
        """Helper method to create a test patient."""
        default_data = {
            "vorname": "Test",
            "nachname": "Patient",
            "email": "test.patient@example.com",
            "telefon": "+49 123 456789",
            "strasse": "Teststraße 123",
            "plz": "12345",
            "ort": "Berlin",
            "geburtsdatum": "1990-01-01",
            "diagnose": "F32.1",
            "krankenkasse": "Test Krankenkasse"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{BASE_URL}/patients", json=data)
        assert response.status_code == 201
        return response.json()

    def test_create_patient(self):
        """Test creating a new patient."""
        patient_data = {
            "vorname": "Max",
            "nachname": "Mustermann",
            "email": "max.mustermann@example.com",
            "telefon": "+49 30 12345678",
            "strasse": "Musterstraße 1",
            "plz": "10115",
            "ort": "Berlin",
            "geburtsdatum": "1985-05-15",
            "diagnose": "F32.1",
            "krankenkasse": "AOK Berlin",
            "status": "offen"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["vorname"] == "Max"
        assert created_patient["nachname"] == "Mustermann"
        assert created_patient["status"] == "offen"
        assert "id" in created_patient
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_get_patient_by_id(self):
        """Test retrieving a patient by ID."""
        # Create a patient first
        patient = self.create_test_patient(
            vorname="Anna",
            nachname="Schmidt"
        )
        
        # Get the patient
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        assert response.status_code == 200
        
        retrieved_patient = response.json()
        assert retrieved_patient["id"] == patient["id"]
        assert retrieved_patient["vorname"] == "Anna"
        assert retrieved_patient["nachname"] == "Schmidt"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_get_patients_list_empty(self):
        """Test getting empty patient list with pagination."""
        # Note: This assumes no patients exist. In a real test environment,
        # you might want to clean up all patients first.
        response = requests.get(f"{BASE_URL}/patients")
        assert response.status_code == 200
        
        # Now expecting paginated structure
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20  # Default limit
        assert data['total'] >= 0  # Could be 0 or more

    def test_get_patients_list_with_data(self):
        """Test getting patient list with data and pagination."""
        # Create test patients
        patient1 = self.create_test_patient(vorname="Anna", nachname="Müller")
        patient2 = self.create_test_patient(vorname="Max", nachname="Schmidt")
        
        response = requests.get(f"{BASE_URL}/patients")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        patients = data['data']
        assert len(patients) >= 2
        
        # Verify our patients are in the list
        patient_ids = [p['id'] for p in patients]
        assert patient1['id'] in patient_ids
        assert patient2['id'] in patient_ids
        
        # Verify pagination metadata
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 2
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient1['id']}")
        requests.delete(f"{BASE_URL}/patients/{patient2['id']}")

    def test_get_patients_with_pagination(self):
        """Test pagination parameters."""
        # Create multiple patients
        created_patients = []
        for i in range(5):
            patient = self.create_test_patient(
                vorname=f"Test{i}",
                nachname=f"Patient{i}",
                email=f"test{i}@example.com"
            )
            created_patients.append(patient)
        
        # Test page 1 with limit 2
        response = requests.get(f"{BASE_URL}/patients?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        assert data['total'] >= 5
        
        # Test page 2 with limit 2
        response = requests.get(f"{BASE_URL}/patients?page=2&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 2
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        
        # Cleanup
        for patient in created_patients:
            requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_get_patients_list_filtered_by_status(self):
        """Test filtering patients by status with pagination."""
        # Create patients with different statuses
        patient1 = self.create_test_patient(
            vorname="Active",
            nachname="Patient",
            status="auf_der_Suche"
        )
        patient2 = self.create_test_patient(
            vorname="Open",
            nachname="Patient",
            status="offen"
        )
        
        # Filter by status
        response = requests.get(f"{BASE_URL}/patients?status=auf_der_Suche")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        patients = data['data']
        
        # Check that all returned patients have the correct status
        for patient in patients:
            assert patient['status'] == "auf_der_Suche"
        
        # Verify patient1 is in results
        patient_ids = [p['id'] for p in patients]
        assert patient1['id'] in patient_ids
        assert patient2['id'] not in patient_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient1['id']}")
        requests.delete(f"{BASE_URL}/patients/{patient2['id']}")

    def test_update_patient(self):
        """Test updating a patient."""
        # Create a patient
        patient = self.create_test_patient()
        
        # Update the patient
        update_data = {
            "telefon": "+49 30 98765432",
            "status": "in_Therapie",
            "letzter_kontakt": date.today().isoformat()
        }
        
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json=update_data
        )
        assert response.status_code == 200
        
        updated_patient = response.json()
        assert updated_patient["telefon"] == "+49 30 98765432"
        assert updated_patient["status"] == "in_Therapie"
        assert updated_patient["letzter_kontakt"] == date.today().isoformat()
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_delete_patient(self):
        """Test deleting a patient."""
        # Create a patient
        patient = self.create_test_patient()
        
        # Delete the patient
        response = requests.delete(f"{BASE_URL}/patients/{patient['id']}")
        assert response.status_code == 200
        
        # Verify patient is deleted
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        assert response.status_code == 404

    def test_patient_not_found(self):
        """Test getting a non-existent patient."""
        response = requests.get(f"{BASE_URL}/patients/99999")
        assert response.status_code == 404
        assert response.json()["message"] == "Patient not found"

    def test_invalid_status_filter(self):
        """Test filtering with invalid status returns empty result."""
        response = requests.get(f"{BASE_URL}/patients?status=invalid_status")
        assert response.status_code == 200
        
        # Should return empty paginated result
        data = response.json()
        assert data['data'] == []
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] == 0

    def test_create_patient_with_preferences(self):
        """Test creating a patient with therapy preferences."""
        patient_data = {
            "vorname": "Maria",
            "nachname": "Weber",
            "bevorzugtes_therapeutengeschlecht": "Weiblich",
            "bevorzugtes_therapieverfahren": ["Verhaltenstherapie"],
            "offen_fuer_gruppentherapie": True,
            "raeumliche_verfuegbarkeit": {"max_km": 15},
            "zeitliche_verfuegbarkeit": {
                "montag": ["09:00-12:00", "14:00-18:00"],
                "dienstag": ["10:00-16:00"]
            }
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["bevorzugtes_therapeutengeschlecht"] == "Weiblich"
        assert created_patient["bevorzugtes_therapieverfahren"] == ["Verhaltenstherapie"]
        assert created_patient["offen_fuer_gruppentherapie"] is True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_patient_communication_history(self):
        """Test getting patient communication history."""
        # Create a patient
        patient = self.create_test_patient()
        
        # Get communication history (should be empty initially)
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}/communication")
        assert response.status_code == 200
        
        comm_data = response.json()
        assert comm_data['patient_id'] == patient['id']
        assert comm_data['patient_name'] == f"{patient['vorname']} {patient['nachname']}"
        assert comm_data['total_emails'] >= 0
        assert comm_data['total_calls'] >= 0
        assert isinstance(comm_data['communications'], list)
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_pagination_limits(self):
        """Test pagination limit constraints."""
        # Test max limit (should be capped at 100)
        response = requests.get(f"{BASE_URL}/patients?limit=200")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 100  # Should be capped at max limit
        
        # Test zero limit (should be set to 1)
        response = requests.get(f"{BASE_URL}/patients?limit=0")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1  # Should be set to minimum
        
        # Test negative page (should be set to 1)
        response = requests.get(f"{BASE_URL}/patients?page=-1")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1  # Should be set to minimum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
