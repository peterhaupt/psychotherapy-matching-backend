"""Integration tests for Matching Service API - Phase 2 target state.

This file represents the complete test suite after Phase 2 implementation.
All tests here should pass once Phase 2 is complete.
"""
import pytest
import requests
import time
from datetime import date, datetime
import os

# Base URLs for services
BASE_URL = os.environ["MATCHING_API_URL"]
PATIENT_BASE_URL = os.environ["PATIENT_API_URL"]
THERAPIST_BASE_URL = os.environ["THERAPIST_API_URL"]
COMMUNICATION_BASE_URL = os.environ["COMMUNICATION_API_URL"]


class TestMatchingServiceAPI:
    """Test class for Matching Service API endpoints."""

    @classmethod
    def setup_class(cls):
        """Setup test class - wait for service to be ready."""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/platzsuchen")
                if response.status_code == 200:
                    print("Matching service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Matching service did not start in time")

    def create_test_patient(self, **kwargs):
        """Helper to create a test patient with Phase 2 format."""
        default_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Patient",
            "plz": "52064",
            "ort": "Aachen",
            "email": "test.patient@example.com",
            "telefon": "+49 123 456789",
            "strasse": "Teststraße 123",
            "geburtsdatum": "1990-01-01",
            "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"],  # Array format, no diagnosis
            "krankenkasse": "Test Krankenkasse",
            "erfahrung_mit_psychotherapie": False,
            "offen_fuer_gruppentherapie": False,
            "zeitliche_verfuegbarkeit": {
                "montag": ["09:00-17:00"],
                "mittwoch": ["14:00-18:00"]
            },
            "raeumliche_verfuegbarkeit": {"max_km": 25},
            "bevorzugtes_therapeutengeschlecht": "Egal",
            "bevorzugtes_therapieverfahren": "egal"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{PATIENT_BASE_URL}/patients", json=data)
        assert response.status_code == 201, f"Failed to create patient: {response.status_code} - {response.text}"
        return response.json()

    def create_test_therapist(self, **kwargs):
        """Helper to create a test therapist."""
        default_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Therapeut",
            "plz": "52062",
            "ort": "Aachen",
            "email": "test.therapeut@example.com",
            "telefon": "+49 241 123456",
            "status": "aktiv",
            "potenziell_verfuegbar": True,
            "ueber_curavani_informiert": True
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{THERAPIST_BASE_URL}/therapists", json=data)
        assert response.status_code == 201, f"Failed to create therapist: {response.status_code} - {response.text}"
        return response.json()

    def safe_delete_platzsuche(self, search_id):
        """Safely delete a platzsuche."""
        try:
            response = requests.delete(f"{BASE_URL}/platzsuchen/{search_id}")
            if response.status_code not in [200, 404]:
                print(f"Warning: Failed to delete platzsuche {search_id}: {response.status_code}")
        except Exception as e:
            print(f"Warning: Exception deleting platzsuche {search_id}: {e}")

    def safe_delete_patient(self, patient_id):
        """Safely delete a patient."""
        try:
            response = requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_id}")
            if response.status_code not in [200, 404]:
                print(f"Warning: Failed to delete patient {patient_id}: {response.status_code}")
        except Exception as e:
            print(f"Warning: Exception deleting patient {patient_id}: {e}")

    def safe_delete_therapist(self, therapist_id):
        """Safely delete a therapist."""
        try:
            response = requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_id}")
            if response.status_code not in [200, 404]:
                print(f"Warning: Failed to delete therapist {therapist_id}: {response.status_code}")
        except Exception as e:
            print(f"Warning: Exception deleting therapist {therapist_id}: {e}")

    # ==================== PLATZSUCHE TESTS ====================

    def test_create_platzsuche(self):
        """Test creating a new patient search."""
        patient = self.create_test_patient()
        
        search_data = {
            "patient_id": patient['id'],
            "notizen": "Test patient search"
        }
        
        response = requests.post(f"{BASE_URL}/platzsuchen", json=search_data)
        assert response.status_code == 201, f"Failed to create platzsuche: {response.status_code} - {response.text}"
        
        created_search = response.json()
        assert created_search["patient_id"] == patient['id']
        assert created_search["status"] == "aktiv"
        assert "id" in created_search
        
        # Cleanup
        self.safe_delete_platzsuche(created_search['id'])
        self.safe_delete_patient(patient['id'])

    def test_create_platzsuche_without_diagnosis(self):
        """Test creating platzsuche without diagnosis field."""
        patient = self.create_test_patient(
            symptome=["Burnout / Erschöpfung", "Stress / Überforderung"]
        )
        
        search_data = {
            "patient_id": patient['id'],
            "notizen": "Patient without diagnosis"
        }
        
        response = requests.post(f"{BASE_URL}/platzsuchen", json=search_data)
        assert response.status_code == 201
        
        created_search = response.json()
        assert created_search["patient_id"] == patient['id']
        
        # Cleanup
        self.safe_delete_platzsuche(created_search['id'])
        self.safe_delete_patient(patient['id'])

    def test_get_platzsuche_by_id(self):
        """Test retrieving a specific platzsuche."""
        patient = self.create_test_patient()
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        search = search_response.json()
        
        # Get the platzsuche
        response = requests.get(f"{BASE_URL}/platzsuchen/{search['id']}")
        assert response.status_code == 200
        
        retrieved_search = response.json()
        assert retrieved_search["id"] == search["id"]
        assert retrieved_search["patient_id"] == patient['id']
        assert retrieved_search["status"] == "aktiv"
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_patient(patient['id'])

    def test_update_platzsuche(self):
        """Test updating a platzsuche."""
        patient = self.create_test_patient()
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        search = search_response.json()
        
        # Update the search
        update_data = {
            "status": "pausiert",
            "notizen": "Updated note",
            "ausgeschlossene_therapeuten": [101, 102]
        }
        
        response = requests.put(
            f"{BASE_URL}/platzsuchen/{search['id']}",
            json=update_data
        )
        assert response.status_code == 200
        
        # Verify updates
        response = requests.get(f"{BASE_URL}/platzsuchen/{search['id']}")
        updated_search = response.json()
        assert updated_search["status"] == "pausiert"
        assert updated_search["ausgeschlossene_therapeuten"] == [101, 102]
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_patient(patient['id'])

    def test_delete_platzsuche(self):
        """Test deleting a platzsuche."""
        patient = self.create_test_patient()
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        search = search_response.json()
        
        # Delete the search
        response = requests.delete(f"{BASE_URL}/platzsuchen/{search['id']}")
        assert response.status_code == 200
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/platzsuchen/{search['id']}")
        assert response.status_code == 404
        
        # Cleanup
        self.safe_delete_patient(patient['id'])

    def test_duplicate_platzsuche_error(self):
        """Test that creating duplicate active search fails."""
        patient = self.create_test_patient()
        search1_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert search1_response.status_code == 201
        search1 = search1_response.json()
        
        # Try to create another active search for same patient
        response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert response.status_code == 400
        assert "already has an active search" in response.json()['message']
        
        # Cleanup
        self.safe_delete_platzsuche(search1['id'])
        self.safe_delete_patient(patient['id'])

    # ==================== SYMPTOM VALIDATION TESTS ====================

    def test_platzsuche_with_valid_symptom_array(self):
        """Test creating platzsuche with valid symptom array."""
        patient = self.create_test_patient(
            symptome=["Depression / Niedergeschlagenheit", "Schlafstörungen", "Einsamkeit"]
        )
        
        search_data = {"patient_id": patient['id']}
        
        response = requests.post(f"{BASE_URL}/platzsuchen", json=search_data)
        assert response.status_code == 201
        
        # Cleanup
        search = response.json()
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_patient(patient['id'])

    def test_platzsuche_fails_with_empty_symptoms(self):
        """Test platzsuche creation fails with empty symptom array."""
        patient_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "No",
            "nachname": "Symptoms",
            "email": "no.symptoms@example.com",
            "geburtsdatum": "1990-01-01",
            "symptome": [],  # Empty array
            "krankenkasse": "TK",
            "erfahrung_mit_psychotherapie": False,
            "offen_fuer_gruppentherapie": False,
            "zeitliche_verfuegbarkeit": {"montag": ["09:00-17:00"]}
        }
        
        # Patient creation should fail
        response = requests.post(f"{PATIENT_BASE_URL}/patients", json=patient_data)
        assert response.status_code == 400

    def test_platzsuche_validation_requirements(self):
        """Test platzsuche validation doesn't require diagnosis."""
        # Create patient with minimum required fields
        patient = self.create_test_patient(
            symptome=["Ängste / Panikattacken"],
            krankenkasse="Test KK",
            geburtsdatum="1990-01-01",
            erfahrung_mit_psychotherapie=False,
            offen_fuer_gruppentherapie=False,
            zeitliche_verfuegbarkeit={"montag": ["09:00-17:00"]}
        )
        
        search_data = {"patient_id": patient['id']}
        
        response = requests.post(f"{BASE_URL}/platzsuchen", json=search_data)
        assert response.status_code == 201
        
        search = response.json()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_patient(patient['id'])

    # ==================== KONTAKTANFRAGE TESTS ====================

    def test_kontaktanfrage(self):
        """Test requesting additional contacts for a search."""
        patient = self.create_test_patient()
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert search_response.status_code == 201
        search = search_response.json()
        
        # Request additional contacts
        response = requests.post(
            f"{BASE_URL}/platzsuchen/{search['id']}/kontaktanfrage",
            json={
                "requested_count": 10,
                "notizen": "Patient sehr dringend"
            }
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result['new_total'] == 10
        assert result['search_id'] == search['id']
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_patient(patient['id'])

    # ==================== THERAPEUTEN SELECTION TESTS ====================

    def test_get_therapeuten_zur_auswahl(self):
        """Test getting therapists for selection with PLZ filter."""
        therapist1 = self.create_test_therapist(
            plz="52064",
            potenziell_verfuegbar=True,
            ueber_curavani_informiert=True,
            email="therapist1@example.com"
        )
        therapist2 = self.create_test_therapist(
            plz="52062",
            potenziell_verfuegbar=True,
            ueber_curavani_informiert=False,
            email="therapist2@example.com"
        )
        therapist3 = self.create_test_therapist(
            plz="10115",  # Different PLZ prefix
            email="therapist3@example.com"
        )
        
        # Get therapists with PLZ prefix 52
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52")
        assert response.status_code == 200
        
        data = response.json()
        assert data['plz_prefix'] == "52"
        therapists = data['data']
        
        # Verify only therapists with PLZ 52xxx are returned
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids
        assert therapist2['id'] in therapist_ids
        assert therapist3['id'] not in therapist_ids
        
        # Cleanup
        self.safe_delete_therapist(therapist1['id'])
        self.safe_delete_therapist(therapist2['id'])
        self.safe_delete_therapist(therapist3['id'])

    def test_therapeuten_zur_auswahl_email_priority(self):
        """Test that therapists with email are prioritized."""
        therapist_with_email = self.create_test_therapist(
            plz="52064",
            potenziell_verfuegbar=True,
            ueber_curavani_informiert=True,
            email="with.email@example.com",
            nachname="WithEmail"
        )
        
        therapist_without_email = self.create_test_therapist(
            plz="52065",
            potenziell_verfuegbar=True,
            ueber_curavani_informiert=True,
            email=None,
            nachname="WithoutEmail"
        )
        
        # Get therapists for selection
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52")
        assert response.status_code == 200
        
        data = response.json()
        therapists = data['data']
        
        # Find positions of our therapists
        with_email_index = None
        without_email_index = None
        
        for i, t in enumerate(therapists):
            if t['id'] == therapist_with_email['id']:
                with_email_index = i
            elif t['id'] == therapist_without_email['id']:
                without_email_index = i
        
        # Therapist with email should come before therapist without email
        assert with_email_index is not None
        assert without_email_index is not None
        assert with_email_index < without_email_index
        
        # Cleanup
        self.safe_delete_therapist(therapist_with_email['id'])
        self.safe_delete_therapist(therapist_without_email['id'])

    def test_invalid_plz_prefix(self):
        """Test invalid PLZ prefix returns error."""
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=ABC")
        assert response.status_code == 400
        assert "Invalid PLZ prefix" in response.json()['message']
        
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=5")
        assert response.status_code == 400
        assert "Must be exactly 2 digits" in response.json()['message']

    # ==================== THERAPEUTENANFRAGE TESTS ====================

    def test_create_therapeutenanfrage(self):
        """Test creating an anfrage for a manually selected therapist."""
        therapist = self.create_test_therapist(plz="52064", email="test@example.com")
        patient1 = self.create_test_patient(plz="52062")
        patient2 = self.create_test_patient(plz="52068", email="patient2@example.com")
        
        # Create searches
        search1_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient1['id']}
        )
        assert search1_response.status_code == 201
        search1 = search1_response.json()
        
        search2_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient2['id']}
        )
        assert search2_response.status_code == 201
        search2 = search2_response.json()
        
        # Create anfrage
        response = requests.post(
            f"{BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": False
            }
        )
        
        # Could be 201 (created) or 200 (no patients found)
        assert response.status_code in [200, 201]
        
        if response.status_code == 201:
            anfrage = response.json()
            assert anfrage['therapist_id'] == therapist['id']
            assert anfrage['anfragegroesse'] >= 1
            assert 'anfrage_id' in anfrage
            
            # Cleanup anfrage
            try:
                requests.delete(f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}")
            except:
                pass
        
        # Cleanup
        self.safe_delete_platzsuche(search1['id'])
        self.safe_delete_platzsuche(search2['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient1['id'])
        self.safe_delete_patient(patient2['id'])

    def test_therapeutenanfrage_email_without_diagnosis(self):
        """Test that therapeutenanfrage emails don't contain diagnosis."""
        therapist = self.create_test_therapist(plz="52064", email="therapist@example.com")
        patient = self.create_test_patient(
            plz="52062",
            symptome=["Trauer / Verlust", "Sozialer Rückzug"]
        )
        
        # Create search
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert search_response.status_code == 201
        search = search_response.json()
        
        # Create anfrage
        response = requests.post(
            f"{BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": False
            }
        )
        
        if response.status_code == 201:
            anfrage = response.json()
            anfrage_id = anfrage['anfrage_id']
            
            # Get anfrage details
            detail_response = requests.get(f"{BASE_URL}/therapeutenanfragen/{anfrage_id}")
            assert detail_response.status_code == 200
            
            anfrage_details = detail_response.json()
            
            # Verify no diagnosis field in response
            for patient_info in anfrage_details.get('patients', []):
                patient_data = patient_info.get('patient', {})
                assert 'diagnose' not in patient_data
                
                # Verify symptoms are present as array
                assert 'symptome' in patient_data
                assert isinstance(patient_data['symptome'], list)
            
            # Cleanup
            try:
                requests.delete(f"{BASE_URL}/therapeutenanfragen/{anfrage_id}")
            except:
                pass
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_send_anfrage_to_therapist_without_email(self):
        """Test that sending anfrage to therapist without email creates phone call."""
        therapist = self.create_test_therapist(
            plz="52064",
            email=None,
            telefon="+49 241 123456",
            telefonische_erreichbarkeit={
                "montag": ["10:00-12:00"],
                "mittwoch": ["14:00-16:00"]
            }
        )
        
        patient = self.create_test_patient(plz="52062")
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert search_response.status_code == 201
        search = search_response.json()
        
        # Create anfrage
        anfrage_response = requests.post(
            f"{BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": False
            }
        )
        
        if anfrage_response.status_code == 201:
            anfrage = anfrage_response.json()
            
            # Send the anfrage
            send_response = requests.post(
                f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}/senden"
            )
            assert send_response.status_code == 200
            
            send_data = send_response.json()
            
            # Verify response structure for phone call
            assert send_data['communication_type'] == 'phone_call'
            assert send_data['email_id'] is None
            assert send_data['phone_call_id'] is not None
            assert 'sent_date' in send_data
            
            # Cleanup
            try:
                requests.delete(f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}")
            except:
                pass
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_send_anfrage_to_therapist_with_email(self):
        """Test that sending anfrage to therapist with email works normally."""
        therapist = self.create_test_therapist(
            plz="52064",
            email="therapist@example.com"
        )
        
        patient = self.create_test_patient(plz="52062")
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert search_response.status_code == 201
        search = search_response.json()
        
        # Create anfrage
        anfrage_response = requests.post(
            f"{BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": False
            }
        )
        
        if anfrage_response.status_code == 201:
            anfrage = anfrage_response.json()
            
            # Send the anfrage
            send_response = requests.post(
                f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}/senden"
            )
            assert send_response.status_code == 200
            
            send_data = send_response.json()
            
            # Verify response structure for email
            assert send_data['communication_type'] == 'email'
            assert send_data['email_id'] is not None
            assert send_data['phone_call_id'] is None
            assert 'sent_date' in send_data
            
            # Cleanup
            try:
                requests.delete(f"{BASE_URL}/therapeutenanfragen/{anfrage['anfrage_id']}")
            except:
                pass
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_therapist(therapist['id'])
        self.safe_delete_patient(patient['id'])

    def test_anfrage_response(self):
        """Test recording a therapist response to an anfrage."""
        # This would need a real anfrage to test properly
        # For now, test the error case
        response = requests.put(
            f"{BASE_URL}/therapeutenanfragen/99999/antwort",
            json={
                "patient_responses": {
                    "1": "angenommen",
                    "2": "abgelehnt_Kapazitaet"
                },
                "notizen": "Test response"
            }
        )
        assert response.status_code == 404

    # ==================== PAGINATION TESTS ====================

    def test_get_platzsuchen_list_empty(self):
        """Test getting empty platzsuche list with pagination."""
        response = requests.get(f"{BASE_URL}/platzsuchen")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 0

    def test_get_platzsuchen_with_pagination(self):
        """Test platzsuche pagination parameters."""
        created_patients = []
        created_searches = []
        
        for i in range(5):
            patient = self.create_test_patient(
                vorname=f"Patient{i}",
                email=f"patient{i}@example.com"
            )
            created_patients.append(patient)
            
            search_response = requests.post(
                f"{BASE_URL}/platzsuchen",
                json={"patient_id": patient['id']}
            )
            assert search_response.status_code == 201
            created_searches.append(search_response.json())
        
        # Test page 1 with limit 2
        response = requests.get(f"{BASE_URL}/platzsuchen?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        assert data['total'] >= 5
        
        # Cleanup
        for search in created_searches:
            self.safe_delete_platzsuche(search['id'])
        for patient in created_patients:
            self.safe_delete_patient(patient['id'])

    def test_get_platzsuchen_filtered_by_status(self):
        """Test filtering platzsuche by status."""
        patient = self.create_test_patient()
        
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert search_response.status_code == 201
        search = search_response.json()
        
        # Update one to pausiert
        update_response = requests.put(
            f"{BASE_URL}/platzsuchen/{search['id']}",
            json={"status": "pausiert"}
        )
        assert update_response.status_code == 200
        
        # Filter by status
        response = requests.get(f"{BASE_URL}/platzsuchen?status=pausiert")
        assert response.status_code == 200
        
        data = response.json()
        searches = data['data']
        
        # Check that all returned searches have correct status
        for s in searches:
            assert s['status'] == "pausiert"
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_patient(patient['id'])

    def test_get_therapeutenanfragen_list_empty(self):
        """Test getting empty therapeutenanfrage list with pagination."""
        response = requests.get(f"{BASE_URL}/therapeutenanfragen")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 0
        assert 'summary' in data

    def test_get_therapeutenanfragen_with_pagination(self):
        """Test therapeutenanfrage pagination parameters."""
        response = requests.get(f"{BASE_URL}/therapeutenanfragen?page=1&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 5
        assert len(data['data']) <= 5

    def test_pagination_limits(self):
        """Test pagination limit constraints."""
        # Test max limit
        response = requests.get(f"{BASE_URL}/platzsuchen?limit=2000")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1000  # Should be capped
        
        # Test zero limit
        response = requests.get(f"{BASE_URL}/therapeutenanfragen?limit=0")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1  # Should be minimum

    # ==================== CONSTRAINT TESTS ====================

    def test_matching_with_diverse_gender_patients(self):
        """Test matching service with patients of diverse gender."""
        patient_diverse = self.create_test_patient(
            geschlecht="divers",
            vorname="Alex",
            email="alex.diverse@example.com"
        )
        
        patient_keine_angabe = self.create_test_patient(
            geschlecht="keine_Angabe",
            vorname="Chris",
            email="chris.nogender@example.com"
        )
        
        # Create searches
        search1_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient_diverse['id']}
        )
        assert search1_response.status_code == 201
        search1 = search1_response.json()
        
        search2_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient_keine_angabe['id']}
        )
        assert search2_response.status_code == 201
        search2 = search2_response.json()
        
        # Verify searches created successfully
        assert search1['patient_id'] == patient_diverse['id']
        assert search2['patient_id'] == patient_keine_angabe['id']
        
        # Cleanup
        self.safe_delete_platzsuche(search1['id'])
        self.safe_delete_platzsuche(search2['id'])
        self.safe_delete_patient(patient_diverse['id'])
        self.safe_delete_patient(patient_keine_angabe['id'])

    def test_matching_with_diverse_gender_therapists(self):
        """Test therapist selection with diverse gender therapists."""
        therapist_diverse = self.create_test_therapist(
            geschlecht="divers",
            vorname="Alex",
            plz="52064",
            email="alex.diverse.therapist@example.com"
        )
        
        therapist_keine_angabe = self.create_test_therapist(
            geschlecht="keine_Angabe",
            vorname="Chris",
            plz="52065",
            email="chris.nogender.therapist@example.com"
        )
        
        # Get therapists for selection
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52")
        assert response.status_code == 200
        
        data = response.json()
        therapists = data['data']
        
        therapist_ids = [t['id'] for t in therapists]
        
        # Verify diverse therapists are included
        assert therapist_diverse['id'] in therapist_ids
        assert therapist_keine_angabe['id'] in therapist_ids
        
        # Cleanup
        self.safe_delete_therapist(therapist_diverse['id'])
        self.safe_delete_therapist(therapist_keine_angabe['id'])

    def test_patient_with_therapy_experience(self):
        """Test patient validation when therapy experience is true."""
        patient = self.create_test_patient(
            erfahrung_mit_psychotherapie=True,
            letzte_sitzung_vorherige_psychotherapie="2023-05-15"
        )
        
        # Should be able to create platzsuche
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert search_response.status_code == 201
        search = search_response.json()
        
        # Cleanup
        self.safe_delete_platzsuche(search['id'])
        self.safe_delete_patient(patient['id'])

    def test_patient_validation_errors(self):
        """Test that patient validation works correctly without diagnosis."""
        # Create patient with missing required fields (no diagnosis required)
        incomplete_patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Incomplete",
            "nachname": "Patient",
            "email": "incomplete@example.com"
            # Missing: symptome, krankenkasse, geburtsdatum, etc.
        }
        
        response = requests.post(f"{PATIENT_BASE_URL}/patients", json=incomplete_patient_data)
        # Patient creation might succeed with minimal data
        if response.status_code == 201:
            incomplete_patient = response.json()
            
            # Try to create platzsuche with incomplete patient
            search_data = {
                "patient_id": incomplete_patient['id'],
                "notizen": "This should fail"
            }
            
            response = requests.post(f"{BASE_URL}/platzsuchen", json=search_data)
            assert response.status_code == 400
            
            error_message = response.json()['message']
            assert "Cannot create platzsuche" in error_message
            # Should check for symptome but NOT diagnosis
            assert "symptome" in error_message.lower() or "krankenkasse" in error_message.lower()
            assert "diagnose" not in error_message.lower()
            
            # Cleanup
            self.safe_delete_patient(incomplete_patient['id'])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])