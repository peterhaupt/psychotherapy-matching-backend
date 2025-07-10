"""Updated integration tests for Therapist Service API with search-based isolation."""
import requests
import uuid
from datetime import date, timedelta


# Base URL for the therapist service
BASE_URL = "http://localhost:8002"


class TestTherapistServiceAPI:
    """Integration tests for the Therapist Service API using search-based test isolation."""
    
    def __init__(self):
        """Initialize test class with unique test identifier."""
        # Generate unique test session ID to avoid conflicts between test runs
        self.test_session_id = str(uuid.uuid4())[:8]
        self.test_prefix = f"TestTherapist_{self.test_session_id}"
        print(f"Test session ID: {self.test_session_id}")
    
    def create_test_therapist(self, **kwargs):
        """Create a test therapist with unique searchable name and provided attributes.
        
        Args:
            **kwargs: Therapist attributes to override defaults
            
        Returns:
            dict: Created therapist data from API response
        """
        # Generate unique names for this test therapist
        unique_id = str(uuid.uuid4())[:4]
        
        # Default test therapist data with unique searchable names
        default_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich", 
            "vorname": f"{self.test_prefix}_{unique_id}",
            "nachname": f"TestNachname_{unique_id}",
            "titel": "Dr. med.",
            "strasse": "Teststraße 123",
            "plz": "52062",
            "ort": "Aachen",
            "telefon": "+49 241 12345678",
            "email": f"test_{unique_id}@example.com",
            "kassensitz": True,
            "psychotherapieverfahren": "Verhaltenstherapie",
            "potenziell_verfuegbar": True,
            "ueber_curavani_informiert": False,
            "status": "aktiv"
        }
        
        # Override with provided kwargs
        default_data.update(kwargs)
        
        # Ensure vorname includes our test prefix for searchability
        if not default_data["vorname"].startswith(self.test_prefix):
            default_data["vorname"] = f"{self.test_prefix}_{default_data['vorname']}"
        
        # Create therapist via API
        response = requests.post(f"{BASE_URL}/api/therapists", json=default_data)
        assert response.status_code == 201, f"Failed to create therapist: {response.text}"
        
        return response.json()
    
    def get_test_therapists(self, additional_filters=None):
        """Get all test therapists created in this session using search.
        
        Args:
            additional_filters: Dict of additional query parameters to include
            
        Returns:
            list: List of test therapists matching search criteria
        """
        # Base search for our test therapists
        params = {"search": self.test_prefix}
        
        # Add any additional filters
        if additional_filters:
            params.update(additional_filters)
        
        response = requests.get(f"{BASE_URL}/api/therapists", params=params)
        assert response.status_code == 200, f"Failed to search therapists: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Expected paginated response"
        assert 'data' in data, "Expected 'data' field in response"
        
        return data['data']
    
    def cleanup_test_therapists(self):
        """Clean up test therapists created in this session."""
        try:
            test_therapists = self.get_test_therapists()
            for therapist in test_therapists:
                requests.delete(f"{BASE_URL}/api/therapists/{therapist['id']}")
                print(f"Cleaned up test therapist {therapist['id']}")
        except Exception as e:
            print(f"Warning: Could not clean up test therapists: {e}")
    
    def test_get_therapists_list_with_data(self):
        """Test getting therapist list with data and pagination."""
        # Create test therapists with unique searchable names
        therapist1 = self.create_test_therapist(
            vorname="Anna", 
            nachname="Schmidt", 
            anrede="Frau", 
            geschlecht="weiblich"
        )
        therapist2 = self.create_test_therapist(
            vorname="Peter", 
            nachname="Meyer", 
            anrede="Herr", 
            geschlecht="männlich"
        )
        
        # Search for our test therapists specifically
        therapists = self.get_test_therapists()
        
        # Verify we have at least our 2 test therapists
        assert len(therapists) >= 2, f"Expected at least 2 therapists, got {len(therapists)}"
        
        # Verify our therapists are in the search results
        therapist_ids = [t['id'] for t in therapists]
        assert therapist1['id'] in therapist_ids, f"Therapist1 {therapist1['id']} not found in search results"
        assert therapist2['id'] in therapist_ids, f"Therapist2 {therapist2['id']} not found in search results"
        
        # Verify data structure
        for therapist in therapists:
            assert 'id' in therapist
            assert 'vorname' in therapist
            assert 'nachname' in therapist
            assert 'anrede' in therapist
            assert 'geschlecht' in therapist
            # Verify it's actually our test data
            assert therapist['vorname'].startswith(self.test_prefix)
        
        print("✓ test_get_therapists_list_with_data passed")
    
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
        
        # Search for active test therapists only
        active_therapists = self.get_test_therapists({"status": "aktiv"})
        
        # Check that all returned therapists have the correct status
        for therapist in active_therapists:
            assert therapist['status'] == "aktiv", f"Expected aktiv status, got {therapist['status']}"
        
        # Verify therapist1 is in results but therapist2 is not
        active_ids = [t['id'] for t in active_therapists]
        assert therapist1['id'] in active_ids, f"Active therapist {therapist1['id']} not in filtered results"
        assert therapist2['id'] not in active_ids, f"Blocked therapist {therapist2['id']} should not be in active results"
        
        # Test blocked filter as well
        blocked_therapists = self.get_test_therapists({"status": "gesperrt"})
        blocked_ids = [t['id'] for t in blocked_therapists]
        assert therapist2['id'] in blocked_ids, f"Blocked therapist {therapist2['id']} not in blocked results"
        assert therapist1['id'] not in blocked_ids, f"Active therapist {therapist1['id']} should not be in blocked results"
        
        print("✓ test_get_therapists_list_filtered_by_status passed")
    
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
        
        # Search for available test therapists only
        available_therapists = self.get_test_therapists({"potenziell_verfuegbar": "true"})
        
        # Check that all returned therapists are available
        for therapist in available_therapists:
            assert therapist['potenziell_verfuegbar'] is True, f"Expected available therapist, got {therapist['potenziell_verfuegbar']}"
        
        # Verify therapist1 is in results
        available_ids = [t['id'] for t in available_therapists]
        assert therapist1['id'] in available_ids, f"Available therapist {therapist1['id']} not in filtered results"
        
        # Test unavailable filter
        unavailable_therapists = self.get_test_therapists({"potenziell_verfuegbar": "false"})
        unavailable_ids = [t['id'] for t in unavailable_therapists]
        assert therapist2['id'] in unavailable_ids, f"Unavailable therapist {therapist2['id']} not in unavailable results"
        
        print("✓ test_get_therapists_filtered_by_availability passed")
    
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
        
        # Get all test therapists
        all_test_therapists = self.get_test_therapists()
        
        # Both should be returned (filtering is done by matching service)
        therapist_ids = [t['id'] for t in all_test_therapists]
        assert therapist1['id'] in therapist_ids, f"Cooling period therapist {therapist1['id']} not found"
        assert therapist2['id'] in therapist_ids, f"Available therapist {therapist2['id']} not found"
        
        # Verify the cooling period dates are set correctly
        therapist1_data = next(t for t in all_test_therapists if t['id'] == therapist1['id'])
        therapist2_data = next(t for t in all_test_therapists if t['id'] == therapist2['id'])
        
        # Verify cooling period is in the future for therapist1
        cooling_date = therapist1_data.get('naechster_kontakt_moeglich')
        assert cooling_date is not None, "Cooling period therapist should have next contact date"
        
        # Verify therapist2 is available today
        available_date = therapist2_data.get('naechster_kontakt_moeglich')
        assert available_date is not None, "Available therapist should have next contact date"
        
        print("✓ test_cooling_period_filtering passed")
    
    def test_search_functionality(self):
        """Test the search functionality specifically."""
        # Create therapists with different searchable attributes
        therapist1 = self.create_test_therapist(
            vorname="Unique_Search_Name",
            nachname="Schmidt",
            psychotherapieverfahren="Verhaltenstherapie"
        )
        therapist2 = self.create_test_therapist(
            vorname="Different",
            nachname="Unique_Search_Lastname", 
            psychotherapieverfahren="tiefenpsychologisch_fundierte_Psychotherapie"
        )
        
        # Test search by first name
        response = requests.get(f"{BASE_URL}/api/therapists", params={"search": "Unique_Search_Name"})
        assert response.status_code == 200
        results = response.json()['data']
        result_ids = [t['id'] for t in results]
        assert therapist1['id'] in result_ids, "Search by first name failed"
        
        # Test search by last name
        response = requests.get(f"{BASE_URL}/api/therapists", params={"search": "Unique_Search_Lastname"})
        assert response.status_code == 200
        results = response.json()['data']
        result_ids = [t['id'] for t in results]
        assert therapist2['id'] in result_ids, "Search by last name failed"
        
        # Test search by therapy method
        response = requests.get(f"{BASE_URL}/api/therapists", params={"search": "verhaltens"})
        assert response.status_code == 200
        results = response.json()['data']
        # Should find therapists with Verhaltenstherapie (case-insensitive partial match)
        found_verhaltens = any(t.get('psychotherapieverfahren') == 'Verhaltenstherapie' for t in results)
        assert found_verhaltens, "Search by therapy method failed"
        
        print("✓ test_search_functionality passed")
    
    def test_therapist_crud_operations(self):
        """Test Create, Read, Update, Delete operations."""
        # CREATE
        therapist_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": f"{self.test_prefix}_CRUD_Test",
            "nachname": "TestCRUD",
            "psychotherapieverfahren": "egal"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/therapists", json=therapist_data)
        assert create_response.status_code == 201, f"Create failed: {create_response.text}"
        created_therapist = create_response.json()
        therapist_id = created_therapist['id']
        
        # READ
        read_response = requests.get(f"{BASE_URL}/api/therapists/{therapist_id}")
        assert read_response.status_code == 200, f"Read failed: {read_response.text}"
        read_therapist = read_response.json()
        assert read_therapist['vorname'] == therapist_data['vorname']
        assert read_therapist['nachname'] == therapist_data['nachname']
        
        # UPDATE
        update_data = {
            "psychotherapieverfahren": "Verhaltenstherapie",
            "email": "updated@example.com"
        }
        update_response = requests.put(f"{BASE_URL}/api/therapists/{therapist_id}", json=update_data)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Verify update
        updated_response = requests.get(f"{BASE_URL}/api/therapists/{therapist_id}")
        updated_therapist = updated_response.json()
        assert updated_therapist['psychotherapieverfahren'] == "Verhaltenstherapie"
        assert updated_therapist['email'] == "updated@example.com"
        
        # DELETE
        delete_response = requests.delete(f"{BASE_URL}/api/therapists/{therapist_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/therapists/{therapist_id}")
        assert verify_response.status_code == 404, "Therapist should be deleted"
        
        print("✓ test_therapist_crud_operations passed")
    
    def run_all_tests(self):
        """Run all tests and clean up afterwards."""
        print(f"Starting Therapist Service Integration Tests (Session: {self.test_session_id})")
        print("=" * 70)
        
        try:
            # Run all test methods
            self.test_get_therapists_list_with_data()
            self.test_get_therapists_list_filtered_by_status()
            self.test_get_therapists_filtered_by_availability()
            self.test_cooling_period_filtering()
            self.test_search_functionality()
            self.test_therapist_crud_operations()
            
            print("=" * 70)
            print("🎉 All tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            raise
        finally:
            # Clean up test data
            print("\nCleaning up test data...")
            self.cleanup_test_therapists()
            print("✅ Cleanup completed")


if __name__ == "__main__":
    # Run the tests
    test_runner = TestTherapistServiceAPI()
    test_runner.run_all_tests()
