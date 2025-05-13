"""Geocoding API endpoints implementation."""
import logging
from typing import Dict, List, Optional, Tuple, Any, Union

from flask import request, current_app
from flask_restful import Resource, reqparse, fields, marshal_with
import requests

from utils.osm import geocode_address, reverse_geocode, get_route
from utils.distance import calculate_distance, find_nearby_therapists

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
    'travel_time_minutes': fields.Float,
    'status': fields.String,
    'source': fields.String,
    'travel_mode': fields.String,
    'route_available': fields.Boolean
}

# Output fields for therapist search responses
therapist_distance_fields = {
    'id': fields.Integer,
    'distance_km': fields.Float,
    'travel_time_minutes': fields.Float,
    'travel_mode': fields.String
}


class GeocodingResource(Resource):
    """REST resource for geocoding operations."""
    
    @marshal_with(geocode_fields)
    def get(self):
        """Geocode an address to coordinates."""
        parser = reqparse.RequestParser()
        parser.add_argument('address', type=str, required=True,
                          help='Address is required',
                          location='args')  # Look for arguments in query string
        
        args = parser.parse_args()
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
    
    @marshal_with(geocode_fields)
    def get(self):
        """Convert coordinates to an address."""
        parser = reqparse.RequestParser()
        parser.add_argument('lat', type=float, required=True,
                          help='Latitude is required',
                          location='args')  # Look for arguments in query string
        parser.add_argument('lon', type=float, required=True,
                          help='Longitude is required',
                          location='args')  # Look for arguments in query string
        
        args = parser.parse_args()
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
    
    @marshal_with(distance_fields)
    def get(self):
        """Calculate distance between two points."""
        parser = reqparse.RequestParser()
        # Origin can be address or coordinates
        parser.add_argument('origin', type=str,
                          help='Origin address',
                          location='args')  # Look for arguments in query string
        parser.add_argument('origin_lat', type=float,
                          help='Origin latitude',
                          location='args')  # Look for arguments in query string
        parser.add_argument('origin_lon', type=float,
                          help='Origin longitude',
                          location='args')  # Look for arguments in query string
        
        # Destination can be address or coordinates
        parser.add_argument('destination', type=str,
                          help='Destination address',
                          location='args')  # Look for arguments in query string
        parser.add_argument('destination_lat', type=float,
                          help='Destination latitude',
                          location='args')  # Look for arguments in query string
        parser.add_argument('destination_lon', type=float,
                          help='Destination longitude',
                          location='args')  # Look for arguments in query string
        
        # Optional parameters
        parser.add_argument('travel_mode', type=str, default='car',
                          choices=['car', 'transit'],
                          help='Mode of transport (car or transit)',
                          location='args')  # Look for arguments in query string
        parser.add_argument('no_cache', type=bool, default=False,
                          help='Bypass cache for fresh calculation',
                          location='args')  # Look for arguments in query string
        
        args = parser.parse_args()
        
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
            use_cache=not args['no_cache']
        )
        
        return result, 200


class TherapistSearchResource(Resource):
    """REST resource for therapist search operations."""
    
    def post(self):
        """Find therapists within a specified distance from a patient."""
        parser = reqparse.RequestParser()
        # Patient location
        parser.add_argument('patient_address', type=str,
                          help='Patient address')
        parser.add_argument('patient_lat', type=float,
                          help='Patient latitude')
        parser.add_argument('patient_lon', type=float,
                          help='Patient longitude')
        
        # Search parameters
        parser.add_argument('max_distance_km', type=float, default=30.0,
                          help='Maximum distance in kilometers')
        parser.add_argument('travel_mode', type=str, default='car',
                          choices=['car', 'transit'],
                          help='Mode of transport (car or transit)')
        
        # Therapist list
        parser.add_argument('therapists', type=list, required=True,
                          help='List of therapist data is required')
        
        args = parser.parse_args()
        
        # Process patient location
        patient_location = None
        if args['patient_address']:
            patient_location = args['patient_address']
        elif args['patient_lat'] is not None and args['patient_lon'] is not None:
            patient_location = (args['patient_lat'], args['patient_lon'])
        else:
            return {
                'status': 'error', 
                'error': 'Patient location is required (address or coordinates)'
            }, 400
        
        # Process therapist list
        therapists = args['therapists']
        
        # Find nearby therapists
        results = find_nearby_therapists(
            patient_location,
            therapists,
            max_distance_km=args['max_distance_km'],
            travel_mode=args['travel_mode']
        )
        
        return {
            'status': 'success',
            'count': len(results),
            'therapists': results
        }, 200