"""Matching service API package."""
from .matching import PlacementRequestResource, PlacementRequestListResource
from .bundle import (
    PlatzsucheResource,
    PlatzsucheListResource,
    KontaktanfrageResource,
    TherapeutenanfrageResource,
    TherapeutenanfrageListResource,
    BundleCreationResource,
    BundleResponseResource
)

__all__ = [
    # Legacy endpoints (return 501)
    'PlacementRequestResource',
    'PlacementRequestListResource',
    
    # Bundle system endpoints
    'PlatzsucheResource',
    'PlatzsucheListResource',
    'KontaktanfrageResource',
    'TherapeutenanfrageResource',
    'TherapeutenanfrageListResource',
    'BundleCreationResource',
    'BundleResponseResource'
]