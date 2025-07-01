"""Integration tests for Therapist Service API with pagination support."""
import pytest
import requests
import time
from datetime import date, timedelta

# Base URL for the Therapist Service
BASE_URL = "http://localhost:8002/api"


class TestTherapistServiceAPI:
    """Test class for Therapist Service API endpoints."""

    @classmethod
    def setup_class(cls):
        """Setup test class - wait for service to be ready."""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{BASE_URL}/therapists")
                if response.status_code == 200:
                    print("Therapist service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Therapist service did not start in time")

    def create_test_therapist(self, **kwargs):
        """Helper method to create a test therapist."""
        default_data = {
            "anrede": "Herr",  # Required field
            "geschlecht": "männlich",  # Required field
            "vorname": "Test",
            "nachname": "Therapeut",
            "email": "test.therapeut@example.com",
            "telefon": "+49 123 456789",
            "strasse": "Therapiestraße 1",
            "plz": "10178",
            "ort": "Berlin",
            "kassensitz": True,
            "status": "aktiv"
        }
        data = {**default_data, **kwargs}
        
        response = requests.post(f"{BASE_URL}/therapists", json=data)
        assert response.status_code == 201
        return response.json()

    def test_create_therapist(self):
        """Test creating a new therapist."""
        therapist_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "titel": "Dr.",
            "vorname": "Maria",
            "nachname": "Müller",
            "email": "dr.mueller@therapie.de",
            "telefon": "+49 30 12345678",
            "strasse": "Friedrichstraße 123",
            "plz": "10117",
            "ort": "Berlin",
            "kassensitz": True,
            "psychotherapieverfahren": ["Verhaltenstherapie", "Tiefenpsychologie"],
            "fremdsprachen": ["Englisch", "Französisch"],
            "potenziell_verfuegbar": True,
            "ueber_curavani_informiert": True,
            "status": "aktiv"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 201
        
        created_therapist = response.json()
        assert created_therapist["vorname"] == "Maria"
        assert created_therapist["nachname"] == "Müller"
        assert created_therapist["anrede"] == "Frau"
        assert created_therapist["geschlecht"] == "weiblich"
        assert created_therapist["status"] == "aktiv"
        assert created_therapist["ueber_curavani_informiert"] is True
        assert "id" in created_therapist
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{created_therapist['id']}")

    def test_create_therapist_with_different_gender(self):
        """Test creating a therapist with different gender options."""
        therapist_data = {
            "anrede": "Herr",
            "geschlecht": "divers",
            "vorname": "Alex",
            "nachname": "Schmidt",
            "email": "alex.schmidt@therapie.de"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 201
        
        created_therapist = response.json()
        assert created_therapist["geschlecht"] == "divers"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{created_therapist['id']}")

    def test_create_therapist_no_gender_specified(self):
        """Test creating a therapist with keine_Angabe gender."""
        therapist_data = {
            "anrede": "Frau",
            "geschlecht": "keine_Angabe",
            "vorname": "Chris",
            "nachname": "Weber"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 201
        
        created_therapist = response.json()
        assert created_therapist["geschlecht"] == "keine_Angabe"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{created_therapist['id']}")

    def test_create_therapist_invalid_anrede(self):
        """Test creating a therapist with invalid anrede."""
        therapist_data = {
            "anrede": "Prof.",  # Invalid
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Invalid"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 400
        assert "Invalid anrede 'Prof.'" in response.json()["message"]
        assert "Valid values: Herr, Frau" in response.json()["message"]

    def test_create_therapist_invalid_geschlecht(self):
        """Test creating a therapist with invalid geschlecht."""
        therapist_data = {
            "anrede": "Herr",
            "geschlecht": "m",  # Invalid (old format)
            "vorname": "Test",
            "nachname": "Invalid"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 400
        assert "Invalid geschlecht 'm'" in response.json()["message"]
        assert "Valid values: männlich, weiblich, divers, keine_Angabe" in response.json()["message"]

    def test_create_therapist_missing_required_fields(self):
        """Test creating a therapist without required fields."""
        # Missing anrede
        therapist_data = {
            "geschlecht": "männlich",
            "vorname": "Test",
            "nachname": "Therapist"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 400
        assert "anrede" in response.json()["message"].lower()
        
        # Missing geschlecht
        therapist_data = {
            "anrede": "Herr",
            "vorname": "Test",
            "nachname": "Therapist"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 400
        assert "geschlecht" in response.json()["message"].lower()

    def test_get_therapist_by_id(self):
        """Test retrieving a therapist by ID."""
        # Create a therapist first
        therapist = self.create_test_therapist(
            anrede="Herr",
            geschlecht="männlich",
            vorname="Thomas",
            nachname="Weber"
        )
        
        # Get the therapist
        response = requests.get(f"{BASE_URL}/therapists/{therapist['id']}")
        assert response.status_code == 200
        
        retrieved_therapist = response.json()
        assert retrieved_therapist["id"] == therapist["id"]
        assert retrieved_therapist["vorname"] == "Thomas"
        assert retrieved_therapist["nachname"] == "Weber"
        assert retrieved_therapist["anrede"] == "Herr"
        assert retrieved_therapist["geschlecht"] == "männlich"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist['id']}")

    def test_get_therapists_list_empty(self):
        """Test getting empty therapist list with pagination."""
        # Note: This assumes no therapists exist. In a real test environment,
        # you might want to clean up all therapists first.
        response = requests.get(f"{BASE_URL}/therapists")
        assert response.status_code == 200
        
        # Now expecting paginated structure
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['page'] == 1
        assert data['limit'] == 20  # Default limit
        assert data['total'] >= 0  # Could be 0 or more

    def test_get_therapists_list_with_data(self):
        """Test getting therapist list with data and pagination."""
        # Create test therapists
        therapist1 = self.create_test_therapist(vorname="Anna", nachname="Schmidt", anrede="Frau", geschlecht="weiblich")
        therapist2 = self.create_test_therapist(vorname="Peter", nachname="Meyer", anrede="Herr", geschlecht="männlich")
        
        response = requests.get(f"{BASE_URL}/therapists")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        therapists = data['data']
        assert len(therapists) >= 2
        
        # Verify our therapists are in the list
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids
        assert therapist2['id'] in therapist_ids
        
        # Verify pagination metadata
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] >= 2
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist1['id']}")
        requests.delete(f"{BASE_URL}/therapists/{therapist2['id']}")

    def test_get_therapists_with_pagination(self):
        """Test pagination parameters."""
        # Create multiple therapists
        created_therapists = []
        for i in range(5):
            therapist = self.create_test_therapist(
                vorname=f"Therapist{i}",
                nachname=f"Test{i}",
                email=f"therapist{i}@example.com",
                anrede="Herr" if i % 2 == 0 else "Frau",
                geschlecht="männlich" if i % 2 == 0 else "weiblich"
            )
            created_therapists.append(therapist)
        
        # Test page 1 with limit 2
        response = requests.get(f"{BASE_URL}/therapists?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        assert data['total'] >= 5
        
        # Test page 2 with limit 2
        response = requests.get(f"{BASE_URL}/therapists?page=2&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 2
        assert data['limit'] == 2
        assert len(data['data']) <= 2
        
        # Cleanup
        for therapist in created_therapists:
            requests.delete(f"{BASE_URL}/therapists/{therapist['id']}")

    def test_get_therapists_list_filtered_by_status(self):
        """Test filtering therapists by status with pagination."""
        # Create therapists with different statuses
        therapist1 = self.create_test_therapist(
            vorname="Active",
            nachname="Therapist",
            status="aktiv"
        )
        therapist2 = self.create_test_therapist(
            vorname="Blocked",
            nachname="Therapist",
            status="gesperrt"
        )
        
        # Filter by status
        response = requests.get(f"{BASE_URL}/therapists?status=aktiv")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'data' in data
        therapists = data['data']
        
        # Check that all returned therapists have the correct status
        for therapist in therapists:
            assert therapist['status'] == "aktiv"
        
        # Verify therapist1 is in results
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids
        assert therapist2['id'] not in therapist_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist1['id']}")
        requests.delete(f"{BASE_URL}/therapists/{therapist2['id']}")

    def test_get_therapists_filtered_by_availability(self):
        """Test filtering therapists by availability with pagination."""
        # Create therapists with different availability
        therapist1 = self.create_test_therapist(
            vorname="Available",
            nachname="Therapist",
            potenziell_verfuegbar=True
        )
        therapist2 = self.create_test_therapist(
            vorname="Unavailable",
            nachname="Therapist",
            potenziell_verfuegbar=False
        )
        
        # Filter by availability
        response = requests.get(f"{BASE_URL}/therapists?potenziell_verfuegbar=true")
        assert response.status_code == 200
        
        data = response.json()
        therapists = data['data']
        
        # Check that all returned therapists are available
        for therapist in therapists:
            assert therapist['potenziell_verfuegbar'] is True
        
        # Verify therapist1 is in results
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids
        assert therapist2['id'] not in therapist_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist1['id']}")
        requests.delete(f"{BASE_URL}/therapists/{therapist2['id']}")

    def test_update_therapist(self):
        """Test updating a therapist."""
        # Create a therapist
        therapist = self.create_test_therapist()
        
        # Update the therapist
        update_data = {
            "telefon": "+49 30 98765432",
            "potenziell_verfuegbar": True,
            "ueber_curavani_informiert": True,
            "naechster_kontakt_moeglich": (date.today() + timedelta(days=7)).isoformat(),
            "bevorzugte_diagnosen": ["F32", "F33", "F41"]
        }
        
        response = requests.put(
            f"{BASE_URL}/therapists/{therapist['id']}",
            json=update_data
        )
        assert response.status_code == 200
        
        updated_therapist = response.json()
        assert updated_therapist["telefon"] == "+49 30 98765432"
        assert updated_therapist["potenziell_verfuegbar"] is True
        assert updated_therapist["ueber_curavani_informiert"] is True
        assert updated_therapist["bevorzugte_diagnosen"] == ["F32", "F33", "F41"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist['id']}")

    def test_update_therapist_anrede_geschlecht(self):
        """Test updating therapist's anrede and geschlecht."""
        # Create a therapist
        therapist = self.create_test_therapist(anrede="Herr", geschlecht="männlich")
        
        # Update to different values
        update_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich"
        }
        
        response = requests.put(
            f"{BASE_URL}/therapists/{therapist['id']}",
            json=update_data
        )
        assert response.status_code == 200
        
        updated_therapist = response.json()
        assert updated_therapist["anrede"] == "Frau"
        assert updated_therapist["geschlecht"] == "weiblich"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist['id']}")

    def test_block_therapist(self):
        """Test blocking a therapist."""
        # Create a therapist
        therapist = self.create_test_therapist()
        
        # Block the therapist
        update_data = {
            "status": "gesperrt",
            "sperrgrund": "Keine Kapazität mehr",
            "sperrdatum": date.today().isoformat()
        }
        
        response = requests.put(
            f"{BASE_URL}/therapists/{therapist['id']}",
            json=update_data
        )
        assert response.status_code == 200
        
        blocked_therapist = response.json()
        assert blocked_therapist["status"] == "gesperrt"
        assert blocked_therapist["sperrgrund"] == "Keine Kapazität mehr"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist['id']}")

    def test_delete_therapist(self):
        """Test deleting a therapist."""
        # Create a therapist
        therapist = self.create_test_therapist()
        
        # Delete the therapist
        response = requests.delete(f"{BASE_URL}/therapists/{therapist['id']}")
        assert response.status_code == 200
        
        # Verify therapist is deleted
        response = requests.get(f"{BASE_URL}/therapists/{therapist['id']}")
        assert response.status_code == 404

    def test_therapist_not_found(self):
        """Test getting a non-existent therapist."""
        response = requests.get(f"{BASE_URL}/therapists/99999")
        assert response.status_code == 404
        assert response.json()["message"] == "Therapist not found"

    def test_invalid_status_filter(self):
        """Test filtering with invalid status returns empty result."""
        response = requests.get(f"{BASE_URL}/therapists?status=invalid_status")
        assert response.status_code == 200
        
        # Should return empty paginated result
        data = response.json()
        assert data['data'] == []
        assert data['page'] == 1
        assert data['limit'] == 20
        assert data['total'] == 0

    def test_create_therapist_with_preferences(self):
        """Test creating a therapist with inquiry preferences."""
        therapist_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": "Klaus",
            "nachname": "Fischer",
            "bevorzugte_diagnosen": ["F32", "F33", "F40", "F41"],
            "alter_min": 18,
            "alter_max": 65,
            "geschlechtspraeferenz": "Egal",
            "bevorzugt_gruppentherapie": False,
            "arbeitszeiten": {
                "montag": ["09:00-12:00", "14:00-18:00"],
                "mittwoch": ["09:00-17:00"],
                "freitag": ["09:00-14:00"]
            }
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 201
        
        created_therapist = response.json()
        assert created_therapist["bevorzugte_diagnosen"] == ["F32", "F33", "F40", "F41"]
        assert created_therapist["alter_min"] == 18
        assert created_therapist["alter_max"] == 65
        assert created_therapist["geschlechtspraeferenz"] == "Egal"
        assert "arbeitszeiten" in created_therapist
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{created_therapist['id']}")

    def test_therapist_communication_history(self):
        """Test getting therapist communication history."""
        # Create a therapist
        therapist = self.create_test_therapist()
        
        # Get communication history (should be empty initially)
        response = requests.get(f"{BASE_URL}/therapists/{therapist['id']}/communication")
        assert response.status_code == 200
        
        comm_data = response.json()
        assert comm_data['therapist_id'] == therapist['id']
        assert comm_data['therapist_name'] == f"{therapist['vorname']} {therapist['nachname']}"
        assert comm_data['total_emails'] >= 0
        assert comm_data['total_calls'] >= 0
        assert isinstance(comm_data['communications'], list)
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist['id']}")

    def test_pagination_limits(self):
        """Test pagination limit constraints."""
        # Test max limit (should be capped at 100)
        response = requests.get(f"{BASE_URL}/therapists?limit=200")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 100  # Should be capped at max limit
        
        # Test zero limit (should be set to 1)
        response = requests.get(f"{BASE_URL}/therapists?limit=0")
        assert response.status_code == 200
        
        data = response.json()
        assert data['limit'] == 1  # Should be set to minimum
        
        # Test negative page (should be set to 1)
        response = requests.get(f"{BASE_URL}/therapists?page=-1")
        assert response.status_code == 200
        
        data = response.json()
        assert data['page'] == 1  # Should be set to minimum

    def test_cooling_period_filtering(self):
        """Test that therapists in cooling period are handled correctly."""
        # Create a therapist in cooling period
        therapist1 = self.create_test_therapist(
            vorname="Cooling",
            nachname="Therapist",
            naechster_kontakt_moeglich=(date.today() + timedelta(days=30)).isoformat()
        )
        
        # Create a therapist not in cooling period
        therapist2 = self.create_test_therapist(
            vorname="Available",
            nachname="Therapist",
            naechster_kontakt_moeglich=date.today().isoformat()
        )
        
        # Get all therapists
        response = requests.get(f"{BASE_URL}/therapists")
        assert response.status_code == 200
        
        data = response.json()
        therapists = data['data']
        
        # Both should be returned (filtering is done by matching service)
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids
        assert therapist2['id'] in therapist_ids
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{therapist1['id']}")
        requests.delete(f"{BASE_URL}/therapists/{therapist2['id']}")

    def test_jsonb_field_defaults(self):
        """Test that JSONB fields return proper defaults instead of null."""
        # Create minimal therapist
        therapist_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich",
            "vorname": "Test",
            "nachname": "Minimal"
        }
        
        response = requests.post(f"{BASE_URL}/therapists", json=therapist_data)
        assert response.status_code == 201
        
        created_therapist = response.json()
        
        # Check JSONB array fields return empty arrays, not null
        assert created_therapist["fremdsprachen"] == []
        assert created_therapist["psychotherapieverfahren"] == []
        assert created_therapist["bevorzugte_diagnosen"] == []
        
        # Check JSONB object fields return empty objects, not null
        assert created_therapist["telefonische_erreichbarkeit"] == {}
        assert created_therapist["arbeitszeiten"] == {}
        
        # Cleanup
        requests.delete(f"{BASE_URL}/therapists/{created_therapist['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
