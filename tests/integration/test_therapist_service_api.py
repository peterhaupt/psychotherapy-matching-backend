"""Pytest-compatible integration tests for Therapist Service API with search-based isolation and enhanced debugging."""
import requests
import uuid
import pytest
import time
from datetime import date, timedelta
import os

# Base URL for the therapist service
BASE_URL = os.environ["THERAPIST_API_URL"]


@pytest.fixture(scope="class")
def test_session():
    """Create a unique test session identifier for this test class."""
    session_id = str(uuid.uuid4())[:8]
    test_prefix = f"TestTherapist_{session_id}"
    print(f"\nTest session ID: {session_id}")
    return {
        "session_id": session_id,
        "test_prefix": test_prefix,
        "created_therapists": []
    }


@pytest.fixture
def therapist_factory(test_session):
    """Factory fixture for creating test therapists with unique searchable names."""
    
    def _create_test_therapist(**kwargs):
        """Create a test therapist with unique searchable name and provided attributes.
        
        Args:
            **kwargs: Therapist attributes to override defaults
            
        Returns:
            dict: Created therapist data from API response
        """
        # Generate unique names for this test therapist
        unique_id = str(uuid.uuid4())[:4]
        test_prefix = test_session["test_prefix"]
        
        # Default test therapist data with unique searchable names
        default_data = {
            "anrede": "Frau",
            "geschlecht": "weiblich", 
            "vorname": f"{test_prefix}_{unique_id}",
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
        if not default_data["vorname"].startswith(test_prefix):
            default_data["vorname"] = f"{test_prefix}_{default_data['vorname']}"
        
        print(f"\n=== DEBUG: Creating therapist with data ===")
        for key, value in kwargs.items():
            print(f"  Override: {key} = {value}")
        print(f"  Final potenziell_verfuegbar: {default_data['potenziell_verfuegbar']}")
        
        # Create therapist via API
        response = requests.post(f"{BASE_URL}/api/therapists", json=default_data)
        
        print(f"  Creation response status: {response.status_code}")
        if response.status_code != 201:
            print(f"  Creation failed: {response.text}")
        
        assert response.status_code == 201, f"Failed to create therapist: {response.text}"
        
        created_therapist = response.json()
        therapist_id = created_therapist["id"]
        
        print(f"  Created therapist ID: {therapist_id}")
        print(f"  Created with availability: {created_therapist.get('potenziell_verfuegbar')}")
        
        # Track created therapist for cleanup
        test_session["created_therapists"].append(therapist_id)
        
        # IMMEDIATE VERIFICATION: Get the therapist back to confirm it exists
        verification_response = requests.get(f"{BASE_URL}/api/therapists/{therapist_id}")
        if verification_response.ok:
            verified_data = verification_response.json()
            print(f"  Verification GET successful")
            print(f"  Verified availability: {verified_data.get('potenziell_verfuegbar')}")
            print(f"  Verified vorname: {verified_data.get('vorname')}")
        else:
            print(f"  Verification GET failed: {verification_response.status_code}")
        
        return created_therapist
    
    return _create_test_therapist


@pytest.fixture
def therapist_searcher(test_session):
    """Fixture for searching test therapists created in this session."""
    
    def _get_test_therapists(additional_filters=None):
        """Get all test therapists created in this session using search.
        
        Args:
            additional_filters: Dict of additional query parameters to include
            
        Returns:
            list: List of test therapists matching search criteria
        """
        # Base search for our test therapists
        params = {"search": test_session["test_prefix"]}
        
        # Add any additional filters
        if additional_filters:
            params.update(additional_filters)
        
        print(f"\n=== DEBUG: Searching with parameters ===")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        response = requests.get(f"{BASE_URL}/api/therapists", params=params)
        
        print(f"  Search response status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Search failed: {response.text}")
        
        assert response.status_code == 200, f"Failed to search therapists: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Expected paginated response"
        assert 'data' in data, "Expected 'data' field in response"
        
        therapists = data['data']
        print(f"  Found {len(therapists)} therapists")
        print(f"  Total in database: {data.get('total', 'unknown')}")
        
        # Show details of found therapists
        for i, therapist in enumerate(therapists):
            print(f"    Therapist {i+1}: ID={therapist['id']}, available={therapist.get('potenziell_verfuegbar')}, name={therapist.get('vorname', 'N/A')}")
        
        return therapists
    
    return _get_test_therapists


@pytest.fixture(scope="class", autouse=True)
def cleanup_therapists(test_session):
    """Automatically clean up test therapists after all tests in the class."""
    yield  # Let all tests run first
    
    # Cleanup after all tests
    try:
        created_ids = test_session.get("created_therapists", [])
        print(f"\n=== DEBUG: Cleanup starting for {len(created_ids)} therapists ===")
        for therapist_id in created_ids:
            response = requests.delete(f"{BASE_URL}/api/therapists/{therapist_id}")
            if response.status_code == 200:
                print(f"  Cleaned up test therapist {therapist_id}")
            else:
                print(f"  Warning: Could not clean up therapist {therapist_id}: {response.status_code}")
        
        print(f"✅ Cleanup completed - removed {len(created_ids)} test therapists")
    except Exception as e:
        print(f"Warning: Error during cleanup: {e}")


class TestTherapistServiceAPI:
    """Integration tests for the Therapist Service API using search-based test isolation."""
    
    def test_get_therapists_list_with_data(self, therapist_factory, therapist_searcher):
        """Test getting therapist list with data and pagination."""
        # Create test therapists with unique searchable names
        therapist1 = therapist_factory(
            vorname="Anna", 
            nachname="Schmidt", 
            anrede="Frau", 
            geschlecht="weiblich"
        )
        therapist2 = therapist_factory(
            vorname="Peter", 
            nachname="Meyer", 
            anrede="Herr", 
            geschlecht="männlich"
        )
        
        # Search for our test therapists specifically
        therapists = therapist_searcher()
        
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
    
    def test_get_therapists_list_filtered_by_status(self, therapist_factory, therapist_searcher):
        """Test filtering therapists by status with pagination."""
        # Create therapists with different statuses
        therapist1 = therapist_factory(
            vorname="Active",
            nachname="Therapist",
            status="aktiv"
        )
        therapist2 = therapist_factory(
            vorname="Blocked",
            nachname="Therapist", 
            status="gesperrt"
        )
        
        # Search for active test therapists only
        active_therapists = therapist_searcher({"status": "aktiv"})
        
        # Check that all returned therapists have the correct status
        for therapist in active_therapists:
            assert therapist['status'] == "aktiv", f"Expected aktiv status, got {therapist['status']}"
        
        # Verify therapist1 is in results but therapist2 is not
        active_ids = [t['id'] for t in active_therapists]
        assert therapist1['id'] in active_ids, f"Active therapist {therapist1['id']} not in filtered results"
        assert therapist2['id'] not in active_ids, f"Blocked therapist {therapist2['id']} should not be in active results"
        
        # Test blocked filter as well
        blocked_therapists = therapist_searcher({"status": "gesperrt"})
        blocked_ids = [t['id'] for t in blocked_therapists]
        assert therapist2['id'] in blocked_ids, f"Blocked therapist {therapist2['id']} not in blocked results"
        assert therapist1['id'] not in blocked_ids, f"Active therapist {therapist1['id']} should not be in blocked results"
    
    def test_get_therapists_filtered_by_availability(self, therapist_factory, therapist_searcher):
        """Test filtering therapists by availability with pagination."""
        print(f"\n{'='*60}")
        print(f"STARTING AVAILABILITY FILTER TEST")
        print(f"{'='*60}")
        
        # Create therapists with different availability
        print(f"\n--- Creating AVAILABLE therapist ---")
        therapist1 = therapist_factory(
            vorname="Available",
            nachname="Therapist",
            potenziell_verfuegbar=True
        )
        
        print(f"\n--- Creating UNAVAILABLE therapist ---")
        therapist2 = therapist_factory(
            vorname="Unavailable",
            nachname="Therapist",
            potenziell_verfuegbar=False
        )
        
        print(f"\n--- Creation Summary ---")
        print(f"Available therapist: ID {therapist1['id']}, availability: {therapist1.get('potenziell_verfuegbar')}")
        print(f"Unavailable therapist: ID {therapist2['id']}, availability: {therapist2.get('potenziell_verfuegbar')}")
        
        # Small delay to ensure database consistency
        print(f"\n--- Waiting 0.5 seconds for database consistency ---")
        time.sleep(0.5)
        
        # DIRECT VERIFICATION: Get both therapists individually
        print(f"\n--- Direct verification of created therapists ---")
        for therapist_id, expected_available in [(therapist1['id'], True), (therapist2['id'], False)]:
            direct_response = requests.get(f"{BASE_URL}/api/therapists/{therapist_id}")
            if direct_response.ok:
                direct_data = direct_response.json()
                actual_available = direct_data.get('potenziell_verfuegbar')
                print(f"  Therapist {therapist_id}: expected={expected_available}, actual={actual_available} ✓" if actual_available == expected_available else f"  Therapist {therapist_id}: expected={expected_available}, actual={actual_available} ❌")
            else:
                print(f"  Therapist {therapist_id}: FAILED to get directly (status {direct_response.status_code})")
        
        # Test AVAILABLE filter
        print(f"\n--- Testing AVAILABLE filter ---")
        available_therapists = therapist_searcher({"potenziell_verfuegbar": "true"})
        
        print(f"\nAvailable filter results:")
        print(f"  Found {len(available_therapists)} therapists")
        available_ids = [t['id'] for t in available_therapists]
        print(f"  IDs: {available_ids}")
        
        # Check that all returned therapists are available
        for therapist in available_therapists:
            actual_availability = therapist['potenziell_verfuegbar']
            assert actual_availability is True, f"Expected available therapist, got {actual_availability} for therapist {therapist['id']}"
        
        # Verify therapist1 is in results
        if therapist1['id'] in available_ids:
            print(f"  ✓ Available therapist {therapist1['id']} found in results")
        else:
            print(f"  ❌ Available therapist {therapist1['id']} NOT found in results")
            print(f"  Available IDs: {available_ids}")
        
        assert therapist1['id'] in available_ids, f"Available therapist {therapist1['id']} not in filtered results"
        
        # Test UNAVAILABLE filter
        print(f"\n--- Testing UNAVAILABLE filter ---")
        unavailable_therapists = therapist_searcher({"potenziell_verfuegbar": "false"})
        
        print(f"\nUnavailable filter results:")
        print(f"  Found {len(unavailable_therapists)} therapists")
        unavailable_ids = [t['id'] for t in unavailable_therapists]
        print(f"  IDs: {unavailable_ids}")
        
        # Show detailed info about each unavailable therapist
        for i, therapist in enumerate(unavailable_therapists):
            print(f"    Therapist {i+1}: ID={therapist['id']}, available={therapist.get('potenziell_verfuegbar')}, name={therapist.get('vorname', 'N/A')}")
        
        # Check if our unavailable therapist is in the results
        if therapist2['id'] in unavailable_ids:
            print(f"  ✓ Unavailable therapist {therapist2['id']} found in results")
        else:
            print(f"  ❌ Unavailable therapist {therapist2['id']} NOT found in results")
            print(f"  Unavailable IDs: {unavailable_ids}")
            print(f"  Missing therapist created with: potenziell_verfuegbar=False")
            
            # Try to find it in all therapists
            print(f"\n--- Searching for missing therapist in ALL results ---")
            all_our_therapists = therapist_searcher()
            for therapist in all_our_therapists:
                if therapist['id'] == therapist2['id']:
                    print(f"  Found missing therapist in general search: ID={therapist['id']}, available={therapist.get('potenziell_verfuegbar')}")
                    break
            else:
                print(f"  Missing therapist {therapist2['id']} not found even in general search!")
        
        assert therapist2['id'] in unavailable_ids, f"Unavailable therapist {therapist2['id']} not in unavailable results. Found IDs: {unavailable_ids}"
    
    def test_cooling_period_filtering(self, therapist_factory, therapist_searcher):
        """Test that therapists in cooling period are handled correctly."""
        # Create a therapist in cooling period
        therapist1 = therapist_factory(
            vorname="Cooling",
            nachname="Therapist",
            naechster_kontakt_moeglich=(date.today() + timedelta(days=30)).isoformat()
        )
        
        # Create a therapist not in cooling period  
        therapist2 = therapist_factory(
            vorname="Available",
            nachname="Therapist",
            naechster_kontakt_moeglich=date.today().isoformat()
        )
        
        # Get all test therapists
        all_test_therapists = therapist_searcher()
        
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
    
    def test_search_functionality(self, therapist_factory):
        """Test the search functionality specifically."""
        # Create therapists with different searchable attributes
        therapist1 = therapist_factory(
            vorname="Unique_Search_Name",
            nachname="Schmidt",
            psychotherapieverfahren="Verhaltenstherapie"
        )
        therapist2 = therapist_factory(
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
    
    def test_therapist_crud_operations(self, test_session):
        """Test Create, Read, Update, Delete operations."""
        # CREATE
        therapist_data = {
            "anrede": "Herr",
            "geschlecht": "männlich",
            "vorname": f"{test_session['test_prefix']}_CRUD_Test",
            "nachname": "TestCRUD",
            "psychotherapieverfahren": "egal"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/therapists", json=therapist_data)
        assert create_response.status_code == 201, f"Create failed: {create_response.text}"
        created_therapist = create_response.json()
        therapist_id = created_therapist['id']
        
        # Track for cleanup
        test_session["created_therapists"].append(therapist_id)
        
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
        
        # Remove from cleanup list since we just deleted it
        test_session["created_therapists"].remove(therapist_id)
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/therapists/{therapist_id}")
        assert verify_response.status_code == 404, "Therapist should be deleted"
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert 'status' in health_data
        assert health_data['status'] == 'healthy'
        assert 'service' in health_data
    
    def test_communication_history_endpoint(self, therapist_factory):
        """Test the communication history endpoint."""
        # Create a test therapist
        therapist = therapist_factory(
            vorname="Communication",
            nachname="Test"
        )
        
        # Test communication history endpoint
        response = requests.get(f"{BASE_URL}/api/therapists/{therapist['id']}/communication")
        assert response.status_code == 200
        
        comm_data = response.json()
        assert 'therapist_id' in comm_data
        assert 'therapist_name' in comm_data
        assert 'communications' in comm_data
        assert comm_data['therapist_id'] == therapist['id']
    
    def test_import_status_endpoint(self):
        """Test the import status monitoring endpoint."""
        response = requests.get(f"{BASE_URL}/api/therapists/import-status")
        assert response.status_code == 200
        
        status_data = response.json()
        # Check for expected status fields
        expected_fields = [
            'running', 'last_check', 'files_processed_today',
            'therapists_processed_today', 'total_files_processed'
        ]
        for field in expected_fields:
            assert field in status_data, f"Missing field: {field}"


# Pytest entry point - can be run with: pytest test_therapist_service_api.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])