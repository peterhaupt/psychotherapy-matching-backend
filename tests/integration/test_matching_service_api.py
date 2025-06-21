"""Integration tests for Matching Service API.

This test suite verifies all matching service endpoints work exactly as described
in API_REFERENCE.md. All field names use German terminology (anfrage instead of bundle).

Prerequisites:
- Docker environment must be running
- All services (patient, therapist, matching, communication) must be accessible
- Database must be available
"""
import pytest
import requests
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

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

# Base URLs for all services
MATCHING_BASE_URL = f"http://localhost:{config.MATCHING_SERVICE_PORT}/api"
PATIENT_BASE_URL = f"http://localhost:{config.PATIENT_SERVICE_PORT}/api"
THERAPIST_BASE_URL = f"http://localhost:{config.THERAPIST_SERVICE_PORT}/api"
COMM_BASE_URL = f"http://localhost:{config.COMMUNICATION_SERVICE_PORT}/api"


class TestMatchingServiceAPI:
    """Test all Matching Service API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup before each test and cleanup after."""
        self.created_platzsuche_ids: List[int] = []
        self.created_anfrage_ids: List[int] = []
        self.created_patient_ids: List[int] = []
        self.created_therapist_ids: List[int] = []
        self.base_headers = {'Content-Type': 'application/json'}
        
        # Create test patients and therapists for use in tests
        self._create_test_data()
        
        yield
        
        # Cleanup: Delete all created resources in reverse order
        # Delete platzsuchen first (they reference patients)
        for search_id in self.created_platzsuche_ids:
            try:
                requests.delete(f"{MATCHING_BASE_URL}/platzsuchen/{search_id}")
            except:
                pass
        
        # Delete patients
        for patient_id in self.created_patient_ids:
            try:
                requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_id}")
            except:
                pass
        
        # Delete therapists
        for therapist_id in self.created_therapist_ids:
            try:
                requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_id}")
            except:
                pass
    
    def _create_test_data(self):
        """Create test patients and therapists with different PLZ prefixes."""
        # Create patients in different PLZ areas
        self.test_patients = {
            '52': [],  # Aachen area
            '10': [],  # Berlin area
            '80': []   # Munich area
        }
        
        # Create 3 patients per PLZ area
        for plz_prefix in self.test_patients.keys():
            for i in range(3):
                patient_data = {
                    "vorname": f"Test{i}",
                    "nachname": f"Patient{plz_prefix}",
                    "plz": f"{plz_prefix}{str(100 + i).zfill(3)}",
                    "ort": f"Stadt{plz_prefix}",
                    "email": f"patient{plz_prefix}_{i}@test.com",
                    "diagnose": "F32.1" if i == 0 else "F41.1",
                    "bevorzugtes_therapeutengeschlecht": "Egal" if i == 0 else ("Männlich" if i == 1 else "Weiblich"),
                    "offen_fuer_gruppentherapie": i != 1,
                    "raeumliche_verfuegbarkeit": {"max_km": 20 if i == 0 else 30},
                    "geburtsdatum": f"{1990 - i * 10}-01-15",
                    "bevorzugtes_therapieverfahren": ["Verhaltenstherapie"] if i == 0 else ["egal"],
                    "bevorzugtes_therapeutenalter_min": 30 if i == 1 else None,
                    "bevorzugtes_therapeutenalter_max": 50 if i == 1 else None
                }
                
                response = requests.post(
                    f"{PATIENT_BASE_URL}/patients",
                    json=patient_data,
                    headers=self.base_headers
                )
                
                if response.status_code == 201:
                    patient = response.json()
                    self.created_patient_ids.append(patient['id'])
                    self.test_patients[plz_prefix].append(patient)
        
        # Create therapists in different PLZ areas
        self.test_therapists = {
            '52': [],
            '10': [],
            '80': []
        }
        
        # Create 2 therapists per PLZ area with different characteristics
        for plz_prefix in self.test_therapists.keys():
            for i in range(2):
                therapist_data = {
                    "vorname": f"Dr{i}",
                    "nachname": f"Therapeut{plz_prefix}",
                    "titel": "Dr. med.",
                    "plz": f"{plz_prefix}{str(200 + i).zfill(3)}",
                    "ort": f"Stadt{plz_prefix}",
                    "strasse": f"Praxisstr. {i+1}",
                    "email": f"therapeut{plz_prefix}_{i}@test.com",
                    "geschlecht": "männlich" if i == 0 else "weiblich",
                    "potenziell_verfuegbar": True,
                    "ueber_curavani_informiert": i == 0,
                    "naechster_kontakt_moeglich": None if i == 0 else (date.today() + timedelta(days=30)).isoformat(),
                    "bevorzugte_diagnosen": ["F32", "F41"] if i == 0 else ["F43"],
                    "alter_min": 18,
                    "alter_max": 65 if i == 0 else 45,
                    "geschlechtspraeferenz": "Egal",
                    "psychotherapieverfahren": ["Verhaltenstherapie", "Tiefenpsychologie"],
                    "bevorzugt_gruppentherapie": i == 1,
                    "geburtsdatum": f"{1970 + i * 5}-06-15"
                }
                
                response = requests.post(
                    f"{THERAPIST_BASE_URL}/therapists",
                    json=therapist_data,
                    headers=self.base_headers
                )
                
                if response.status_code == 201:
                    therapist = response.json()
                    self.created_therapist_ids.append(therapist['id'])
                    self.test_therapists[plz_prefix].append(therapist)
    
    def create_platzsuche(self, patient_id: int, **kwargs) -> Dict[str, Any]:
        """Helper to create a platzsuche and track it for cleanup."""
        data = {
            "patient_id": patient_id
        }
        data.update(kwargs)
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen",
            json=data,
            headers=self.base_headers
        )
        
        if response.status_code == 201:
            search = response.json()
            self.created_platzsuche_ids.append(search['id'])
            return search
        else:
            raise Exception(f"Failed to create platzsuche: {response.status_code} - {response.text}")
    
    # --- Platzsuche (Patient Search) Tests ---
    
    def test_get_platzsuchen_empty(self):
        """Test getting empty platzsuche list."""
        response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen")
        assert response.status_code == 200
        
        data = response.json()
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert 'page' in data
        assert 'limit' in data
        assert 'total' in data
    
    def test_get_platzsuchen_with_data(self):
        """Test getting platzsuche list with data."""
        # Create searches for different patients
        patient1 = self.test_patients['52'][0]
        patient2 = self.test_patients['10'][0]
        
        search1 = self.create_platzsuche(patient1['id'], notizen="Test search 1")
        search2 = self.create_platzsuche(patient2['id'], notizen="Test search 2")
        
        response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen")
        assert response.status_code == 200
        
        data = response.json()
        searches = data['data']
        assert len(searches) >= 2
        
        # Verify our searches are in the list
        search_ids = [s['id'] for s in searches]
        assert search1['id'] in search_ids
        assert search2['id'] in search_ids
        
        # Verify German field names
        for search in searches:
            assert 'patienten_name' in search
            assert 'gesamt_angeforderte_kontakte' in search
            assert 'aktive_anfragen' in search  # Not aktive_buendel
            assert 'gesamt_anfragen' in search  # Not gesamt_buendel
    
    def test_get_platzsuchen_filter_by_status(self):
        """Test filtering platzsuchen by status with German values."""
        patient = self.test_patients['52'][0]
        
        # Create searches with different statuses
        search1 = self.create_platzsuche(patient['id'])
        
        # Update one to different status
        update_response = requests.put(
            f"{MATCHING_BASE_URL}/platzsuchen/{search1['id']}",
            json={"status": "pausiert"},
            headers=self.base_headers
        )
        assert update_response.status_code == 200
        
        # Create another active search
        search2 = self.create_platzsuche(self.test_patients['52'][1]['id'])
        
        # Filter by status
        response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen?status=aktiv")
        assert response.status_code == 200
        
        data = response.json()
        searches = data['data']
        search_ids = [s['id'] for s in searches]
        
        assert search2['id'] in search_ids
        assert search1['id'] not in search_ids
    
    def test_get_platzsuchen_filter_by_patient(self):
        """Test filtering platzsuchen by patient_id."""
        patient1 = self.test_patients['52'][0]
        patient2 = self.test_patients['52'][1]
        
        search1 = self.create_platzsuche(patient1['id'])
        search2 = self.create_platzsuche(patient2['id'])
        
        response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen?patient_id={patient1['id']}")
        assert response.status_code == 200
        
        data = response.json()
        searches = data['data']
        
        assert len(searches) == 1
        assert searches[0]['patient_id'] == patient1['id']
    
    def test_get_platzsuche_by_id(self):
        """Test getting specific platzsuche with full details."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(
            patient['id'],
            notizen="Detailed test search"
        )
        
        response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        assert response.status_code == 200
        
        detailed = response.json()
        assert detailed['id'] == search['id']
        assert detailed['patient_id'] == patient['id']
        assert 'patient' in detailed
        assert detailed['patient']['vorname'] == patient['vorname']
        assert 'anfrage_verlauf' in detailed  # Not bundle_verlauf
        assert isinstance(detailed['anfrage_verlauf'], list)
        assert detailed['notizen'] == "Detailed test search"
    
    def test_get_platzsuche_not_found(self):
        """Test getting non-existent platzsuche returns 404."""
        response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen/99999999")
        assert response.status_code == 404
        
        error = response.json()
        assert 'message' in error
        assert 'not found' in error['message'].lower()
    
    def test_create_platzsuche_minimal(self):
        """Test creating platzsuche with minimal data."""
        patient = self.test_patients['52'][0]
        
        data = {"patient_id": patient['id']}
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        search = response.json()
        self.created_platzsuche_ids.append(search['id'])
        
        assert search['patient_id'] == patient['id']
        assert search['status'] == "aktiv"
        assert 'message' in search
    
    def test_create_platzsuche_duplicate_active(self):
        """Test creating duplicate active search is rejected."""
        patient = self.test_patients['52'][0]
        
        # Create first search
        search1 = self.create_platzsuche(patient['id'])
        
        # Try to create another active search for same patient
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']},
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'already has an active search' in error['message']
    
    def test_create_platzsuche_invalid_patient(self):
        """Test creating platzsuche with invalid patient_id."""
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen",
            json={"patient_id": 99999999},
            headers=self.base_headers
        )
        
        assert response.status_code == 404
        error = response.json()
        assert 'not found' in error['message'].lower()
    
    def test_update_platzsuche_status(self):
        """Test updating platzsuche status with German values."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Test status transitions
        status_updates = ["pausiert", "aktiv", "erfolgreich"]
        
        for new_status in status_updates:
            response = requests.put(
                f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}",
                json={"status": new_status},
                headers=self.base_headers
            )
            
            assert response.status_code == 200
            assert 'message' in response.json()
    
    def test_update_platzsuche_exclusions(self):
        """Test updating excluded therapists list."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        therapist_ids = [t['id'] for t in self.test_therapists['52']]
        
        response = requests.put(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}",
            json={"ausgeschlossene_therapeuten": therapist_ids},
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        
        # Verify update
        get_response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        updated = get_response.json()
        assert set(updated['ausgeschlossene_therapeuten']) == set(therapist_ids)
    
    def test_delete_platzsuche_cancels(self):
        """Test that deleting a platzsuche cancels it (not deletes)."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        response = requests.delete(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        assert response.status_code == 200
        
        # Verify it still exists but is cancelled
        get_response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        assert get_response.status_code == 200
        
        cancelled = get_response.json()
        assert cancelled['status'] == "abgebrochen"
    
    # --- Kontaktanfrage Tests ---
    
    def test_kontaktanfrage_valid(self):
        """Test requesting additional contacts."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        data = {
            "requested_count": 10,
            "notizen": "Patient still searching"
        }
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}/kontaktanfrage",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['new_total'] == 10
        assert result['previous_total'] == 0
    
    def test_kontaktanfrage_invalid_count(self):
        """Test kontaktanfrage with invalid counts."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Test zero count
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}/kontaktanfrage",
            json={"requested_count": 0},
            headers=self.base_headers
        )
        assert response.status_code == 400
        
        # Test too high count
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}/kontaktanfrage",
            json={"requested_count": 101},
            headers=self.base_headers
        )
        assert response.status_code == 400
    
    def test_kontaktanfrage_wrong_status(self):
        """Test kontaktanfrage on non-active search."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Cancel the search
        requests.delete(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        
        # Try to request contacts
        response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}/kontaktanfrage",
            json={"requested_count": 5},
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'only request contacts for active searches' in error['message'].lower()
    
    # --- Therapist Selection Tests ---
    
    def test_therapeuten_zur_auswahl_valid_plz(self):
        """Test getting therapists for selection with valid PLZ prefix."""
        response = requests.get(f"{MATCHING_BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52")
        assert response.status_code == 200
        
        data = response.json()
        assert 'plz_prefix' in data
        assert data['plz_prefix'] == '52'
        assert 'total' in data
        assert 'data' in data
        assert isinstance(data['data'], list)
        
        # Verify only therapists from PLZ 52 area
        for therapist in data['data']:
            assert therapist['plz'].startswith('52')
        
        # Verify sorting (available + informed should be first)
        if len(data['data']) >= 2:
            first = data['data'][0]
            # First therapist should have optimal characteristics
            assert first['potenziell_verfuegbar'] == True or first['ueber_curavani_informiert'] == True
    
    def test_therapeuten_zur_auswahl_invalid_plz(self):
        """Test therapist selection with invalid PLZ prefix."""
        # Not 2 digits
        response = requests.get(f"{MATCHING_BASE_URL}/therapeuten-zur-auswahl?plz_prefix=5")
        assert response.status_code == 400
        error = response.json()
        assert 'must be exactly 2 digits' in error['message']
        
        # Non-numeric
        response = requests.get(f"{MATCHING_BASE_URL}/therapeuten-zur-auswahl?plz_prefix=AB")
        assert response.status_code == 400
        
        # Missing parameter
        response = requests.get(f"{MATCHING_BASE_URL}/therapeuten-zur-auswahl")
        assert response.status_code == 400
    
    def test_therapeuten_zur_auswahl_contactable_only(self):
        """Test that only contactable therapists are returned."""
        # Set one therapist to not contactable (cooling period)
        therapist = self.test_therapists['52'][0]
        future_date = (date.today() + timedelta(days=30)).isoformat()
        
        requests.put(
            f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}",
            json={"naechster_kontakt_moeglich": future_date},
            headers=self.base_headers
        )
        
        # Get therapists for selection
        response = requests.get(f"{MATCHING_BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52")
        assert response.status_code == 200
        
        data = response.json()
        therapist_ids = [t['id'] for t in data['data']]
        
        # The therapist with future contact date should not be included
        assert therapist['id'] not in therapist_ids
    
    # --- Therapeutenanfrage (Inquiry) Tests ---
    
    def test_get_therapeutenanfragen_empty(self):
        """Test getting empty therapeutenanfrage list."""
        response = requests.get(f"{MATCHING_BASE_URL}/therapeutenanfragen")
        assert response.status_code == 200
        
        data = response.json()
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert 'summary' in data
        assert data['summary']['total_anfragen'] == 0  # Not total_bundles
    
    def test_create_anfrage_for_therapist(self):
        """Test creating anfrage for manually selected therapist."""
        therapist = self.test_therapists['52'][0]
        
        # Create active searches for patients in same PLZ area
        for patient in self.test_patients['52'][:2]:
            self.create_platzsuche(patient['id'])
        
        data = {
            "therapist_id": therapist['id'],
            "plz_prefix": "52",
            "sofort_senden": False
        }
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        
        result = response.json()
        assert 'anfrage_id' in result  # Not bundle_id
        assert 'anfragegroesse' in result  # Not buendelgroesse
        assert result['anfragegroesse'] >= 1
        assert result['therapist_id'] == therapist['id']
        assert result['gesendet'] == False
        
        self.created_anfrage_ids.append(result['anfrage_id'])
    
    def test_create_anfrage_no_eligible_patients(self):
        """Test creating anfrage when no patients match."""
        therapist = self.test_therapists['10'][0]  # Berlin therapist
        
        # Create searches only for Aachen patients (PLZ 52)
        for patient in self.test_patients['52']:
            self.create_platzsuche(patient['id'])
        
        data = {
            "therapist_id": therapist['id'],
            "plz_prefix": "10"  # No patients in Berlin area
        }
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json=data,
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert 'no eligible patients found' in result['message'].lower()
    
    def test_create_anfrage_hard_constraints(self):
        """Test that hard constraints are properly enforced."""
        # Create a patient with specific preferences
        patient_data = {
            "vorname": "Specific",
            "nachname": "Preferences",
            "plz": "52100",
            "ort": "Aachen",
            "bevorzugtes_therapeutengeschlecht": "Weiblich",  # Only female
            "bevorzugtes_therapieverfahren": ["Verhaltenstherapie"],
            "offen_fuer_gruppentherapie": False,
            "raeumliche_verfuegbarkeit": {"max_km": 5}  # Very limited distance
        }
        
        patient_response = requests.post(
            f"{PATIENT_BASE_URL}/patients",
            json=patient_data,
            headers=self.base_headers
        )
        patient = patient_response.json()
        self.created_patient_ids.append(patient['id'])
        
        # Create search for this patient
        self.create_platzsuche(patient['id'])
        
        # Try with male therapist - should not match
        male_therapist = self.test_therapists['52'][0]  # This is male
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": male_therapist['id'],
                "plz_prefix": "52"
            },
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        # Should have no eligible patients due to gender preference
        assert 'no eligible patients' in result['message'].lower()
    
    def test_get_therapeutenanfragen_with_filters(self):
        """Test getting anfragen with various filters."""
        # Create some anfragen first
        therapist = self.test_therapists['52'][0]
        for patient in self.test_patients['52'][:2]:
            self.create_platzsuche(patient['id'])
        
        # Create anfrage
        create_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52"
            },
            headers=self.base_headers
        )
        anfrage = create_response.json()
        self.created_anfrage_ids.append(anfrage['anfrage_id'])
        
        # Test filter by therapist
        response = requests.get(f"{MATCHING_BASE_URL}/therapeutenanfragen?therapist_id={therapist['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) >= 1
        
        # Test filter by versand_status
        response = requests.get(f"{MATCHING_BASE_URL}/therapeutenanfragen?versand_status=ungesendet")
        assert response.status_code == 200
        
        # Test filter by size
        response = requests.get(f"{MATCHING_BASE_URL}/therapeutenanfragen?min_size=1&max_size=6")
        assert response.status_code == 200
    
    def test_get_therapeutenanfrage_details(self):
        """Test getting specific anfrage with full details."""
        # Setup: Create anfrage
        therapist = self.test_therapists['52'][0]
        for patient in self.test_patients['52'][:3]:
            self.create_platzsuche(patient['id'])
        
        create_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52"
            },
            headers=self.base_headers
        )
        anfrage_data = create_response.json()
        anfrage_id = anfrage_data['anfrage_id']
        self.created_anfrage_ids.append(anfrage_id)
        
        # Get details
        response = requests.get(f"{MATCHING_BASE_URL}/therapeutenanfragen/{anfrage_id}")
        assert response.status_code == 200
        
        details = response.json()
        assert details['id'] == anfrage_id
        assert 'therapist' in details
        assert 'patients' in details
        assert len(details['patients']) >= 1
        
        # Verify patient details structure
        for patient in details['patients']:
            assert 'position' in patient
            assert 'patient_id' in patient
            assert 'platzsuche_id' in patient
            assert 'wartezeit_tage' in patient
            assert patient['status'] == "anstehend"  # German value
    
    def test_record_anfrage_response_full_acceptance(self):
        """Test recording full acceptance response."""
        # Setup: Create and send anfrage
        therapist = self.test_therapists['52'][0]
        patients = []
        for patient in self.test_patients['52'][:2]:
            search = self.create_platzsuche(patient['id'])
            patients.append(patient)
        
        create_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": True  # Send immediately
            },
            headers=self.base_headers
        )
        anfrage_data = create_response.json()
        anfrage_id = anfrage_data['anfrage_id']
        patient_ids = anfrage_data['patient_ids']
        self.created_anfrage_ids.append(anfrage_id)
        
        # Record full acceptance
        patient_responses = {
            str(pid): "angenommen" for pid in patient_ids
        }
        
        response = requests.put(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/{anfrage_id}/antwort",
            json={
                "patient_responses": patient_responses,
                "notizen": "Can take all patients"
            },
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['response_type'] == "vollstaendige_Annahme"  # German value
        assert len(result['angenommene_patienten']) == len(patient_ids)
    
    def test_record_anfrage_response_partial(self):
        """Test recording partial acceptance response."""
        # Setup similar to above but with 3 patients
        therapist = self.test_therapists['52'][0]
        for patient in self.test_patients['52']:
            self.create_platzsuche(patient['id'])
        
        create_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": True
            },
            headers=self.base_headers
        )
        anfrage_data = create_response.json()
        anfrage_id = anfrage_data['anfrage_id']
        patient_ids = anfrage_data['patient_ids']
        self.created_anfrage_ids.append(anfrage_id)
        
        # Accept 1, reject others
        patient_responses = {}
        for i, pid in enumerate(patient_ids):
            if i == 0:
                patient_responses[str(pid)] = "angenommen"
            else:
                patient_responses[str(pid)] = "abgelehnt_Kapazitaet"
        
        response = requests.put(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/{anfrage_id}/antwort",
            json={"patient_responses": patient_responses},
            headers=self.base_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['response_type'] == "teilweise_Annahme"
        assert result['antwort_zusammenfassung']['accepted'] == 1
        assert result['antwort_zusammenfassung']['rejected'] == len(patient_ids) - 1
    
    def test_record_response_invalid_patient(self):
        """Test recording response with invalid patient ID."""
        # Create anfrage
        therapist = self.test_therapists['52'][0]
        patient = self.test_patients['52'][0]
        self.create_platzsuche(patient['id'])
        
        create_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": True
            },
            headers=self.base_headers
        )
        anfrage_data = create_response.json()
        anfrage_id = anfrage_data['anfrage_id']
        self.created_anfrage_ids.append(anfrage_id)
        
        # Try to record response for wrong patient
        response = requests.put(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/{anfrage_id}/antwort",
            json={
                "patient_responses": {
                    "99999": "angenommen"  # Invalid patient ID
                }
            },
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert 'extra_patient_ids' in error['message'] or 'not in anfrage' in error['message'].lower()
    
    # --- German Enum Tests ---
    
    def test_suchstatus_enum_values(self):
        """Test all German SuchStatus enum values."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Test valid status values
        valid_statuses = ["aktiv", "erfolgreich", "pausiert", "abgebrochen"]
        
        # Can only test certain transitions due to business rules
        # aktiv -> pausiert -> aktiv -> erfolgreich
        transitions = [
            ("pausiert", 200),
            ("aktiv", 200),
            ("erfolgreich", 200)
        ]
        
        for status, expected_code in transitions:
            response = requests.put(
                f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}",
                json={"status": status},
                headers=self.base_headers
            )
            assert response.status_code == expected_code
        
        # Test invalid status
        response = requests.put(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}",
            json={"status": "ACTIVE"},  # English value
            headers=self.base_headers
        )
        assert response.status_code == 400
    
    def test_patientenergebnis_enum_values(self):
        """Test all German PatientenErgebnis enum values."""
        # Create anfrage
        therapist = self.test_therapists['52'][0]
        for patient in self.test_patients['52'][:3]:
            self.create_platzsuche(patient['id'])
        
        create_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": True
            },
            headers=self.base_headers
        )
        anfrage_data = create_response.json()
        anfrage_id = anfrage_data['anfrage_id']
        patient_ids = anfrage_data['patient_ids']
        self.created_anfrage_ids.append(anfrage_id)
        
        # Test different outcome values
        valid_outcomes = [
            "angenommen",
            "abgelehnt_Kapazitaet",
            "abgelehnt_nicht_geeignet",
            "abgelehnt_sonstiges"
        ]
        
        patient_responses = {}
        for i, pid in enumerate(patient_ids[:len(valid_outcomes)]):
            if i < len(valid_outcomes):
                patient_responses[str(pid)] = valid_outcomes[i]
        
        response = requests.put(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/{anfrage_id}/antwort",
            json={"patient_responses": patient_responses},
            headers=self.base_headers
        )
        
        assert response.status_code == 200
    
    # --- Complex Scenario Tests ---
    
    def test_complete_matching_lifecycle(self):
        """Test complete lifecycle from search creation to successful match."""
        # 1. Create patient and search
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'], notizen="Complete lifecycle test")
        
        # 2. Request contacts
        contact_response = requests.post(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}/kontaktanfrage",
            json={"requested_count": 25},
            headers=self.base_headers
        )
        assert contact_response.status_code == 200
        
        # 3. Get therapists for selection
        selection_response = requests.get(
            f"{MATCHING_BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52"
        )
        assert selection_response.status_code == 200
        therapists = selection_response.json()['data']
        assert len(therapists) > 0
        
        # 4. Create anfrage for selected therapist
        therapist_id = therapists[0]['id']
        anfrage_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist_id,
                "plz_prefix": "52",
                "sofort_senden": True
            },
            headers=self.base_headers
        )
        assert anfrage_response.status_code == 201
        anfrage_data = anfrage_response.json()
        anfrage_id = anfrage_data['anfrage_id']
        self.created_anfrage_ids.append(anfrage_id)
        
        # 5. Record therapist acceptance
        patient_responses = {
            str(patient['id']): "angenommen"
        }
        
        response_result = requests.put(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/{anfrage_id}/antwort",
            json={"patient_responses": patient_responses},
            headers=self.base_headers
        )
        assert response_result.status_code == 200
        
        # 6. Verify search is now successful
        final_search = requests.get(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        assert final_search.status_code == 200
        final_data = final_search.json()
        assert final_data['status'] == "erfolgreich"
    
    def test_parallel_search_multiple_anfragen(self):
        """Test patient can be in multiple anfragen simultaneously."""
        # Create patient and search
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Create anfragen with different therapists
        therapist_ids = []
        anfrage_ids = []
        
        for therapist in self.test_therapists['52']:
            response = requests.post(
                f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
                json={
                    "therapist_id": therapist['id'],
                    "plz_prefix": "52"
                },
                headers=self.base_headers
            )
            
            if response.status_code == 201:
                result = response.json()
                therapist_ids.append(therapist['id'])
                anfrage_ids.append(result['anfrage_id'])
                self.created_anfrage_ids.append(result['anfrage_id'])
        
        # Verify patient appears in multiple anfragen
        search_details = requests.get(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        anfrage_verlauf = search_details.json()['anfrage_verlauf']
        
        assert len(anfrage_verlauf) >= 2  # Patient in multiple anfragen
    
    def test_exclusion_list_management(self):
        """Test that exclusion list is properly managed."""
        patient = self.test_patients['52'][0]
        therapist = self.test_therapists['52'][0]
        
        # Create search with excluded therapist
        search = self.create_platzsuche(patient['id'])
        
        # Add therapist to exclusion list
        response = requests.put(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}",
            json={"ausgeschlossene_therapeuten": [therapist['id']]},
            headers=self.base_headers
        )
        assert response.status_code == 200
        
        # Try to create anfrage - should get no patients
        anfrage_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52"
            },
            headers=self.base_headers
        )
        
        assert anfrage_response.status_code == 200
        result = anfrage_response.json()
        assert 'no eligible patients' in result['message'].lower()
    
    def test_terminology_verification(self):
        """Verify no bundle terminology appears in responses."""
        # Create some data
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Check platzsuche response
        search_response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}")
        search_text = str(search_response.json())
        
        # Verify no "bundle" references
        assert 'bundle' not in search_text.lower()
        assert 'buendel' not in search_text.lower()
        
        # Verify correct terminology is used
        assert 'anfrage' in search_text.lower()
        
        # Check list response
        list_response = requests.get(f"{MATCHING_BASE_URL}/platzsuchen")
        list_text = str(list_response.json())
        
        # Should use anfragen not bundles
        assert 'aktive_anfragen' in list_text
        assert 'gesamt_anfragen' in list_text
        assert 'aktive_buendel' not in list_text
        assert 'gesamt_buendel' not in list_text
    
    def test_single_patient_anfrage(self):
        """Test that single patient anfragen are allowed (MIN=1)."""
        # Create only one patient search
        patient = self.test_patients['80'][0]  # Munich patient
        search = self.create_platzsuche(patient['id'])
        
        therapist = self.test_therapists['80'][0]  # Munich therapist
        
        # Create anfrage
        response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "80"
            },
            headers=self.base_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result['anfragegroesse'] == 1  # Single patient allowed
        self.created_anfrage_ids.append(result['anfrage_id'])
    
    def test_age_preference_constraints(self):
        """Test that age preferences are properly enforced."""
        # Create patient with age preference
        patient_data = {
            "vorname": "AgePref",
            "nachname": "Test",
            "plz": "52000",
            "ort": "Aachen",
            "bevorzugtes_therapeutenalter_min": 40,
            "bevorzugtes_therapeutenalter_max": 50,
            "geburtsdatum": "1990-01-01"
        }
        
        patient_response = requests.post(
            f"{PATIENT_BASE_URL}/patients",
            json=patient_data,
            headers=self.base_headers
        )
        patient = patient_response.json()
        self.created_patient_ids.append(patient['id'])
        
        search = self.create_platzsuche(patient['id'])
        
        # Young therapist (born 1970, ~55 years old) - outside preference
        therapist = self.test_therapists['52'][0]
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52"
            },
            headers=self.base_headers
        )
        
        # Should not match due to age preference
        assert response.status_code == 200
        result = response.json()
        assert 'no eligible patients' in result['message'].lower()
    
    def test_therapy_procedure_matching(self):
        """Test therapy procedure preference matching."""
        # Patient wants specific procedure
        patient_data = {
            "vorname": "Procedure",
            "nachname": "Test",
            "plz": "52000",
            "ort": "Aachen",
            "bevorzugtes_therapieverfahren": ["Psychoanalyse"]  # Not offered by test therapists
        }
        
        patient_response = requests.post(
            f"{PATIENT_BASE_URL}/patients",
            json=patient_data,
            headers=self.base_headers
        )
        patient = patient_response.json()
        self.created_patient_ids.append(patient['id'])
        
        search = self.create_platzsuche(patient['id'])
        
        # Therapist only offers Verhaltenstherapie and Tiefenpsychologie
        therapist = self.test_therapists['52'][0]
        
        response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52"
            },
            headers=self.base_headers
        )
        
        # Should not match
        assert response.status_code == 200
        result = response.json()
        assert 'no eligible patients' in result['message'].lower()
    
    def test_invalid_enum_rejection(self):
        """Test that invalid enum values are properly rejected."""
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Test invalid search status
        response = requests.put(
            f"{MATCHING_BASE_URL}/platzsuchen/{search['id']}",
            json={"status": "searching"},  # English value
            headers=self.base_headers
        )
        
        assert response.status_code == 400
        error = response.json()
        assert "Invalid status 'searching'" in error['message']
        assert "Valid values:" in error['message']
        assert "aktiv" in error['message']
    
    def test_cooling_period_enforcement(self):
        """Test that cooling period is enforced after response."""
        # Create anfrage and record response
        therapist = self.test_therapists['52'][0]
        patient = self.test_patients['52'][0]
        search = self.create_platzsuche(patient['id'])
        
        # Create and send anfrage
        create_response = requests.post(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/erstellen-fuer-therapeut",
            json={
                "therapist_id": therapist['id'],
                "plz_prefix": "52",
                "sofort_senden": True
            },
            headers=self.base_headers
        )
        anfrage_data = create_response.json()
        anfrage_id = anfrage_data['anfrage_id']
        self.created_anfrage_ids.append(anfrage_id)
        
        # Record response
        patient_responses = {
            str(patient['id']): "angenommen"
        }
        
        response = requests.put(
            f"{MATCHING_BASE_URL}/therapeutenanfragen/{anfrage_id}/antwort",
            json={"patient_responses": patient_responses},
            headers=self.base_headers
        )
        assert response.status_code == 200
        
        # Verify therapist now has cooling period
        therapist_response = requests.get(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")
        updated_therapist = therapist_response.json()
        
        assert updated_therapist['naechster_kontakt_moeglich'] is not None
        next_contact = datetime.fromisoformat(updated_therapist['naechster_kontakt_moeglich'])
        assert next_contact.date() > date.today()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])
