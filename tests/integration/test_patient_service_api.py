"""Integration tests for Patient Service API - Phase 2 implementation compatible.

This file has been updated to match the actual Phase 2 implementation.
Changes made:
1. Updated validation messages to match actual implementation
2. Rewritten payment tests to use PUT endpoint with zahlung_eingegangen field
3. Removed HTTP import tests (import is file-based via GCS)
4. Updated automatic startdatum test for new payment-based logic
5. Fixed case sensitivity for auf_der_Suche status (capital 'S')
6. Updated cascade integration tests for simplified deletion logic
7. Updated symptom validation to allow 1-6 symptoms instead of 1-3
"""
import pytest
import requests
import time
from datetime import date
import os

# Base URL for the Patient Service
BASE_URL = os.environ["PATIENT_API_URL"]

# Base URL for the Matching Service (for cascade tests)
MATCHING_API_URL = os.environ["MATCHING_API_URL"]

# Valid symptoms list for validation
VALID_SYMPTOMS = [
    # HÄUFIGSTE ANLIEGEN
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
        """Helper method to create a test patient with Phase 2 format."""
        default_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Patient",
            "email": "test.patient@example.com",
            "telefon": "+49 123 456789",
            "strasse": "Teststraße 123",
            "plz": "12345",
            "ort": "Berlin",
            "geburtsdatum": "1990-01-01",
            "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"],  # Array format
            "krankenkasse": "Test Krankenkasse"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{BASE_URL}/patients", json=data)
        assert response.status_code == 201
        return response.json()

    def find_patients_in_paginated_results(self, patient_ids, max_pages=50, **query_params):
        """Helper method to find specific patient IDs in paginated results."""
        found_ids = set()
        page = 1
        
        while page <= max_pages:
            params = {"page": page, "limit": 20}
            params.update(query_params)
            
            response = requests.get(f"{BASE_URL}/patients", params=params)
            assert response.status_code == 200
            
            data = response.json()
            patients = data['data']
            
            for patient in patients:
                if patient['id'] in patient_ids:
                    found_ids.add(patient['id'])
            
            if len(found_ids) == len(patient_ids) or len(patients) < 20:
                break
                
            page += 1
        
        return found_ids, page

    def verify_patients_exist(self, patient_ids, **query_params):
        """Verify that specific patient IDs exist in the system using pagination."""
        found_ids, pages_checked = self.find_patients_in_paginated_results(patient_ids, **query_params)
        
        if len(found_ids) != len(patient_ids):
            missing_ids = set(patient_ids) - found_ids
            print(f"Missing patient IDs: {missing_ids}, checked {pages_checked} pages")
            return False
        
        return True

    # ==================== BASIC CRUD TESTS ====================

    def test_create_patient(self):
        """Test creating a new patient."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Max",
            "nachname": "Mustermann",
            "email": "max.mustermann@example.com",
            "telefon": "+49 30 12345678",
            "strasse": "Musterstraße 1",
            "plz": "10115",
            "ort": "Berlin",
            "geburtsdatum": "1985-05-15",
            "symptome": ["Ängste / Panikattacken", "Stress / Überforderung"],
            "krankenkasse": "AOK Berlin",
            "status": "offen"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["vorname"] == "Max"
        assert created_patient["nachname"] == "Mustermann"
        assert created_patient["status"] == "offen"
        assert created_patient["anrede"] == "Herr"
        assert created_patient["geschlecht"] == "männlich"
        assert isinstance(created_patient["symptome"], list)
        assert len(created_patient["symptome"]) == 2
        assert "id" in created_patient
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_get_patient_by_id(self):
        """Test retrieving a patient by ID."""
        patient = self.create_test_patient(
            vorname="Anna",
            nachname="Schmidt"
        )
        
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        assert response.status_code == 200
        
        retrieved_patient = response.json()
        assert retrieved_patient["id"] == patient["id"]
        assert retrieved_patient["vorname"] == "Anna"
        assert retrieved_patient["nachname"] == "Schmidt"
        assert isinstance(retrieved_patient["symptome"], list)
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_update_patient(self):
        """Test updating a patient."""
        patient = self.create_test_patient()
        
        update_data = {
            "telefon": "+49 30 98765432",
            "status": "in_Therapie",
            "symptome": ["Burnout / Erschöpfung", "Innere Leere"]
        }
        
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json=update_data
        )
        assert response.status_code == 200
        
        updated_patient = response.json()
        assert updated_patient["telefon"] == "+49 30 98765432"
        assert updated_patient["status"] == "in_Therapie"
        assert len(updated_patient["symptome"]) == 2
        assert "Burnout / Erschöpfung" in updated_patient["symptome"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_delete_patient(self):
        """Test deleting a patient."""
        patient = self.create_test_patient()
        
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

    # ==================== SYMPTOM VALIDATION TESTS ====================

    def test_create_patient_with_single_symptom(self):
        """Test creating patient with minimum 1 symptom."""
        patient_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "Single",
            "nachname": "Symptom",
            "email": "single@example.com",
            "geburtsdatum": "1990-01-01",
            "symptome": ["Schlafstörungen"],
            "krankenkasse": "TK"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert len(created_patient["symptome"]) == 1
        assert created_patient["symptome"][0] == "Schlafstörungen"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_create_patient_with_six_symptoms(self):
        """Test creating patient with maximum 6 symptoms."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Max",
            "nachname": "Six",
            "email": "six@example.com",
            "geburtsdatum": "1985-01-01",
            "symptome": [
                "Trauer / Verlust",
                "Einsamkeit",
                "Sozialer Rückzug",
                "Depression / Niedergeschlagenheit",
                "Ängste / Panikattacken",
                "Burnout / Erschöpfung"
            ],
            "krankenkasse": "AOK"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert len(created_patient["symptome"]) == 6
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_reject_patient_with_zero_symptoms(self):
        """Test that patient creation fails with no symptoms."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "No",
            "nachname": "Symptoms",
            "email": "no.symptoms@example.com",
            "geburtsdatum": "1990-01-01",
            "symptome": [],
            "krankenkasse": "TK"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        # Updated to match actual implementation message
        assert "At least one symptom is required" in response.json()["message"]

    def test_reject_patient_with_seven_symptoms(self):
        """Test that patient creation fails with more than 6 symptoms."""
        patient_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "Too",
            "nachname": "Many",
            "email": "too.many@example.com",
            "geburtsdatum": "1990-01-01",
            "symptome": [
                "Depression / Niedergeschlagenheit",
                "Ängste / Panikattacken",
                "Burnout / Erschöpfung",
                "Schlafstörungen",
                "Stress / Überforderung",
                "Trauer / Verlust",
                "Reizbarkeit / Wutausbrüche"
            ],
            "krankenkasse": "Barmer"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        # Updated to match new implementation message
        assert "Between 1 and 6 symptoms must be selected" in response.json()["message"]

    def test_reject_patient_with_invalid_symptom(self):
        """Test that patient creation fails with invalid symptom."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Invalid",
            "nachname": "Symptom",
            "email": "invalid@example.com",
            "geburtsdatum": "1990-01-01",
            "symptome": ["Depression / Niedergeschlagenheit", "Kopfschmerzen"],  # Kopfschmerzen not valid
            "krankenkasse": "DAK"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        assert "Invalid symptom" in response.json()["message"]
        assert "Kopfschmerzen" in response.json()["message"]

    # ==================== GENDER TESTS ====================

    def test_create_patient_with_different_gender(self):
        """Test creating patients with different gender options."""
        patient_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "Anna",
            "nachname": "Schmidt",
            "email": "anna.schmidt@example.com",
            "symptome": ["Sorgen / Grübeln"]
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["anrede"] == "Frau"
        assert created_patient["geschlecht"] == "weiblich"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_create_patient_diverse_gender(self):
        """Test creating a patient with diverse gender."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "divers",
            "vorname": "Alex",
            "nachname": "Meyer",
            "symptome": ["Identitätskrise"]
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["geschlecht"] == "divers"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_create_patient_no_gender_specified(self):
        """Test creating a patient with keine_Angabe gender."""
        patient_data = {
            "anrede": "Frau",
            "geschlecht": "keine_Angabe",
            "vorname": "Chris",
            "nachname": "Weber",
            "symptome": ["Selbstzweifel"]
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["geschlecht"] == "keine_Angabe"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    # ==================== VALIDATION TESTS ====================

    def test_create_patient_invalid_anrede(self):
        """Test creating a patient with invalid anrede."""
        patient_data = {
            "anrede": "Dr.",  # Invalid
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Invalid",
            "symptome": ["Zwänge"]
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        assert "Invalid anrede 'Dr.'" in response.json()["message"]
        assert "Valid values: Herr, Frau" in response.json()["message"]

    def test_create_patient_invalid_geschlecht(self):
        """Test creating a patient with invalid geschlecht."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "other",  # Invalid
            "vorname": "Test",
            "nachname": "Invalid",
            "symptome": ["Mobbing"]
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        assert "Invalid geschlecht 'other'" in response.json()["message"]
        assert "Valid values: männlich, weiblich, divers, keine_Angabe" in response.json()["message"]

    def test_create_patient_missing_required_fields(self):
        """Test creating a patient without required fields."""
        # Missing anrede
        patient_data = {
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Patient",
            "symptome": ["Trennungsschmerz"]
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        assert "anrede" in response.json()["message"].lower()
        
        # Missing geschlecht
        patient_data = {
            "anrede": "Herr",
            "vorname": "Test",
            "nachname": "Patient",
            "symptome": ["Reizbarkeit / Wutausbrüche"]
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        assert "geschlecht" in response.json()["message"].lower()

    # ==================== PAYMENT WORKFLOW TESTS (UPDATED) ====================

    def test_patient_has_zahlungsreferenz_field(self):
        """Test that patients have zahlungsreferenz field."""
        patient = self.create_test_patient()
        
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        assert response.status_code == 200
        
        patient_data = response.json()
        assert "zahlungsreferenz" in patient_data
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_payment_confirmation_workflow(self):
        """Test payment confirmation workflow using PUT endpoint."""
        patient = self.create_test_patient(
            vertraege_unterschrieben=True,
            status="offen",
            zahlung_eingegangen=False
        )
        
        # Confirm payment by updating zahlung_eingegangen field
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json={"zahlung_eingegangen": True}
        )
        assert response.status_code == 200
        
        # Get updated patient
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        updated_patient = response.json()
        
        # Verify automatic changes triggered by payment confirmation
        assert updated_patient["zahlung_eingegangen"] is True
        assert updated_patient["status"] == "auf_der_Suche"  # Fixed: capital 'S'
        assert updated_patient["startdatum"] == date.today().isoformat()  # Automatically set
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_payment_without_contracts_no_status_change(self):
        """Test payment confirmation without signed contracts using PUT endpoint."""
        patient = self.create_test_patient(
            vertraege_unterschrieben=False,
            status="offen",
            zahlung_eingegangen=False
        )
        
        # Confirm payment by updating zahlung_eingegangen field
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json={"zahlung_eingegangen": True}
        )
        assert response.status_code == 200
        
        # Get updated patient
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        updated_patient = response.json()
        
        # Verify payment confirmed but no automatic status change
        assert updated_patient["zahlung_eingegangen"] is True
        assert updated_patient["status"] == "offen"  # No change
        assert updated_patient.get("startdatum") is None  # Not set
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_payment_idempotent_workflow(self):
        """Test that payment confirmation is idempotent using PUT endpoint."""
        patient = self.create_test_patient(
            vertraege_unterschrieben=True,
            status="offen",
            zahlung_eingegangen=False
        )
        
        # First payment confirmation
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json={"zahlung_eingegangen": True}
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        first_update = response.json()
        first_startdatum = first_update["startdatum"]
        
        # Wait a moment
        time.sleep(0.1)
        
        # Second payment confirmation (should be idempotent)
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json={"zahlung_eingegangen": True}
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/patients/{patient['id']}")
        second_update = response.json()
        
        # Startdatum should not change
        assert second_update["startdatum"] == first_startdatum
        assert second_update["status"] == "auf_der_Suche"  # Fixed: capital 'S'
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    # ==================== PAGINATION TESTS ====================

    def test_get_patients_list_empty(self):
        """Test getting patient list pagination structure."""
        response = requests.get(f"{BASE_URL}/patients")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 0

    def test_get_patients_with_pagination(self):
        """Test pagination parameters."""
        created_patients = []
        for i in range(5):
            patient = self.create_test_patient(
                vorname=f"PagTest{i}",
                nachname=f"Patient{i}",
                email=f"pagtest{i}@example.com"
            )
            created_patients.append(patient)
        
        patient_ids = [p['id'] for p in created_patients]
        
        # Test page 1 with limit 2
        response = requests.get(f"{BASE_URL}/patients?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        assert data['total'] >= 5
        
        # Verify all patients exist
        assert self.verify_patients_exist(patient_ids)
        
        # Cleanup
        for patient in created_patients:
            requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_get_patients_list_filtered_by_status(self):
        """Test filtering patients by status."""
        patient1 = self.create_test_patient(
            vorname="StatusActive",
            email="active@example.com",
            status="auf_der_Suche"
        )
        patient2 = self.create_test_patient(
            vorname="StatusOpen",
            email="open@example.com",
            status="offen"
        )
        
        # Filter by status
        found_ids, _ = self.find_patients_in_paginated_results(
            [patient1['id']], 
            status="auf_der_Suche"
        )
        
        assert patient1['id'] in found_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient1['id']}")
        requests.delete(f"{BASE_URL}/patients/{patient2['id']}")

    def test_pagination_limits(self):
        """Test pagination limit constraints."""
        # Test max limit
        response = requests.get(f"{BASE_URL}/patients?limit=2000")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1000  # Should be capped
        
        # Test zero limit
        response = requests.get(f"{BASE_URL}/patients?limit=0")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1  # Should be minimum
        
        # Test negative page
        response = requests.get(f"{BASE_URL}/patients?page=-1")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1  # Should be minimum

    # ==================== PREFERENCES TESTS ====================

    def test_create_patient_with_preferences(self):
        """Test creating a patient with therapy preferences."""
        patient_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "Maria",
            "nachname": "Weber",
            "symptome": ["Beziehungsprobleme", "Familienkonflikte"],
            "bevorzugtes_therapeutengeschlecht": "Weiblich",
            "bevorzugtes_therapieverfahren": "Verhaltenstherapie",
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
        assert created_patient["bevorzugtes_therapieverfahren"] == "Verhaltenstherapie"
        assert created_patient["offen_fuer_gruppentherapie"] is True
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_validate_therapieverfahren(self):
        """Test validation of bevorzugtes_therapieverfahren field."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Valid",
            "symptome": ["Chronische Schmerzen"],
            "bevorzugtes_therapieverfahren": "Verhaltenstherapie"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        patient = response.json()
        assert patient['bevorzugtes_therapieverfahren'] == "Verhaltenstherapie"
        patient_id = patient['id']
        
        # Test other valid values
        valid_values = ["egal", "tiefenpsychologisch_fundierte_Psychotherapie"]
        for value in valid_values:
            update_response = requests.put(
                f"{BASE_URL}/patients/{patient_id}",
                json={"bevorzugtes_therapieverfahren": value}
            )
            assert update_response.status_code == 200
            updated = update_response.json()
            assert updated['bevorzugtes_therapieverfahren'] == value
        
        # Invalid value
        patient_data['bevorzugtes_therapieverfahren'] = "Psychoanalyse"  # Invalid
        patient_data['nachname'] = "Invalid"
        patient_data['email'] = "invalid@example.com"
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400
        assert "Invalid therapy method 'Psychoanalyse'" in response.json()["message"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient_id}")

    # ==================== OTHER FEATURES ====================

    def test_patient_communication_history(self):
        """Test getting patient communication history."""
        patient = self.create_test_patient()
        
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

    def test_automatic_startdatum_with_payment(self):
        """Test automatic setting of startdatum when payment is confirmed with signed contracts."""
        # Create patient with signed contracts but no payment
        patient = self.create_test_patient(
            vertraege_unterschrieben=True,
            zahlung_eingegangen=False,
            status="offen"
        )
        
        # Verify startdatum is not set initially
        assert patient.get('startdatum') is None
        
        # Confirm payment
        response = requests.put(
            f"{BASE_URL}/patients/{patient['id']}",
            json={"zahlung_eingegangen": True}
        )
        assert response.status_code == 200
        
        updated_patient = response.json()
        # startdatum should now be set to today
        assert updated_patient['startdatum'] == date.today().isoformat()
        # Status should also change
        assert updated_patient['status'] == "auf_der_Suche"  # Fixed: capital 'S'
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{patient['id']}")

    def test_create_patient_with_new_fields(self):
        """Test creating patient with experience fields."""
        patient_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "Test",
            "nachname": "Experience",
            "symptome": ["Psychosomatische Beschwerden", "Sexuelle Probleme"],
            "erfahrung_mit_psychotherapie": True,
            "letzte_sitzung_vorherige_psychotherapie": "2023-06-15",
            "krankenkasse": "TK"
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["erfahrung_mit_psychotherapie"] is True
        assert created_patient["letzte_sitzung_vorherige_psychotherapie"] == "2023-06-15"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    def test_import_status_endpoint(self):
        """Test import status monitoring endpoint."""
        response = requests.get(f"{BASE_URL}/patients/import-status")
        assert response.status_code == 200
        
        status = response.json()
        assert 'running' in status
        assert 'files_processed_today' in status
        assert 'files_failed_today' in status

    def test_create_patient_with_zahlungsreferenz(self):
        """Test creating patient with zahlungsreferenz field."""
        patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Payment",
            "nachname": "Reference",
            "symptome": ["Stress / Überforderung"],
            "zahlungsreferenz": "ABC12345",
            "zahlung_eingegangen": False
        }
        
        response = requests.post(f"{BASE_URL}/patients", json=patient_data)
        assert response.status_code == 201
        
        created_patient = response.json()
        assert created_patient["zahlungsreferenz"] == "ABC12345"
        assert created_patient["zahlung_eingegangen"] is False
        
        # Cleanup
        requests.delete(f"{BASE_URL}/patients/{created_patient['id']}")

    # ==================== SIMPLIFIED DELETION TEST ====================

    def test_patient_deletion_blocked_with_platzsuche(self):
        """Test that patient deletion is blocked when Platzsuche exists.
        
        This test verifies the simplified deletion logic where:
        1. Patient deletion is blocked if a Platzsuche exists
        2. User must manually delete Platzsuche first
        3. Then patient can be deleted
        """
        # Step 1: Create a test patient
        patient = self.create_test_patient(
            vorname="BlockedDeletion",
            nachname="TestPatient",
            email="blocked.deletion@example.com",
            status="auf_der_Suche",
            erfahrung_mit_psychotherapie=False,
            offen_fuer_gruppentherapie=False,
            zeitliche_verfuegbarkeit={"montag": ["09:00-17:00"]}
        )
        patient_id = patient['id']
        
        # Step 2: Create an active platzsuche for this patient
        platzsuche_data = {
            "patient_id": patient_id
        }
        
        try:
            response = requests.post(f"{MATCHING_API_URL}/platzsuchen", json=platzsuche_data)
            if response.status_code != 201:
                pytest.skip(f"Could not create Platzsuche: {response.status_code} - {response.text}")
            
            platzsuche = response.json()
            platzsuche_id = platzsuche['id']
            
            # Step 3: Attempt to delete the patient - should be BLOCKED
            response = requests.delete(f"{BASE_URL}/patients/{patient_id}")
            
            # Verify deletion is blocked with error 400
            assert response.status_code == 400
            error_message = response.json()["message"]
            assert "Cannot delete patient" in error_message
            assert "Active search exists" in error_message
            assert "Please delete the search first" in error_message
            
            # Also check if the response includes the count of existing searches
            if "existing_searches" in response.json():
                assert response.json()["existing_searches"] == 1
            
            # Step 4: Verify the patient still exists
            response = requests.get(f"{BASE_URL}/patients/{patient_id}")
            assert response.status_code == 200
            still_exists = response.json()
            assert still_exists['id'] == patient_id
            
            # Step 5: Delete the Platzsuche first
            response = requests.delete(f"{MATCHING_API_URL}/platzsuchen/{platzsuche_id}")
            if response.status_code != 200:
                print(f"Warning: Could not delete Platzsuche: {response.status_code}")
            
            # Step 6: Now try to delete the patient again - should succeed
            response = requests.delete(f"{BASE_URL}/patients/{patient_id}")
            assert response.status_code == 200
            
            # Step 7: Verify patient is now deleted
            response = requests.get(f"{BASE_URL}/patients/{patient_id}")
            assert response.status_code == 404
            
        except requests.ConnectionError:
            pytest.skip("Matching service not available for deletion blocking test")
        except AssertionError:
            # If test fails, try cleanup
            try:
                # Try to delete Platzsuche if it exists
                if 'platzsuche_id' in locals():
                    requests.delete(f"{MATCHING_API_URL}/platzsuchen/{platzsuche_id}")
                # Try to delete patient if it still exists
                requests.delete(f"{BASE_URL}/patients/{patient_id}")
            except:
                pass
            raise
        finally:
            # Final cleanup attempt
            try:
                requests.delete(f"{BASE_URL}/patients/{patient_id}")
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
