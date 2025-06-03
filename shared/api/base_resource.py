"""Base resource classes for the therapy platform API."""
from flask import request
from flask_restful import Resource


class PaginatedListResource(Resource):
    """Base resource class with built-in pagination support.
    
    This class provides pagination functionality for list endpoints.
    Subclasses should call self.paginate_query() on their SQLAlchemy
    query objects to apply pagination.
    
    Default pagination settings:
    - page: 1 (first page)
    - limit: 20 items per page
    - max_limit: 100 items per page
    
    Example usage:
        class PatientListResource(PaginatedListResource):
            def get(self):
                query = db.query(Patient)
                query = self.paginate_query(query)
                patients = query.all()
                return patients
    """
    
    DEFAULT_PAGE = 1
    DEFAULT_LIMIT = 20
    MAX_LIMIT = 100
    
    def paginate_query(self, query):
        """Apply pagination to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            
        Returns:
            SQLAlchemy query object with limit and offset applied
        """
        # Get pagination parameters from request
        page = request.args.get('page', self.DEFAULT_PAGE, type=int)
        limit = request.args.get('limit', self.DEFAULT_LIMIT, type=int)
        
        # Validate page number (must be at least 1)
        page = max(1, page)
        
        # Validate limit (must be between 1 and MAX_LIMIT)
        limit = min(max(1, limit), self.MAX_LIMIT)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Apply pagination to query
        return query.limit(limit).offset(offset)
    
    def get_pagination_params(self):
        """Get validated pagination parameters.
        
        Returns:
            tuple: (page, limit) with validated values
        """
        page = request.args.get('page', self.DEFAULT_PAGE, type=int)
        limit = request.args.get('limit', self.DEFAULT_LIMIT, type=int)
        
        # Validate
        page = max(1, page)
        limit = min(max(1, limit), self.MAX_LIMIT)
        
        return page, limit
