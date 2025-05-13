"""Unit tests for the Geocoding Service."""
import unittest
from unittest.mock import patch, MagicMock
import json

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from geocoding_service.utils.distance import calculate_haversine_distance
from geocoding_service.utils.osm import geocode_address


class TestGeocoding(unittest.TestCase):
    """Test cases for geocoding functionality."""
    
    def test_haversine_distance(self):
        """Test the haversine distance calculation."""
        # Berlin coordinates
        berlin = (52.5200, 13.4050)
        # Munich coordinates
        munich = (48.1351, 11.5820)
        
        # Calculate distance between Berlin and Munich
        distance = calculate_haversine_distance(berlin, munich)
        
        # Distance should be approximately 504 km
        self.assertGreater(distance, 500)
        self.assertLess(distance, 510)
    
    @patch('geocoding_service.utils.osm._make_request')
    def test_geocode_address(self, mock_make_request):
        """Test geocoding an address."""
        # Mock response from OpenStreetMap API
        mock_response = [
            {
                "lat": "52.5200",
                "lon": "13.4050",
                "display_name": "Berlin, Germany",
                "address": {
                    "city": "Berlin",
                    "country": "Germany"
                }
            }
        ]
        mock_make_request.return_value = mock_response
        
        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Patch SessionLocal to return our mock
        with patch('geocoding_service.utils.osm.SessionLocal', return_value=mock_db):
            # Geocode an address
            result = geocode_address("Berlin, Germany")
            
            # Assert that the geocoding was successful
            self.assertIsNotNone(result)
            self.assertEqual(result["latitude"], 52.52)
            self.assertEqual(result["longitude"], 13.405)
            self.assertEqual(result["display_name"], "Berlin, Germany")
            
            # Check that API was called with correct parameters
            mock_make_request.assert_called_once()
            url, params = mock_make_request.call_args[0]
            self.assertIn("search", url)
            self.assertEqual(params["q"], "Berlin, Germany")


if __name__ == "__main__":
    unittest.main()