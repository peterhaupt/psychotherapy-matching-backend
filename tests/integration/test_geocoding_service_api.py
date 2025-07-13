"""Integration tests for Geocoding Service API."""
import pytest
import requests
import time
import os

# Base URL for the Geocoding Service
BASE_URL = os.environ["GEOCODING_API_URL"]
HEALTH_URL = os.environ["GEOCODING_HEALTH_URL"]


class TestGeocodingServiceAPI:
    """Test class for Geocoding Service API endpoints."""

    @classmethod
    def setup_class(cls):
        """Setup test class - wait for service to be ready."""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(HEALTH_URL)
                if response.status_code == 200:
                    print("Geocoding service is ready")
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("Geocoding service did not start in time")

    # Health Check Tests

    def test_health_check(self):
        """Test the health check endpoint."""
        response = requests.get(HEALTH_URL)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "geocoding" in data["service"].lower()

    # Geocoding Tests

    def test_geocode_valid_address(self):
        """Test geocoding a valid address."""
        response = requests.get(f"{BASE_URL}/geocode", params={
            "address": "Berlin, Germany"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "latitude" in data
        assert "longitude" in data
        assert "display_name" in data
        assert data["source"] == "nominatim"
        
        # Basic sanity checks for Berlin coordinates
        assert 52.0 < data["latitude"] < 53.0
        assert 13.0 < data["longitude"] < 14.0

    def test_geocode_german_city(self):
        """Test geocoding a German city."""
        response = requests.get(f"{BASE_URL}/geocode", params={
            "address": "München, Deutschland"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "latitude" in data
        assert "longitude" in data
        
        # Basic sanity checks for Munich coordinates
        assert 48.0 < data["latitude"] < 49.0
        assert 11.0 < data["longitude"] < 12.0

    def test_geocode_with_plz(self):
        """Test geocoding with German postal code."""
        response = requests.get(f"{BASE_URL}/geocode", params={
            "address": "52062 Aachen"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "latitude" in data
        assert "longitude" in data

    def test_geocode_missing_address(self):
        """Test geocoding without address parameter."""
        response = requests.get(f"{BASE_URL}/geocode")
        assert response.status_code == 400
        
        data = response.json()
        assert "address" in data["message"].lower()

    def test_geocode_invalid_address(self):
        """Test geocoding with invalid/non-existent address."""
        response = requests.get(f"{BASE_URL}/geocode", params={
            "address": "NonExistentCity12345XYZ"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert data["status"] == "error"
        assert "failed" in data["error"].lower()

    # Reverse Geocoding Tests

    def test_reverse_geocode_valid_coordinates(self):
        """Test reverse geocoding with valid coordinates."""
        # Berlin coordinates
        response = requests.get(f"{BASE_URL}/reverse-geocode", params={
            "lat": 52.5200,
            "lon": 13.4050
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "display_name" in data
        assert "address_components" in data
        assert data["latitude"] == 52.5200
        assert data["longitude"] == 13.4050
        assert data["source"] == "nominatim"

    def test_reverse_geocode_munich_coordinates(self):
        """Test reverse geocoding with Munich coordinates."""
        response = requests.get(f"{BASE_URL}/reverse-geocode", params={
            "lat": 48.1351,
            "lon": 11.5820
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "display_name" in data
        assert "münchen" in data["display_name"].lower() or "munich" in data["display_name"].lower()

    def test_reverse_geocode_missing_coordinates(self):
        """Test reverse geocoding without coordinates."""
        response = requests.get(f"{BASE_URL}/reverse-geocode")
        assert response.status_code == 400
        
        data = response.json()
        assert "latitude" in data["message"].lower() or "lat" in data["message"].lower()

    def test_reverse_geocode_missing_longitude(self):
        """Test reverse geocoding with missing longitude."""
        response = requests.get(f"{BASE_URL}/reverse-geocode", params={
            "lat": 52.5200
        })
        assert response.status_code == 400
        
        data = response.json()
        assert "longitude" in data["message"].lower() or "lon" in data["message"].lower()

    def test_reverse_geocode_invalid_coordinates(self):
        """Test reverse geocoding with invalid coordinates."""
        # Coordinates in the ocean
        response = requests.get(f"{BASE_URL}/reverse-geocode", params={
            "lat": 0.0,
            "lon": 0.0
        })
        # Note: This might return 200 with ocean/sea result or 400 depending on service
        # We just check it doesn't crash
        assert response.status_code in [200, 400]

    def test_reverse_geocode_out_of_range_coordinates(self):
        """Test reverse geocoding with out-of-range coordinates."""
        response = requests.get(f"{BASE_URL}/reverse-geocode", params={
            "lat": 200.0,  # Invalid latitude
            "lon": 13.4050
        })
        # Should handle gracefully
        assert response.status_code in [200, 400]

    # Distance Calculation Tests

    def test_calculate_distance_with_addresses(self):
        """Test distance calculation using addresses."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "Berlin",
            "destination": "Munich",
            "travel_mode": "car"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "distance_km" in data
        assert data["travel_mode"] == "car"
        assert data["status"] in ["success", "partial"]
        assert data["source"] in ["osrm", "haversine", "plz_centroids", "cache"]
        
        # Distance between Berlin and Munich should be around 500-600 km
        assert 400 < data["distance_km"] < 700

    def test_calculate_distance_with_coordinates(self):
        """Test distance calculation using coordinates."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin_lat": 52.5200,
            "origin_lon": 13.4050,
            "destination_lat": 48.1351,
            "destination_lon": 11.5820,
            "travel_mode": "car"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "distance_km" in data
        assert data["travel_mode"] == "car"
        assert data["status"] in ["success", "partial"]
        
        # Distance between Berlin and Munich coordinates
        assert 400 < data["distance_km"] < 700

    def test_calculate_distance_transit_mode(self):
        """Test distance calculation with transit mode."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "Berlin",
            "destination": "Hamburg",
            "travel_mode": "transit"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["travel_mode"] == "transit"
        assert "distance_km" in data

    def test_calculate_distance_no_cache(self):
        """Test distance calculation with cache bypass."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "Berlin",
            "destination": "Dresden",
            "no_cache": True
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "distance_km" in data

    def test_calculate_distance_with_plz_fallback(self):
        """Test distance calculation with PLZ fallback enabled."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "52062 Aachen",  # PLZ will be extracted
            "destination": "10115 Berlin",
            "use_plz_fallback": True
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "distance_km" in data
        # Should work with PLZ fallback
        assert data["status"] in ["success", "partial"]

    def test_calculate_distance_missing_origin(self):
        """Test distance calculation without origin."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "destination": "Munich"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert data["status"] == "error"
        assert "origin" in data["error"].lower()

    def test_calculate_distance_missing_destination(self):
        """Test distance calculation without destination."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "Berlin"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert data["status"] == "error"
        assert "destination" in data["error"].lower()

    def test_calculate_distance_invalid_travel_mode(self):
        """Test distance calculation with invalid travel mode."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "Berlin",
            "destination": "Munich",
            "travel_mode": "rocket"  # Invalid mode
        })
        assert response.status_code == 400
        
        data = response.json()
        # Flask-RESTful returns the help text for invalid choices
        assert "mode of transport" in data["message"].lower()

    def test_calculate_distance_invalid_addresses(self):
        """Test distance calculation with invalid addresses."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "NonExistentPlace12345",
            "destination": "AnotherFakePlace98765"
        })
        assert response.status_code == 200  # Should return gracefully
        
        data = response.json()
        # Might return 0 distance with error status
        assert data["status"] == "error" or data["distance_km"] == 0

    # PLZ Distance Calculation Tests

    def test_calculate_plz_distance_valid(self):
        """Test PLZ distance calculation with valid postal codes."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "52062",  # Aachen
            "destination_plz": "10115"  # Berlin
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["source"] == "plz_centroids"
        assert "distance_km" in data
        assert "origin_centroid" in data
        assert "destination_centroid" in data
        
        # Check centroid structure
        assert "latitude" in data["origin_centroid"]
        assert "longitude" in data["origin_centroid"]
        assert "latitude" in data["destination_centroid"]
        assert "longitude" in data["destination_centroid"]
        
        # Distance should be reasonable (Aachen to Berlin ~475km)
        assert 400 < data["distance_km"] < 600

    def test_calculate_plz_distance_same_plz(self):
        """Test PLZ distance calculation with same postal codes."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "52062",
            "destination_plz": "52062"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["distance_km"] == 0.0

    def test_calculate_plz_distance_nearby_plz(self):
        """Test PLZ distance calculation with nearby postal codes."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "52062",  # Aachen
            "destination_plz": "52064"  # Also Aachen area
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        # Should be a short distance (within same city)
        assert data["distance_km"] < 10

    def test_calculate_plz_distance_missing_origin(self):
        """Test PLZ distance calculation without origin PLZ."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "destination_plz": "10115"
        })
        assert response.status_code == 400
        
        data = response.json()
        # Flask-RESTful converts "origin_plz" to "origin plz" in error messages
        assert "origin plz" in data["message"].lower()

    def test_calculate_plz_distance_missing_destination(self):
        """Test PLZ distance calculation without destination PLZ."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "52062"
        })
        assert response.status_code == 400
        
        data = response.json()
        # Flask-RESTful converts "destination_plz" to "destination plz" in error messages
        assert "destination plz" in data["message"].lower()

    def test_calculate_plz_distance_invalid_format_origin(self):
        """Test PLZ distance calculation with invalid origin PLZ format."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "ABC12",  # Invalid format
            "destination_plz": "10115"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert data["status"] == "error"
        assert "invalid" in data["error"].lower()
        assert "abc12" in data["error"].lower()

    def test_calculate_plz_distance_invalid_format_destination(self):
        """Test PLZ distance calculation with invalid destination PLZ format."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "52062",
            "destination_plz": "1234"  # Too short
        })
        assert response.status_code == 400
        
        data = response.json()
        assert data["status"] == "error"
        assert "invalid" in data["error"].lower()

    def test_calculate_plz_distance_non_existent_plz(self):
        """Test PLZ distance calculation with non-existent PLZ."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "00000",  # Invalid PLZ range
            "destination_plz": "10115"
        })
        assert response.status_code == 404
        
        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["error"].lower()

    def test_calculate_plz_distance_both_non_existent(self):
        """Test PLZ distance calculation with both PLZ non-existent."""
        response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
            "origin_plz": "00001",
            "destination_plz": "00002"
        })
        assert response.status_code == 404
        
        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["error"].lower()

    # Edge Cases and Error Handling

    def test_geocoding_with_special_characters(self):
        """Test geocoding with special characters in address."""
        response = requests.get(f"{BASE_URL}/geocode", params={
            "address": "Café München, Deutschland"
        })
        # Should handle gracefully, either succeed or fail gracefully
        assert response.status_code in [200, 400]

    def test_geocoding_with_very_long_address(self):
        """Test geocoding with very long address string."""
        long_address = "A" * 1000 + " Berlin, Germany"
        response = requests.get(f"{BASE_URL}/geocode", params={
            "address": long_address
        })
        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_distance_calculation_extreme_coordinates(self):
        """Test distance calculation with extreme but valid coordinates."""
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin_lat": -89.0,  # Near South Pole
            "origin_lon": 0.0,
            "destination_lat": 89.0,  # Near North Pole
            "destination_lon": 180.0
        })
        assert response.status_code == 200
        
        data = response.json()
        # Should be a very large distance
        assert data["distance_km"] > 10000

    def test_plz_distance_valid_german_range(self):
        """Test PLZ distance with valid German PLZ ranges."""
        # Test with different German regions
        test_cases = [
            ("01067", "20095"),  # Dresden to Hamburg
            ("80331", "60311"),  # Munich to Frankfurt
            ("50667", "70173")   # Cologne to Stuttgart
        ]
        
        for origin, destination in test_cases:
            response = requests.get(f"{BASE_URL}/calculate-plz-distance", params={
                "origin_plz": origin,
                "destination_plz": destination
            })
            # Should work if PLZ codes exist in database
            assert response.status_code in [200, 404]  # 404 if PLZ not in database

    def test_concurrent_requests(self):
        """Test that service handles concurrent requests properly."""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                response = requests.get(f"{BASE_URL}/geocode", params={
                    "address": "Berlin, Germany"
                }, timeout=10)
                results.append(response.status_code)
            except Exception as e:
                results.append(f"error: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=15)
        
        # All requests should have completed successfully
        assert len(results) == 5
        for result in results:
            assert result == 200, f"Request failed with: {result}"

    def test_response_times(self):
        """Test that responses are reasonably fast."""
        import time
        
        # Test geocoding response time
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/geocode", params={
            "address": "Berlin, Germany"
        })
        geocoding_time = time.time() - start_time
        
        assert response.status_code == 200
        assert geocoding_time < 10.0  # Should respond within 10 seconds
        
        # Test distance calculation response time
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/calculate-distance", params={
            "origin": "Berlin",
            "destination": "Munich"
        })
        distance_time = time.time() - start_time
        
        assert response.status_code == 200
        assert distance_time < 10.0  # Should respond within 10 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
