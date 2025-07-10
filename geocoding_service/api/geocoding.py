"""Geocoding API endpoints implementation."""
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

from flask import request, current_app
from flask_restful import Resource, reqparse, fields, marshal_with
import requests

from utils.osm import geocode_address, reverse_geocode, get_route
from utils.distance import calculate_distance, calculate_plz_distance

# Initialize logging
logger = logging.getLogger(__name__)

# Output fields for geocoding responses
geocode_fields = {
    'latitude': fields.Float,
    'longitude': fields.Float,
    'display_name': fields.String,
    'address_components': fields.Raw,
    'source': fields.String,
    'status': fields.String
}

# Output fields for distance calculation responses
distance_fields = {
    'distance_km': fields.Float,
    'status': fields.String,
    'source': fields.String,
    'travel_mode': fields.String,
    'route_available': fields.Boolean
}

# Output fields for PLZ distance responses
plz_distance_fields = {
    'distance_km': fields.Float,
    'status': fields.String,
    'source': fields.String,
    'origin_centroid': fields.Raw,
    'destination_centroid': fields.Raw
}


def format_validation_error(error_dict):
    """Format Flask-RESTful validation errors to match API documentation.
    
    Converts {"field": "error message"} to a simple string.
    """
    if isinstance(error_dict, dict):
        # Get the first error message
        for field, message in error_dict.items():
            return f"{message}"
    return str(error_dict)


class GeocodingResource(Resource):
    """REST resource for geocoding operations."""
    
    def get(self):
        """Geocode an address to coordinates."""
        parser = reqparse.RequestParser()
        parser.add_argument('address', type=str, required=True,
                          help='Address is required',
                          location='args')
        
        try:
            args = parser.parse_args()
        except Exception as e:
            # Handle validation errors to match API documentation
            if hasattr(e, 'data') and 'message' in e.data:
                return {
                    'message': format_validation_error(e.data['message'])
                }, 400
            raise
        
        address = args['address']
        
        result = geocode_address(address)
        
        if result:
            result['status'] = 'success'
            return result, 200
        else:
            return {
                'status': 'error',
                'error': 'Geocoding failed'
            }, 400


class ReverseGeocodingResource(Resource):
    """REST resource for reverse geocoding operations."""
    
    def get(self):
        """Convert coordinates to an address."""
        parser = reqparse.RequestParser()
        parser.add_argument('lat', type=float, required=True,
                          help='Latitude is required',
                          location='args')
        parser.add_argument('lon', type=float, required=True,
                          help='Longitude is required',
                          location='args')
        
        try:
            args = parser.parse_args()
        except Exception as e:
            # Handle validation errors to match API documentation
            if hasattr(e, 'data') and 'message' in e.data:
                return {
                    'message': format_validation_error(e.data['message'])
                }, 400
            raise
        
        latitude = args['lat']
        longitude = args['lon']
        
        result = reverse_geocode(latitude, longitude)
        
        if result:
            result['status'] = 'success'
            return result, 200
        else:
            return {
                'status': 'error',
                'error': 'Reverse geocoding failed'
            }, 400


class DistanceCalculationResource(Resource):
    """REST resource for distance calculation operations."""
    
    def get(self):
        """Calculate distance between two points."""
        parser = reqparse.RequestParser()
        # Origin can be address or coordinates
        parser.add_argument('origin', type=str,
                          help='Origin address',
                          location='args')
        parser.add_argument('origin_lat', type=float,
                          help='Origin latitude',
                          location='args')
        parser.add_argument('origin_lon', type=float,
                          help='Origin longitude',
                          location='args')
        
        # Destination can be address or coordinates
        parser.add_argument('destination', type=str,
                          help='Destination address',
                          location='args')
        parser.add_argument('destination_lat', type=float,
                          help='Destination latitude',
                          location='args')
        parser.add_argument('destination_lon', type=float,
                          help='Destination longitude',
                          location='args')
        
        # Optional parameters
        parser.add_argument('travel_mode', type=str, default='car',
                          choices=['car', 'transit'],
                          help='Mode of transport (car or transit)',
                          location='args')
        parser.add_argument('no_cache', type=bool, default=False,
                          help='Bypass cache for fresh calculation',
                          location='args')
        parser.add_argument('use_plz_fallback', type=bool, default=True,
                          help='Use PLZ-based fallback for addresses',
                          location='args')
        
        try:
            args = parser.parse_args()
        except Exception as e:
            # Handle validation errors
            if hasattr(e, 'data') and 'message' in e.data:
                return {
                    'message': format_validation_error(e.data['message'])
                }, 400
            raise
        
        # Process origin
        origin = None
        if args['origin']:
            origin = args['origin']
        elif args['origin_lat'] is not None and args['origin_lon'] is not None:
            origin = (args['origin_lat'], args['origin_lon'])
        else:
            return {
                'status': 'error', 
                'error': 'Origin is required (address or coordinates)'
            }, 400
        
        # Process destination
        destination = None
        if args['destination']:
            destination = args['destination']
        elif args['destination_lat'] is not None and args['destination_lon'] is not None:
            destination = (args['destination_lat'], args['destination_lon'])
        else:
            return {
                'status': 'error', 
                'error': 'Destination is required (address or coordinates)'
            }, 400
        
        # Calculate distance
        result = calculate_distance(
            origin, 
            destination,
            travel_mode=args['travel_mode'],
            use_cache=not args['no_cache'],
            use_plz_fallback=args['use_plz_fallback']
        )
        
        return result, 200


class PLZDistanceResource(Resource):
    """REST resource for PLZ-based distance calculation."""
    
    def get(self):
        """Calculate distance between two PLZ centroids."""
        parser = reqparse.RequestParser()
        parser.add_argument('origin_plz', type=str, required=True,
                          help='Origin PLZ is required',
                          location='args')
        parser.add_argument('destination_plz', type=str, required=True,
                          help='Destination PLZ is required',
                          location='args')
        
        try:
            args = parser.parse_args()
        except Exception as e:
            # Handle validation errors to match API documentation
            if hasattr(e, 'data') and 'message' in e.data:
                return {
                    'message': format_validation_error(e.data['message'])
                }, 400
            raise
        
        # Validate PLZ format
        origin_plz = args['origin_plz'].strip()
        destination_plz = args['destination_plz'].strip()
        
        if len(origin_plz) != 5 or not origin_plz.isdigit():
            return {
                'status': 'error',
                'error': f'Invalid origin PLZ format: {origin_plz}'
            }, 400
            
        if len(destination_plz) != 5 or not destination_plz.isdigit():
            return {
                'status': 'error',
                'error': f'Invalid destination PLZ format: {destination_plz}'
            }, 400
        
        # Calculate distance using PLZ centroids
        result = calculate_plz_distance(origin_plz, destination_plz)
        
        if result:
            return result, 200
        else:
            return {
                'status': 'error',
                'error': 'One or both PLZ codes not found'
            }, 404