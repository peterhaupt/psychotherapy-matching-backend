"""Integration tests for Matching Service API with pagination support."""
import pytest
import requests
import time
from datetime import date, datetime

# Base URL for the Matching Service
BASE_URL = "http://localhost:8003/api"

# Base URLs for other services (for setup)
PATIENT_BASE_URL = "http://localhost:8001/api"
THERAPIST_BASE_URL = "http://localhost:8002/api"


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
        """Helper to create a test patient in patient service."""
        default_data = {
            "anrede": "Herr",  # Required field
            "geschlecht": "männlich",  # Required field
            "vorname": "Test",
            "nachname": "Patient",
            "plz": "52064",  # Aachen PLZ for testing
            "ort": "Aachen",
            "email": "test.patient@example.com",
            "diagnose": "F32.1"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{PATIENT_BASE_URL}/patients", json=data)
        assert response.status_code == 201
        return response.json()

    def create_test_therapist(self, **kwargs):
        """Helper to create a test therapist in therapist service."""
        default_data = {
            "anrede": "Herr",  # Required field
            "geschlecht": "männlich",  # Required field
            "vorname": "Test",
            "nachname": "Therapeut",
            "plz": "52062",  # Matching PLZ prefix
            "ort": "Aachen",
            "email": "test.therapeut@example.com",
            "status": "aktiv",
            "potenziell_verfuegbar": True,
            "ueber_curavani_informiert": True
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{THERAPIST_BASE_URL}/therapists", json=data)
        assert response.status_code == 201
        return response.json()

    # Platzsuche (Patient Search) Tests

    def test_create_platzsuche(self):
        """Test creating a new patient search."""
        # Create a patient first
        patient = self.create_test_patient()
        
        # Create platzsuche
        search_data = {
            "patient_id": patient['id'],
            "notizen": "Test patient search"
        }
        
        response = requests.post(f"{BASE_URL}/platzsuchen", json=search_data)
        assert response.status_code == 201
        
        created_search = response.json()
        assert created_search["patient_id"] == patient['id']
        assert created_search["status"] == "aktiv"
        assert "id" in created_search
        
        # Cleanup
        requests.delete(f"{BASE_URL}/platzsuchen/{created_search['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_get_platzsuchen_list_empty(self):
        """Test getting empty platzsuche list with pagination."""
        response = requests.get(f"{BASE_URL}/platzsuchen")
        assert response.status_code == 200
        
        # Expecting paginated structure
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 0

    def test_get_platzsuchen_list_with_data(self):
        """Test getting platzsuche list with data and pagination."""
        # Create test data
        patient1 = self.create_test_patient(vorname="Anna", nachname="Müller", anrede="Frau", geschlecht="weiblich")
        patient2 = self.create_test_patient(vorname="Max", nachname="Schmidt", anrede="Herr", geschlecht="männlich")
        
        search1_response = requests.post(f"{BASE_URL}/platzsuchen", json={"patient_id": patient1['id']})
        search2_response = requests.post(f"{BASE_URL}/platzsuchen", json={"patient_id": patient2['id']})
        
        search1 = search1_response.json()
        search2 = search2_response.json()
        
        # Get list
        response = requests.get(f"{BASE_URL}/platzsuchen")
        assert response.status_code == 200
        
        data = response.json()
        assert 'data' in data
        searches = data['data']
        assert len(searches) >= 2
        
        # Verify our searches are in the list
        search_ids = [s['id'] for s in searches]
        assert search1['id'] in search_ids
        assert search2['id'] in search_ids
        
        # Verify pagination metadata
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 2
        
        # Cleanup
        requests.delete(f"{BASE_URL}/platzsuchen/{search1['id']}")
        requests.delete(f"{BASE_URL}/platzsuchen/{search2['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient1['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient2['id']}")

    def test_get_platzsuchen_with_pagination(self):
        """Test platzsuche pagination parameters."""
        # Create multiple searches
        created_patients = []
        created_searches = []
        
        for i in range(5):
            patient = self.create_test_patient(
                vorname=f"Patient{i}",
                email=f"patient{i}@example.com",
                anrede="Herr" if i % 2 == 0 else "Frau",
                geschlecht="männlich" if i % 2 == 0 else "weiblich"
            )
            created_patients.append(patient)
            
            search_response = requests.post(
                f"{BASE_URL}/platzsuchen",
                json={"patient_id": patient['id']}
            )
            created_searches.append(search_response.json())
        
        # Test page 1 with limit 2
        response = requests.get(f"{BASE_URL}/platzsuchen?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        assert data['total'] >= 5
        
        # Test page 2 with limit 2
        response = requests.get(f"{BASE_URL}/platzsuchen?page=2&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 2
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        
        # Cleanup
        for search in created_searches:
            requests.delete(f"{BASE_URL}/platzsuchen/{search['id']}")
        for patient in created_patients:
            requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_get_platzsuchen_filtered_by_status(self):
        """Test filtering platzsuche by status with pagination."""
        # Create searches with different statuses
        patient = self.create_test_patient()
        
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        search = search_response.json()
        
        # Update one to pausiert
        requests.put(
            f"{BASE_URL}/platzsuchen/{search['id']}",
            json={"status": "pausiert"}
        )
        
        # Filter by status
        response = requests.get(f"{BASE_URL}/platzsuchen?status=pausiert")
        assert response.status_code == 200
        
        data = response.json()
        searches = data['data']
        
        # Check that all returned searches have correct status
        for s in searches:
            assert s['status'] == "pausiert"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/platzsuchen/{search['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_kontaktanfrage(self):
        """Test requesting additional contacts for a search."""
        # Create search
        patient = self.create_test_patient()
        search_response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
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
        requests.delete(f"{BASE_URL}/platzsuchen/{search['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    # Therapeuten zur Auswahl (Therapist Selection) Tests

    def test_get_therapeuten_zur_auswahl(self):
        """Test getting therapists for selection with PLZ filter."""
        # Create therapists with different PLZ
        therapist1 = self.create_test_therapist(
            plz="52064",
            potenziell_verfuegbar=True,
            ueber_curavani_informiert=True,
            anrede="Frau",
            geschlecht="weiblich"
        )
        therapist2 = self.create_test_therapist(
            plz="52062",
            potenziell_verfuegbar=True,
            ueber_curavani_informiert=False,
            anrede="Herr",
            geschlecht="männlich"
        )
        therapist3 = self.create_test_therapist(
            plz="10115",  # Different PLZ prefix
            potenziell_verfuegbar=True
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
        
        # Verify sorting (informed and available first)
        if len(therapists) >= 2:
            # First should be available AND informed
            first_therapist = next((t for t in therapists if t['id'] == therapist1['id']), None)
            assert first_therapist is not None
            therapist_index = therapists.index(first_therapist)
            assert therapist_index < len(therapists) - 1  # Should not be last
        
        # Cleanup
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist1['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist2['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist3['id']}")

    def test_invalid_plz_prefix(self):
        """Test invalid PLZ prefix returns error."""
        # Test with invalid PLZ prefix
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=ABC")
        assert response.status_code == 400
        assert "Invalid PLZ prefix" in response.json()['message']
        
        # Test with wrong length
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=5")
        assert response.status_code == 400
        assert "Must be exactly 2 digits" in response.json()['message']

    # Therapeutenanfrage (Therapist Inquiry) Tests

    def test_create_therapeutenanfrage(self):
        """Test creating an anfrage for a manually selected therapist."""
        # Create test data
        therapist = self.create_test_therapist(plz="52064", anrede="Frau", geschlecht="weiblich")
        patient1 = self.create_test_patient(plz="52062", anrede="Herr", geschlecht="männlich")
        patient2 = self.create_test_patient(plz="52068", anrede="Frau", geschlecht="divers")
        
        # Create searches for patients
        search1 = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient1['id']}
        ).json()
        search2 = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient2['id']}
        ).json()
        
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
            assert anfrage['anfragegroesse'] >= 1  # At least 1 patient
            assert 'anfrage_id' in anfrage
            
            # Cleanup anfrage
            # Note: No delete endpoint for anfragen in the current implementation
        
        # Cleanup
        requests.delete(f"{BASE_URL}/platzsuchen/{search1['id']}")
        requests.delete(f"{BASE_URL}/platzsuchen/{search2['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient1['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient2['id']}")

    def test_get_therapeutenanfragen_list_empty(self):
        """Test getting empty therapeutenanfrage list with pagination."""
        response = requests.get(f"{BASE_URL}/therapeutenanfragen")
        assert response.status_code == 200
        
        # Expecting paginated structure
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
        # Test pagination parameters
        response = requests.get(f"{BASE_URL}/therapeutenanfragen?page=1&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 5
        assert len(data['data']) <= 5
        
        # Test page 2
        response = requests.get(f"{BASE_URL}/therapeutenanfragen?page=2&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 2
        assert data['limit'] == 5

    def test_get_therapeutenanfragen_filtered(self):
        """Test filtering therapeutenanfragen with pagination."""
        # Test various filters
        response = requests.get(f"{BASE_URL}/therapeutenanfragen?versand_status=ungesendet")
        assert response.status_code == 200
        
        data = response.json()
        assert 'data' in data
        # All returned anfragen should be unsent
        for anfrage in data['data']:
            assert anfrage['gesendet_datum'] is None
        
        # Test size filter
        response = requests.get(f"{BASE_URL}/therapeutenanfragen?min_size=3&max_size=5")
        assert response.status_code == 200
        
        data = response.json()
        # All returned anfragen should have size between 3 and 5
        for anfrage in data['data']:
            assert 3 <= anfrage['anfragegroesse'] <= 5

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

    def test_pagination_limits(self):
        """Test pagination limit constraints."""
        # Test max limit (should be capped at 100)
        response = requests.get(f"{BASE_URL}/platzsuchen?limit=200")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 100  # Should be capped at max limit
        
        # Test zero limit (should be set to 1)
        response = requests.get(f"{BASE_URL}/therapeutenanfragen?limit=0")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1  # Should be set to minimum
        
        # Test negative page (should be set to 1)
        response = requests.get(f"{BASE_URL}/platzsuchen?page=-1")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1  # Should be set to minimum

    def test_duplicate_platzsuche_error(self):
        """Test that creating duplicate active search fails."""
        # Create patient and first search
        patient = self.create_test_patient()
        search1 = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        ).json()
        
        # Try to create another active search for same patient
        response = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        )
        assert response.status_code == 400
        assert "already has an active search" in response.json()['message']
        
        # Cleanup
        requests.delete(f"{BASE_URL}/platzsuchen/{search1['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_update_platzsuche_exclusions(self):
        """Test updating therapist exclusion list."""
        # Create search
        patient = self.create_test_patient()
        search = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient['id']}
        ).json()
        
        # Update exclusions
        response = requests.put(
            f"{BASE_URL}/platzsuchen/{search['id']}",
            json={
                "ausgeschlossene_therapeuten": [101, 102, 103]
            }
        )
        assert response.status_code == 200
        
        # Verify exclusions
        response = requests.get(f"{BASE_URL}/platzsuchen/{search['id']}")
        updated_search = response.json()
        assert updated_search['ausgeschlossene_therapeuten'] == [101, 102, 103]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/platzsuchen/{search['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient['id']}")

    def test_matching_with_diverse_gender_patients(self):
        """Test matching service with patients of diverse and keine_Angabe gender."""
        # Create diverse patients
        patient_diverse = self.create_test_patient(
            anrede="Herr",
            geschlecht="divers",
            vorname="Alex",
            nachname="Diverse"
        )
        
        patient_keine_angabe = self.create_test_patient(
            anrede="Frau",
            geschlecht="keine_Angabe",
            vorname="Chris",
            nachname="NoGender"
        )
        
        # Create searches
        search1 = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient_diverse['id']}
        ).json()
        
        search2 = requests.post(
            f"{BASE_URL}/platzsuchen",
            json={"patient_id": patient_keine_angabe['id']}
        ).json()
        
        # Verify searches created successfully
        assert search1['patient_id'] == patient_diverse['id']
        assert search2['patient_id'] == patient_keine_angabe['id']
        
        # Cleanup
        requests.delete(f"{BASE_URL}/platzsuchen/{search1['id']}")
        requests.delete(f"{BASE_URL}/platzsuchen/{search2['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_diverse['id']}")
        requests.delete(f"{PATIENT_BASE_URL}/patients/{patient_keine_angabe['id']}")

    def test_matching_with_diverse_gender_therapists(self):
        """Test therapist selection with diverse gender therapists."""
        # Create therapists with different genders
        therapist_diverse = self.create_test_therapist(
            anrede="Herr",
            geschlecht="divers",
            vorname="Alex",
            nachname="DiverseTherapist",
            plz="52064"
        )
        
        therapist_keine_angabe = self.create_test_therapist(
            anrede="Frau",
            geschlecht="keine_Angabe",
            vorname="Chris",
            nachname="NoGenderTherapist",
            plz="52065"
        )
        
        # Get therapists for selection
        response = requests.get(f"{BASE_URL}/therapeuten-zur-auswahl?plz_prefix=52")
        assert response.status_code == 200
        
        data = response.json()
        therapists = data['data']
        
        # Verify diverse therapists are included
        therapist_ids = [t['id'] for t in therapists]
        assert therapist_diverse['id'] in therapist_ids
        assert therapist_keine_angabe['id'] in therapist_ids
        
        # Cleanup
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_diverse['id']}")
        requests.delete(f"{THERAPIST_BASE_URL}/therapists/{therapist_keine_angabe['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
