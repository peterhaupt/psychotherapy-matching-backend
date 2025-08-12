"""Unit tests for therapist blocking cascade to Matching service.

Tests that blocking/unblocking a therapist calls the Matching service cascade endpoints.
This version tests the REAL TherapistResource implementation.
"""
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import date
import json
from enum import Enum


@pytest.fixture
def mock_therapist_dependencies():
    """Mock all dependencies before importing the code under test."""
    # Save original modules
    original_modules = {}
    modules_to_mock = [
        'models',
        'models.therapist',
        'shared',
        'shared.utils',
        'shared.utils.database',
        'shared.config',
        'shared.api',
        'shared.api.base_resource',
        'shared.api.retry_client',
        'shared.kafka',
        'shared.kafka.robust_producer',
        'events',
        'events.producers',
        'imports',
        'flask',
        'flask_restful',
        'sqlalchemy',
        'sqlalchemy.exc',
        'sqlalchemy.orm',
        'requests',
        'logging',
    ]
    
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Mock all dependencies
    sys.modules['models'] = MagicMock()
    sys.modules['models.therapist'] = MagicMock()
    sys.modules['shared'] = MagicMock()
    sys.modules['shared.utils'] = MagicMock()
    sys.modules['shared.utils.database'] = MagicMock()
    sys.modules['shared.config'] = MagicMock()
    sys.modules['shared.api'] = MagicMock()
    sys.modules['shared.api.base_resource'] = MagicMock()
    sys.modules['shared.api.retry_client'] = MagicMock()
    sys.modules['shared.kafka'] = MagicMock()
    sys.modules['shared.kafka.robust_producer'] = MagicMock()
    sys.modules['events'] = MagicMock()
    sys.modules['events.producers'] = MagicMock()
    sys.modules['imports'] = MagicMock()
    sys.modules['flask'] = MagicMock()
    sys.modules['flask_restful'] = MagicMock()
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlalchemy.exc'] = MagicMock()
    sys.modules['sqlalchemy.orm'] = MagicMock()
    sys.modules['requests'] = MagicMock()
    sys.modules['logging'] = MagicMock()
    
    # Create mock enums for TherapistStatus, Anrede, Geschlecht, Therapieverfahren
    class MockTherapistStatus(str, Enum):
        aktiv = "aktiv"
        gesperrt = "gesperrt"
        inaktiv = "inaktiv"
    
    class MockAnrede(str, Enum):
        Herr = "Herr"
        Frau = "Frau"
    
    class MockGeschlecht(str, Enum):
        männlich = "männlich"
        weiblich = "weiblich"
        divers = "divers"
        keine_Angabe = "keine_Angabe"
    
    class MockTherapieverfahren(str, Enum):
        egal = "egal"
        Verhaltenstherapie = "Verhaltenstherapie"
        tiefenpsychologisch_fundierte_Psychotherapie = "tiefenpsychologisch_fundierte_Psychotherapie"
    
    # Set up the enums in models.therapist
    sys.modules['models.therapist'].TherapistStatus = MockTherapistStatus
    sys.modules['models.therapist'].Anrede = MockAnrede
    sys.modules['models.therapist'].Geschlecht = MockGeschlecht
    sys.modules['models.therapist'].Therapieverfahren = MockTherapieverfahren
    sys.modules['models.therapist'].Therapist = MagicMock()
    
    # Mock shared modules
    mock_config = MagicMock()
    mock_config.get_service_url.return_value = "http://matching-service"
    sys.modules['shared.config'].get_config = MagicMock(return_value=mock_config)
    
    # Mock RetryAPIClient
    mock_retry_client = MagicMock()
    sys.modules['shared.api.retry_client'].RetryAPIClient = mock_retry_client
    
    # Mock SessionLocal
    mock_session_local = MagicMock()
    sys.modules['shared.utils.database'].SessionLocal = mock_session_local
    
    # Mock Flask-RESTful components
    mock_reqparse = MagicMock()
    mock_parser = MagicMock()
    mock_reqparse.RequestParser = MagicMock(return_value=mock_parser)
    sys.modules['flask_restful'].reqparse = mock_reqparse
    sys.modules['flask_restful'].Resource = MagicMock()
    sys.modules['flask_restful'].fields = MagicMock()
    sys.modules['flask_restful'].marshal = MagicMock(return_value={})
    sys.modules['flask_restful'].marshal_with = MagicMock(return_value=lambda x: x)
    
    # Mock PaginatedListResource
    sys.modules['shared.api.base_resource'].PaginatedListResource = MagicMock()
    
    # Mock ImportStatus
    sys.modules['imports'].ImportStatus = MagicMock()
    
    # Mock requests exceptions
    sys.modules['requests'].RequestException = Exception
    sys.modules['requests'].exceptions = MagicMock()
    
    # Mock logging
    mock_logger = MagicMock()
    sys.modules['logging'].getLogger = MagicMock(return_value=mock_logger)
    
    # NOW import the REAL classes after mocking
    from therapist_service.api.therapists import TherapistResource
    
    yield {
        'TherapistResource': TherapistResource,
        'TherapistStatus': MockTherapistStatus,
        'Anrede': MockAnrede,
        'Geschlecht': MockGeschlecht,
        'Therapieverfahren': MockTherapieverfahren,
        'mock_config': mock_config,
        'mock_retry_client': mock_retry_client,
        'mock_session_local': mock_session_local,
        'mock_parser': mock_parser,
        'mock_logger': mock_logger
    }
    
    # Cleanup
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


