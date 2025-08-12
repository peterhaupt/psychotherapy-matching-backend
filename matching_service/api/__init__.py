"""Matching service API package."""
from .anfrage import (
    PlatzsucheResource,
    PlatzsucheListResource,
    KontaktanfrageResource,
    TherapeutenZurAuswahlResource,
    TherapeutenanfrageResource,
    TherapeutenanfrageListResource,
    AnfrageCreationResource,
    AnfrageResponseResource,
    AnfrageSendResource
)
from .cascade_operations import (
    PatientDeletedCascadeResource,
    TherapistBlockedCascadeResource,
    TherapistUnblockedCascadeResource
)

__all__ = [
    # Anfrage system endpoints
    'PlatzsucheResource',
    'PlatzsucheListResource',
    'KontaktanfrageResource',
    'TherapeutenZurAuswahlResource',
    'TherapeutenanfrageResource',
    'TherapeutenanfrageListResource',
    'AnfrageCreationResource',
    'AnfrageResponseResource',
    'AnfrageSendResource',
    # Cascade operation endpoints
    'PatientDeletedCascadeResource',
    'TherapistBlockedCascadeResource',
    'TherapistUnblockedCascadeResource'
]