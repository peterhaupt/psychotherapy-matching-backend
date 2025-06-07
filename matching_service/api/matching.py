"""Matching API endpoints implementation - TEMPORARY STUB."""
from flask_restful import Resource


class PlacementRequestResource(Resource):
    """REST resource for individual placement request operations - STUB."""

    def get(self, request_id):
        """Temporary stub - bundle system not yet implemented."""
        return {'message': 'Bundle system not yet implemented', 'request_id': request_id}, 501

    def put(self, request_id):
        """Temporary stub - bundle system not yet implemented."""
        return {'message': 'Bundle system not yet implemented', 'request_id': request_id}, 501

    def delete(self, request_id):
        """Temporary stub - bundle system not yet implemented."""
        return {'message': 'Bundle system not yet implemented', 'request_id': request_id}, 501


class PlacementRequestListResource(Resource):
    """REST resource for placement request collection operations - STUB."""

    def get(self):
        """Temporary stub - bundle system not yet implemented."""
        return {
            'message': 'Bundle system not yet implemented',
            'data': [],
            'page': 1,
            'limit': 20,
            'total': 0
        }, 501

    def post(self):
        """Temporary stub - bundle system not yet implemented."""
        return {'message': 'Bundle system not yet implemented'}, 501