class TestTherapistBlockingCascade:
    """Test therapist blocking/unblocking with cascade to Matching service."""
    
    def test_block_therapist_calls_matching_api(self, mock_therapist_dependencies):
        """Test that blocking therapist calls Matching service cascade endpoint."""
        TherapistResource = mock_therapist_dependencies['TherapistResource']
        TherapistStatus = mock_therapist_dependencies['TherapistStatus']
        mock_session_local = mock_therapist_dependencies['mock_session_local']
        mock_parser = mock_therapist_dependencies['mock_parser']
        mock_retry_client = mock_therapist_dependencies['mock_retry_client']
        mock_config = mock_therapist_dependencies['mock_config']
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = TherapistStatus.aktiv  # Currently active
        mock_therapist.sperrgrund = None
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'gesperrt',
            'sperrgrund': 'Test reason',
            # Include all other fields as None to avoid KeyError
            'anrede': None,
            'geschlecht': None,
            'titel': None,
            'vorname': None,
            'nachname': None,
            'strasse': None,
            'plz': None,
            'ort': None,
            'telefon': None,
            'fax': None,
            'email': None,
            'webseite': None,
            'kassensitz': None,
            'telefonische_erreichbarkeit': None,
            'fremdsprachen': None,
            'psychotherapieverfahren': None,
            'zusatzqualifikationen': None,
            'besondere_leistungsangebote': None,
            'letzter_kontakt_email': None,
            'letzter_kontakt_telefon': None,
            'letztes_persoenliches_gespraech': None,
            'potenziell_verfuegbar': None,
            'potenziell_verfuegbar_notizen': None,
            'ueber_curavani_informiert': None,
            'naechster_kontakt_moeglich': None,
            'bevorzugte_diagnosen': None,
            'alter_min': None,
            'alter_max': None,
            'geschlechtspraeferenz': None,
            'arbeitszeiten': None,
            'bevorzugt_gruppentherapie': None,
            'sperrdatum': None
        }
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"cancelled_anfragen": 3}'
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        # Mock the validate functions
        with patch('therapist_service.api.therapists.validate_and_get_therapist_status', return_value=TherapistStatus.gesperrt):
            # Execute
            result = resource.put(456)
        
        # Verify API was called
        mock_retry_client.call_with_retry.assert_called_once_with(
            method="POST",
            url="http://matching-service/api/matching/cascade/therapist-blocked",
            json={
                "therapist_id": 456,
                "reason": "Test reason"
            }
        )
        
        # Verify therapist was updated
        assert mock_therapist.status == TherapistStatus.gesperrt
        assert mock_therapist.sperrgrund == 'Test reason'
        mock_db.commit.assert_called_once()
        
        # Verify response (the real implementation returns marshaled data)
        assert result is not None  # Should return marshaled therapist data
    
    def test_block_therapist_rollback_on_matching_failure(self, mock_therapist_dependencies):
        """Test that therapist blocking is rolled back if Matching service fails."""
        TherapistResource = mock_therapist_dependencies['TherapistResource']
        TherapistStatus = mock_therapist_dependencies['TherapistStatus']
        mock_session_local = mock_therapist_dependencies['mock_session_local']
        mock_parser = mock_therapist_dependencies['mock_parser']
        mock_retry_client = mock_therapist_dependencies['mock_retry_client']
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = TherapistStatus.aktiv
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'gesperrt',
            'sperrgrund': 'Test reason',
            # Include all other fields as None
            'anrede': None,
            'geschlecht': None,
            'titel': None,
            'vorname': None,
            'nachname': None,
            'strasse': None,
            'plz': None,
            'ort': None,
            'telefon': None,
            'fax': None,
            'email': None,
            'webseite': None,
            'kassensitz': None,
            'telefonische_erreichbarkeit': None,
            'fremdsprachen': None,
            'psychotherapieverfahren': None,
            'zusatzqualifikationen': None,
            'besondere_leistungsangebote': None,
            'letzter_kontakt_email': None,
            'letzter_kontakt_telefon': None,
            'letztes_persoenliches_gespraech': None,
            'potenziell_verfuegbar': None,
            'potenziell_verfuegbar_notizen': None,
            'ueber_curavani_informiert': None,
            'naechster_kontakt_moeglich': None,
            'bevorzugte_diagnosen': None,
            'alter_min': None,
            'alter_max': None,
            'geschlechtspraeferenz': None,
            'arbeitszeiten': None,
            'bevorzugt_gruppentherapie': None,
            'sperrdatum': None
        }
        
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        # Execute
        result, status_code = resource.put(456)
        
        # Verify therapist was NOT updated
        assert mock_therapist.status == TherapistStatus.aktiv  # Still active
        mock_db.commit.assert_not_called()
        
        # Verify error response
        assert status_code == 500
        assert "Cannot block therapist: Matching service error" in result['message']
    
    def test_unblock_therapist_calls_matching_api(self, mock_therapist_dependencies):
        """Test that unblocking therapist calls Matching service cascade endpoint."""
        TherapistResource = mock_therapist_dependencies['TherapistResource']
        TherapistStatus = mock_therapist_dependencies['TherapistStatus']
        mock_session_local = mock_therapist_dependencies['mock_session_local']
        mock_parser = mock_therapist_dependencies['mock_parser']
        mock_retry_client = mock_therapist_dependencies['mock_retry_client']
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = TherapistStatus.gesperrt  # Currently blocked
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'aktiv',
            'sperrgrund': None,
            # Include all other fields as None
            'anrede': None,
            'geschlecht': None,
            'titel': None,
            'vorname': None,
            'nachname': None,
            'strasse': None,
            'plz': None,
            'ort': None,
            'telefon': None,
            'fax': None,
            'email': None,
            'webseite': None,
            'kassensitz': None,
            'telefonische_erreichbarkeit': None,
            'fremdsprachen': None,
            'psychotherapieverfahren': None,
            'zusatzqualifikationen': None,
            'besondere_leistungsangebote': None,
            'letzter_kontakt_email': None,
            'letzter_kontakt_telefon': None,
            'letztes_persoenliches_gespraech': None,
            'potenziell_verfuegbar': None,
            'potenziell_verfuegbar_notizen': None,
            'ueber_curavani_informiert': None,
            'naechster_kontakt_moeglich': None,
            'bevorzugte_diagnosen': None,
            'alter_min': None,
            'alter_max': None,
            'geschlechtspraeferenz': None,
            'arbeitszeiten': None,
            'bevorzugt_gruppentherapie': None,
            'sperrdatum': None
        }
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_retry_client.call_with_retry.return_value = mock_response
        
        # Mock the validate functions
        with patch('therapist_service.api.therapists.validate_and_get_therapist_status', return_value=TherapistStatus.aktiv):
            # Execute
            result = resource.put(456)
        
        # Verify API was called
        mock_retry_client.call_with_retry.assert_called_once_with(
            method="POST",
            url="http://matching-service/api/matching/cascade/therapist-unblocked",
            json={"therapist_id": 456}
        )
        
        # Verify therapist was updated
        assert mock_therapist.status == TherapistStatus.aktiv
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert result is not None  # Should return marshaled therapist data
    
    def test_unblock_therapist_non_critical_failure(self, mock_therapist_dependencies):
        """Test that unblocking continues even if cascade fails (non-critical)."""
        TherapistResource = mock_therapist_dependencies['TherapistResource']
        TherapistStatus = mock_therapist_dependencies['TherapistStatus']
        mock_session_local = mock_therapist_dependencies['mock_session_local']
        mock_parser = mock_therapist_dependencies['mock_parser']
        mock_retry_client = mock_therapist_dependencies['mock_retry_client']
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = TherapistStatus.gesperrt
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'aktiv',
            'sperrgrund': None,
            # Include all other fields as None
            'anrede': None,
            'geschlecht': None,
            'titel': None,
            'vorname': None,
            'nachname': None,
            'strasse': None,
            'plz': None,
            'ort': None,
            'telefon': None,
            'fax': None,
            'email': None,
            'webseite': None,
            'kassensitz': None,
            'telefonische_erreichbarkeit': None,
            'fremdsprachen': None,
            'psychotherapieverfahren': None,
            'zusatzqualifikationen': None,
            'besondere_leistungsangebote': None,
            'letzter_kontakt_email': None,
            'letzter_kontakt_telefon': None,
            'letztes_persoenliches_gespraech': None,
            'potenziell_verfuegbar': None,
            'potenziell_verfuegbar_notizen': None,
            'ueber_curavani_informiert': None,
            'naechster_kontakt_moeglich': None,
            'bevorzugte_diagnosen': None,
            'alter_min': None,
            'alter_max': None,
            'geschlechtspraeferenz': None,
            'arbeitszeiten': None,
            'bevorzugt_gruppentherapie': None,
            'sperrdatum': None
        }
        
        # Mock API failure (but non-critical for unblocking)
        mock_retry_client.call_with_retry.side_effect = Exception("Connection error")
        
        # Mock the validate functions
        with patch('therapist_service.api.therapists.validate_and_get_therapist_status', return_value=TherapistStatus.aktiv):
            # Execute
            result = resource.put(456)
        
        # Verify therapist was still updated (non-critical failure)
        assert mock_therapist.status == TherapistStatus.aktiv
        mock_db.commit.assert_called_once()
        
        # Verify success response
        assert result is not None  # Should return marshaled therapist data
    
    def test_status_change_not_to_gesperrt_no_cascade(self, mock_therapist_dependencies):
        """Test that changing status to something other than gesperrt doesn't trigger cascade."""
        TherapistResource = mock_therapist_dependencies['TherapistResource']
        TherapistStatus = mock_therapist_dependencies['TherapistStatus']
        mock_session_local = mock_therapist_dependencies['mock_session_local']
        mock_parser = mock_therapist_dependencies['mock_parser']
        mock_retry_client = mock_therapist_dependencies['mock_retry_client']
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = TherapistStatus.aktiv
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser - changing to inaktiv (not gesperrt)
        mock_parser.parse_args.return_value = {
            'status': 'inaktiv',
            'sperrgrund': None,
            # Include all other fields as None
            'anrede': None,
            'geschlecht': None,
            'titel': None,
            'vorname': None,
            'nachname': None,
            'strasse': None,
            'plz': None,
            'ort': None,
            'telefon': None,
            'fax': None,
            'email': None,
            'webseite': None,
            'kassensitz': None,
            'telefonische_erreichbarkeit': None,
            'fremdsprachen': None,
            'psychotherapieverfahren': None,
            'zusatzqualifikationen': None,
            'besondere_leistungsangebote': None,
            'letzter_kontakt_email': None,
            'letzter_kontakt_telefon': None,
            'letztes_persoenliches_gespraech': None,
            'potenziell_verfuegbar': None,
            'potenziell_verfuegbar_notizen': None,
            'ueber_curavani_informiert': None,
            'naechster_kontakt_moeglich': None,
            'bevorzugte_diagnosen': None,
            'alter_min': None,
            'alter_max': None,
            'geschlechtspraeferenz': None,
            'arbeitszeiten': None,
            'bevorzugt_gruppentherapie': None,
            'sperrdatum': None
        }
        
        # Mock the validate functions
        with patch('therapist_service.api.therapists.validate_and_get_therapist_status', return_value=TherapistStatus.inaktiv):
            # Execute
            result = resource.put(456)
            
            # Verify NO API call was made
            mock_retry_client.call_with_retry.assert_not_called()
        
        # Verify therapist was updated
        assert mock_therapist.status == TherapistStatus.inaktiv
        mock_db.commit.assert_called_once()
        
        # Verify response
        assert result is not None  # Should return marshaled therapist data
    
    def test_network_error_on_blocking(self, mock_therapist_dependencies):
        """Test handling network errors when trying to block a therapist."""
        TherapistResource = mock_therapist_dependencies['TherapistResource']
        TherapistStatus = mock_therapist_dependencies['TherapistStatus']
        mock_session_local = mock_therapist_dependencies['mock_session_local']
        mock_parser = mock_therapist_dependencies['mock_parser']
        mock_retry_client = mock_therapist_dependencies['mock_retry_client']
        
        resource = TherapistResource()
        
        # Mock therapist
        mock_therapist = Mock()
        mock_therapist.id = 456
        mock_therapist.status = TherapistStatus.aktiv
        
        # Mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_therapist
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'gesperrt',
            'sperrgrund': 'Network test',
            # Include all other fields as None
            'anrede': None,
            'geschlecht': None,
            'titel': None,
            'vorname': None,
            'nachname': None,
            'strasse': None,
            'plz': None,
            'ort': None,
            'telefon': None,
            'fax': None,
            'email': None,
            'webseite': None,
            'kassensitz': None,
            'telefonische_erreichbarkeit': None,
            'fremdsprachen': None,
            'psychotherapieverfahren': None,
            'zusatzqualifikationen': None,
            'besondere_leistungsangebote': None,
            'letzter_kontakt_email': None,
            'letzter_kontakt_telefon': None,
            'letztes_persoenliches_gespraech': None,
            'potenziell_verfuegbar': None,
            'potenziell_verfuegbar_notizen': None,
            'ueber_curavani_informiert': None,
            'naechster_kontakt_moeglich': None,
            'bevorzugte_diagnosen': None,
            'alter_min': None,
            'alter_max': None,
            'geschlechtspraeferenz': None,
            'arbeitszeiten': None,
            'bevorzugt_gruppentherapie': None,
            'sperrdatum': None
        }
        
        # Mock network error
        import requests
        mock_retry_client.call_with_retry.side_effect = requests.RequestException("Connection timeout")
        
        # Execute
        result, status_code = resource.put(456)
        
        # Verify therapist was NOT updated
        assert mock_therapist.status == TherapistStatus.aktiv  # Still active
        mock_db.commit.assert_not_called()
        
        # Verify service unavailable response
        assert status_code == 503
        assert "Matching service unavailable" in result['message']
    
    def test_therapist_not_found(self, mock_therapist_dependencies):
        """Test updating a therapist that doesn't exist."""
        TherapistResource = mock_therapist_dependencies['TherapistResource']
        mock_session_local = mock_therapist_dependencies['mock_session_local']
        mock_parser = mock_therapist_dependencies['mock_parser']
        mock_retry_client = mock_therapist_dependencies['mock_retry_client']
        
        resource = TherapistResource()
        
        # Mock database session - no therapist found
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None  # Therapist not found
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query
        
        mock_session_local.return_value = mock_db
        
        # Mock request parser
        mock_parser.parse_args.return_value = {
            'status': 'gesperrt',
            # Include all other fields as None
            'anrede': None,
            'geschlecht': None,
            'titel': None,
            'vorname': None,
            'nachname': None,
            'strasse': None,
            'plz': None,
            'ort': None,
            'telefon': None,
            'fax': None,
            'email': None,
            'webseite': None,
            'kassensitz': None,
            'telefonische_erreichbarkeit': None,
            'fremdsprachen': None,
            'psychotherapieverfahren': None,
            'zusatzqualifikationen': None,
            'besondere_leistungsangebote': None,
            'letzter_kontakt_email': None,
            'letzter_kontakt_telefon': None,
            'letztes_persoenliches_gespraech': None,
            'potenziell_verfuegbar': None,
            'potenziell_verfuegbar_notizen': None,
            'ueber_curavani_informiert': None,
            'naechster_kontakt_moeglich': None,
            'bevorzugte_diagnosen': None,
            'alter_min': None,
            'alter_max': None,
            'geschlechtspraeferenz': None,
            'arbeitszeiten': None,
            'bevorzugt_gruppentherapie': None,
            'sperrgrund': None,
            'sperrdatum': None
        }
        
        # Execute
        result, status_code = resource.put(999)
        
        # Verify
        assert status_code == 404
        assert result['message'] == 'Therapist not found'
        
        # Verify no API call was made
        mock_retry_client.call_with_retry.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])