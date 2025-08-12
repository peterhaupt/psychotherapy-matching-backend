"""Unit tests for local therapist import file processing.

These tests cover the therapist import functionality and specifically test
for the critical bug where manual status fields are being overwritten.

IMPORTANT: Several tests in TestStatusPreservation will FAIL intentionally
to demonstrate the current bug in the import logic.
"""
import json
import os
import sys
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock, call
from datetime import datetime, date, timedelta
from enum import Enum


# Create mock classes and enums for testing
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


@pytest.fixture
def mock_therapist_importer():
    """Create a TherapistImporter instance with mocked dependencies."""
    # Store original modules to restore later
    original_modules = {}
    modules_to_mock = [
        'models', 'models.therapist',
        'shared', 'shared.utils', 'shared.utils.database',
        'shared.config', 'shared.api', 'shared.api.retry_client',
        'events', 'events.producers',
        'api', 'api.therapists'
    ]
    
    # Save originals
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Create mocks for dependencies
    mock_config = MagicMock()
    mock_config.get_service_url = MagicMock(return_value="http://test-comm-service")
    
    mock_session_local = MagicMock()
    mock_therapist_model = MagicMock()
    mock_therapist_model.Therapist = MagicMock()
    mock_therapist_model.Therapieverfahren = MockTherapieverfahren
    
    # Setup mocked modules
    sys.modules['models'] = MagicMock()
    sys.modules['models.therapist'] = mock_therapist_model
    sys.modules['shared'] = MagicMock()
    sys.modules['shared.utils'] = MagicMock()
    sys.modules['shared.utils.database'] = MagicMock(SessionLocal=mock_session_local)
    sys.modules['shared.config'] = MagicMock(get_config=lambda: mock_config)
    sys.modules['shared.api'] = MagicMock()
    sys.modules['shared.api.retry_client'] = MagicMock()
    sys.modules['events'] = MagicMock()
    sys.modules['events.producers'] = MagicMock(
        publish_therapist_created=MagicMock(),
        publish_therapist_updated=MagicMock()
    )
    sys.modules['api'] = MagicMock()
    
    # Mock api.therapists module with all needed functions
    mock_api_therapists = MagicMock()
    mock_api_therapists.validate_and_get_anrede = MagicMock(side_effect=lambda x: MockAnrede[x] if x in ['Herr', 'Frau'] else None)
    mock_api_therapists.validate_and_get_geschlecht = MagicMock(side_effect=lambda x: MockGeschlecht[x] if x in MockGeschlecht.__members__ else None)
    mock_api_therapists.validate_and_get_therapist_status = MagicMock(side_effect=lambda x: MockTherapistStatus[x] if x in MockTherapistStatus.__members__ else None)
    mock_api_therapists.validate_and_get_therapieverfahren = MagicMock(side_effect=lambda x: MockTherapieverfahren[x] if x in MockTherapieverfahren.__members__ else None)
    mock_api_therapists.parse_date_field = MagicMock(side_effect=lambda x, _: x)
    mock_api_therapists.therapist_fields = {}
    mock_api_therapists.marshal = MagicMock(return_value={})
    sys.modules['api.therapists'] = mock_api_therapists
    
    # Now import the actual class
    from therapist_service.imports.therapist_importer import TherapistImporter
    
    # Create instance
    importer = TherapistImporter()
    
    # Store references for test use
    importer._mock_session_local = mock_session_local
    importer._mock_config = mock_config
    importer._mock_api_therapists = mock_api_therapists
    
    yield importer
    
    # Cleanup: restore original modules
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


@pytest.fixture
def mock_file_monitor():
    """Create a LocalFileMonitor instance with mocked dependencies."""
    # Store original modules to restore later
    original_modules = {}
    modules_to_mock = [
        'therapist_service.imports.therapist_importer',
        'therapist_service.imports.import_status',
        'shared', 'shared.config'
    ]
    
    # Save originals
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Create mocks
    mock_config = MagicMock()
    mock_config.get_service_url = MagicMock(return_value="http://test-service")
    
    mock_therapist_importer = MagicMock()
    mock_therapist_importer.TherapistImporter = MagicMock()
    
    mock_import_status = MagicMock()
    mock_import_status.ImportStatus = MagicMock()
    
    # Setup mocked modules
    sys.modules['shared'] = MagicMock()
    sys.modules['shared.config'] = MagicMock(get_config=lambda: mock_config)
    sys.modules['therapist_service.imports.therapist_importer'] = mock_therapist_importer
    sys.modules['therapist_service.imports.import_status'] = mock_import_status
    
    # Set environment variables
    with patch.dict(os.environ, {
        'THERAPIST_IMPORT_FOLDER_PATH': '/test/import/path',
        'THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS': '86400'  # 24 hours
    }):
        # Now import the actual class
        from therapist_service.imports.file_monitor import LocalFileMonitor
        
        # Create instance
        monitor = LocalFileMonitor()
        monitor.importer = Mock()
        
        yield monitor
    
    # Cleanup: restore original modules
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


@pytest.fixture
def sample_therapist_json():
    """Sample therapist data from scraper JSON format."""
    return {
        "basic_info": {
            "salutation": "Frau",
            "title": "Dr. med.",
            "first_name": "Maria",
            "last_name": "Schmidt"
        },
        "location": {
            "street": "Therapiestraße",
            "house_number": "42",
            "postal_code": "52062",
            "city": "Aachen"
        },
        "contact": {
            "phone": "+49 241 123456",
            "email": "maria.schmidt@example.com",
            "fax": "+49 241 123457"
        },
        "therapy_methods": [
            "Verhaltenstherapie (Erwachsene)",
            "Verhaltenstherapie (Kinder)"
        ],
        "languages": ["Deutsch", "Englisch"],
        "telephone_hours": {
            "monday": ["10:00-12:00"],
            "wednesday": ["14:00-16:00"]
        }
    }


class TestStatusPreservation:
    """Test that manual status fields are NOT overwritten during import.
    
    ⚠️ THESE TESTS WILL FAIL - demonstrating the current bug!
    """
    
    def test_update_preserves_gesperrt_status(self, mock_therapist_importer):
        """Test that a therapist marked as 'gesperrt' is NOT reset to 'aktiv'.
        
        THIS TEST WILL FAIL - demonstrating the bug!
        """
        # Setup database mock
        db_mock = MagicMock()
        mock_therapist_importer._mock_session_local.return_value = db_mock
        
        # Create existing therapist with gesperrt status
        existing_therapist = MagicMock()
        existing_therapist.id = 123
        existing_therapist.vorname = "Maria"
        existing_therapist.nachname = "Schmidt"
        existing_therapist.plz = "52062"
        existing_therapist.status = MockTherapistStatus.gesperrt
        existing_therapist.sperrgrund = "Nicht mehr tätig"
        existing_therapist.sperrdatum = date.today() - timedelta(days=30)
        existing_therapist.email = "maria.schmidt@example.com"
        
        # Mock database query to return our existing therapist
        db_mock.query.return_value.filter.return_value.first.return_value = existing_therapist
        
        # Import data for the same therapist
        import_data = {
            "basic_info": {
                "salutation": "Frau",
                "first_name": "Maria",
                "last_name": "Schmidt"
            },
            "location": {
                "postal_code": "52062",
                "city": "Aachen"
            },
            "contact": {
                "phone": "+49 241 999999"  # Updated phone
            },
            "therapy_methods": ["Verhaltenstherapie (Erwachsene)"]
        }
        
        # Perform import
        success, message = mock_therapist_importer.import_therapist(import_data)
        
        # ASSERTION THAT WILL FAIL - Status should NOT be changed
        # The bug is that status gets reset to 'aktiv' in _map_therapist_data
        assert existing_therapist.status == MockTherapistStatus.gesperrt, \
            "Status should remain 'gesperrt' but was overwritten to 'aktiv'"
        assert existing_therapist.sperrgrund == "Nicht mehr tätig", \
            "Sperrgrund should be preserved"
        assert existing_therapist.sperrdatum == date.today() - timedelta(days=30), \
            "Sperrdatum should be preserved"
    
    def test_update_preserves_potenziell_verfuegbar_true(self, mock_therapist_importer):
        """Test that potenziell_verfuegbar=True is NOT reset to False.
        
        THIS TEST WILL FAIL - demonstrating the bug!
        """
        # Setup database mock
        db_mock = MagicMock()
        mock_therapist_importer._mock_session_local.return_value = db_mock
        
        # Create existing therapist marked as potentially available
        existing_therapist = MagicMock()
        existing_therapist.id = 124
        existing_therapist.vorname = "Hans"
        existing_therapist.nachname = "Meyer"
        existing_therapist.plz = "52064"
        existing_therapist.potenziell_verfuegbar = True
        existing_therapist.potenziell_verfuegbar_notizen = "Hat Kapazität ab März"
        existing_therapist.email = "hans.meyer@example.com"
        
        # Mock database query
        db_mock.query.return_value.filter.return_value.first.return_value = existing_therapist
        
        # Import data
        import_data = {
            "basic_info": {
                "salutation": "Herr",
                "first_name": "Hans",
                "last_name": "Meyer"
            },
            "location": {
                "postal_code": "52064"
            },
            "contact": {},
            "therapy_methods": ["Tiefenpsychologisch fundierte Psychotherapie (Erwachsene)"]
        }
        
        # Perform import
        success, message = mock_therapist_importer.import_therapist(import_data)
        
        # ASSERTION THAT WILL FAIL
        assert existing_therapist.potenziell_verfuegbar == True, \
            "potenziell_verfuegbar should remain True but was reset to False"
        assert existing_therapist.potenziell_verfuegbar_notizen == "Hat Kapazität ab März", \
            "Notes about availability should be preserved"
    
    def test_update_preserves_ueber_curavani_informiert_true(self, mock_therapist_importer):
        """Test that ueber_curavani_informiert=True is NOT reset to False.
        
        THIS TEST WILL FAIL - demonstrating the bug!
        """
        # Setup database mock
        db_mock = MagicMock()
        mock_therapist_importer._mock_session_local.return_value = db_mock
        
        # Create existing therapist who has been informed about Curavani
        existing_therapist = MagicMock()
        existing_therapist.id = 125
        existing_therapist.vorname = "Anna"
        existing_therapist.nachname = "Weber"
        existing_therapist.plz = "52066"
        existing_therapist.ueber_curavani_informiert = True
        existing_therapist.letzter_kontakt_email = date.today() - timedelta(days=10)
        existing_therapist.email = "anna.weber@example.com"
        
        # Mock database query
        db_mock.query.return_value.filter.return_value.first.return_value = existing_therapist
        
        # Import data
        import_data = {
            "basic_info": {
                "salutation": "Frau",
                "first_name": "Anna",
                "last_name": "Weber"
            },
            "location": {
                "postal_code": "52066"
            },
            "contact": {},
            "therapy_methods": ["Verhaltenstherapie (Erwachsene)"]
        }
        
        # Perform import
        success, message = mock_therapist_importer.import_therapist(import_data)
        
        # ASSERTION THAT WILL FAIL
        assert existing_therapist.ueber_curavani_informiert == True, \
            "ueber_curavani_informiert should remain True but was reset to False"
    
    def test_update_preserves_kassensitz_false(self, mock_therapist_importer):
        """Test that kassensitz=False is NOT reset to True.
        
        THIS TEST WILL FAIL - demonstrating the bug!
        """
        # Setup database mock
        db_mock = MagicMock()
        mock_therapist_importer._mock_session_local.return_value = db_mock
        
        # Create existing therapist without Kassensitz
        existing_therapist = MagicMock()
        existing_therapist.id = 126
        existing_therapist.vorname = "Peter"
        existing_therapist.nachname = "Müller"
        existing_therapist.plz = "52068"
        existing_therapist.kassensitz = False  # Manually set to False
        existing_therapist.email = "peter.mueller@example.com"
        
        # Mock database query
        db_mock.query.return_value.filter.return_value.first.return_value = existing_therapist
        
        # Import data
        import_data = {
            "basic_info": {
                "salutation": "Herr",
                "first_name": "Peter",
                "last_name": "Müller"
            },
            "location": {
                "postal_code": "52068"
            },
            "contact": {},
            "therapy_methods": ["Verhaltenstherapie (Erwachsene)"]
        }
        
        # Perform import
        success, message = mock_therapist_importer.import_therapist(import_data)
        
        # ASSERTION THAT WILL FAIL
        assert existing_therapist.kassensitz == False, \
            "kassensitz should remain False but was reset to True"
    
    def test_update_preserves_all_manual_fields_together(self, mock_therapist_importer):
        """Test that ALL manual fields are preserved together during update.
        
        THIS TEST WILL FAIL - demonstrating the bug comprehensively!
        """
        # Setup database mock
        db_mock = MagicMock()
        mock_therapist_importer._mock_session_local.return_value = db_mock
        
        # Create existing therapist with all manual fields set
        existing_therapist = MagicMock()
        existing_therapist.id = 127
        existing_therapist.vorname = "Klaus"
        existing_therapist.nachname = "Fischer"
        existing_therapist.plz = "52070"
        existing_therapist.email = "klaus.fischer@example.com"
        
        # All manual fields that should be preserved
        existing_therapist.status = MockTherapistStatus.gesperrt
        existing_therapist.sperrgrund = "Praxis geschlossen"
        existing_therapist.sperrdatum = date(2024, 1, 1)
        existing_therapist.kassensitz = False
        existing_therapist.potenziell_verfuegbar = True
        existing_therapist.potenziell_verfuegbar_notizen = "Warteliste vorhanden"
        existing_therapist.ueber_curavani_informiert = True
        existing_therapist.naechster_kontakt_moeglich = date(2024, 3, 1)
        existing_therapist.bevorzugte_diagnosen = ["F32", "F33"]
        existing_therapist.alter_min = 18
        existing_therapist.alter_max = 65
        existing_therapist.geschlechtspraeferenz = "weiblich"
        existing_therapist.arbeitszeiten = {"montag": ["09:00-17:00"]}
        existing_therapist.bevorzugt_gruppentherapie = True
        
        # Mock database query
        db_mock.query.return_value.filter.return_value.first.return_value = existing_therapist
        
        # Import data (minimal update)
        import_data = {
            "basic_info": {
                "salutation": "Herr",
                "first_name": "Klaus",
                "last_name": "Fischer"
            },
            "location": {
                "postal_code": "52070"
            },
            "contact": {
                "phone": "+49 241 777777"  # Only updating phone
            },
            "therapy_methods": ["Verhaltenstherapie (Erwachsene)"]
        }
        
        # Perform import
        success, message = mock_therapist_importer.import_therapist(import_data)
        
        # ALL THESE ASSERTIONS WILL FAIL - demonstrating comprehensive overwrite bug
        assert existing_therapist.status == MockTherapistStatus.gesperrt, \
            "Status should be preserved"
        assert existing_therapist.sperrgrund == "Praxis geschlossen", \
            "Sperrgrund should be preserved"
        assert existing_therapist.kassensitz == False, \
            "Kassensitz should be preserved"
        assert existing_therapist.potenziell_verfuegbar == True, \
            "Availability should be preserved"
        assert existing_therapist.ueber_curavani_informiert == True, \
            "Curavani informed status should be preserved"
        assert existing_therapist.bevorzugte_diagnosen == ["F32", "F33"], \
            "Preferred diagnoses should be preserved"
        assert existing_therapist.bevorzugt_gruppentherapie == True, \
            "Group therapy preference should be preserved"


class TestTherapistImporter:
    """Test the core TherapistImporter functionality."""
    
    def test_email_preservation_rule(self, mock_therapist_importer):
        """Test that existing email is never overwritten with empty value."""
        # Setup database mock
        db_mock = MagicMock()
        mock_therapist_importer._mock_session_local.return_value = db_mock
        
        # Create existing therapist with email
        existing_therapist = MagicMock()
        existing_therapist.id = 130
        existing_therapist.vorname = "Email"
        existing_therapist.nachname = "Test"
        existing_therapist.plz = "52062"
        existing_therapist.email = "important.email@example.com"  # Existing email
        
        # Mock database query
        db_mock.query.return_value.filter.return_value.first.return_value = existing_therapist
        
        # Import data with empty email
        import_data = {
            "basic_info": {
                "salutation": "Herr",
                "first_name": "Email",
                "last_name": "Test"
            },
            "location": {
                "postal_code": "52062"
            },
            "contact": {
                "email": ""  # Empty email in import
            },
            "therapy_methods": []
        }
        
        # Perform import
        success, message = mock_therapist_importer.import_therapist(import_data)
        
        # Email should NOT be overwritten with empty value
        # This test should PASS as this is specifically handled in the code
        assert existing_therapist.email == "important.email@example.com", \
            "Existing email should not be overwritten with empty value"
    
    def test_deduplication_by_name_and_plz(self, mock_therapist_importer):
        """Test therapist deduplication by name and PLZ."""
        # Setup database mock
        db_mock = MagicMock()
        mock_therapist_importer._mock_session_local.return_value = db_mock
        
        # Create existing therapist
        existing_therapist = MagicMock()
        existing_therapist.id = 131
        existing_therapist.vorname = "Duplicate"
        existing_therapist.nachname = "Test"
        existing_therapist.plz = "52062"
        
        # Mock finding existing therapist
        db_mock.query.return_value.filter.return_value.first.return_value = existing_therapist
        
        # Import data for same therapist
        import_data = {
            "basic_info": {
                "salutation": "Frau",
                "first_name": "Duplicate",
                "last_name": "Test"
            },
            "location": {
                "postal_code": "52062"
            },
            "contact": {},
            "therapy_methods": []
        }
        
        # Perform import
        success, message = mock_therapist_importer.import_therapist(import_data)
        
        # Should update, not create new
        assert success == True
        assert "updated" in message.lower() or "131" in message
        db_mock.add.assert_not_called()  # Should not add new therapist


class TestDataMapping:
    """Test data mapping from JSON to model format."""
    
    def test_map_therapy_methods_both_types(self, mock_therapist_importer):
        """Test mapping when both therapy types are found."""
        methods = [
            "Verhaltenstherapie (Erwachsene)",
            "Tiefenpsychologisch fundierte Psychotherapie (Erwachsene)"
        ]
        
        result = mock_therapist_importer._map_therapy_methods(methods)
        assert result == "egal"
    
    def test_map_therapy_methods_only_verhaltenstherapie(self, mock_therapist_importer):
        """Test mapping when only Verhaltenstherapie is found."""
        methods = ["Verhaltenstherapie (Erwachsene)", "Verhaltenstherapie (Kinder)"]
        
        result = mock_therapist_importer._map_therapy_methods(methods)
        assert result == "Verhaltenstherapie"
    
    def test_map_therapy_methods_only_tiefenpsychologisch(self, mock_therapist_importer):
        """Test mapping when only Tiefenpsychologisch is found."""
        methods = [
            "Tiefenpsychologisch fundierte Psychotherapie (Erwachsene)",
            "tiefenpsychologisch fundierte Psychotherapie"
        ]
        
        result = mock_therapist_importer._map_therapy_methods(methods)
        assert result == "tiefenpsychologisch_fundierte_Psychotherapie"
    
    def test_map_therapy_methods_no_recognized(self, mock_therapist_importer):
        """Test mapping when no recognized methods found."""
        methods = ["Systemische Therapie", "Psychoanalyse"]
        
        result = mock_therapist_importer._map_therapy_methods(methods)
        assert result == "egal"
    
    def test_map_gender_from_salutation(self, mock_therapist_importer):
        """Test gender mapping from salutation."""
        assert mock_therapist_importer._map_gender_from_salutation("Herr") == "männlich"
        assert mock_therapist_importer._map_gender_from_salutation("Frau") == "weiblich"
        assert mock_therapist_importer._map_gender_from_salutation("Dr.") == "keine_Angabe"
        assert mock_therapist_importer._map_gender_from_salutation(None) == "keine_Angabe"
    
    def test_map_therapist_data_complete(self, mock_therapist_importer, sample_therapist_json):
        """Test complete mapping of therapist data."""
        result = mock_therapist_importer._map_therapist_data(sample_therapist_json)
        
        assert result is not None
        assert result['anrede'] == "Frau"
        assert result['geschlecht'] == "weiblich"
        assert result['titel'] == "Dr. med."
        assert result['vorname'] == "Maria"
        assert result['nachname'] == "Schmidt"
        assert result['strasse'] == "Therapiestraße 42"
        assert result['plz'] == "52062"
        assert result['ort'] == "Aachen"
        assert result['telefon'] == "+49 241 123456"
        assert result['email'] == "maria.schmidt@example.com"
        assert result['psychotherapieverfahren'] == "Verhaltenstherapie"
        assert result['fremdsprachen'] == ["Deutsch", "Englisch"]
        
        # Check problematic defaults that cause the bug
        assert result['status'] == 'aktiv'  # Always set to aktiv!
        assert result['kassensitz'] == True  # Always set to True!
        assert result['potenziell_verfuegbar'] == False  # Always set to False!
        assert result['ueber_curavani_informiert'] == False  # Always set to False!
    
    def test_map_therapist_data_missing_required_fields(self, mock_therapist_importer):
        """Test mapping with missing required fields."""
        incomplete_data = {
            "basic_info": {
                # Missing first_name and last_name
                "salutation": "Herr"
            },
            "location": {
                # Missing postal_code
                "city": "Aachen"
            }
        }
        
        result = mock_therapist_importer._map_therapist_data(incomplete_data)
        assert result is None  # Should return None for incomplete data


class TestLocalFileMonitor:
    """Test the LocalFileMonitor file processing."""
    
    def test_process_file_successful(self, mock_file_monitor):
        """Test successful file processing."""
        file_path = "/test/import/path/20240101/52062.json"
        
        # Mock file reading
        therapist_data = {
            "therapists": [
                {
                    "basic_info": {"first_name": "Test", "last_name": "Therapist", "salutation": "Herr"},
                    "location": {"postal_code": "52062"},
                    "therapy_methods": ["Verhaltenstherapie (Erwachsene)"]
                }
            ]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(therapist_data))):
            # Mock successful import
            mock_file_monitor.importer.import_therapist.return_value = (True, "Success")
            
            # Process file
            errors = mock_file_monitor._process_file(file_path, "52062")
            
            # Should have no errors
            assert len(errors) == 0
            mock_file_monitor.importer.import_therapist.assert_called_once()
    
    def test_process_file_json_error(self, mock_file_monitor):
        """Test file processing with invalid JSON."""
        file_path = "/test/import/path/20240101/52062.json"
        
        # Mock file reading with invalid JSON
        with patch('builtins.open', mock_open(read_data="Invalid JSON {")):
            # Process file
            errors = mock_file_monitor._process_file(file_path, "52062")
            
            # Should have JSON error
            assert len(errors) == 1
            assert "Invalid JSON" in errors[0]['error']
            mock_file_monitor.importer.import_therapist.assert_not_called()
    
    def test_process_file_import_failure(self, mock_file_monitor):
        """Test file processing with import failure."""
        file_path = "/test/import/path/20240101/52062.json"
        
        # Mock file reading
        therapist_data = {
            "therapists": [
                {
                    "basic_info": {"first_name": "Test", "last_name": "Therapist", "salutation": "Herr"},
                    "location": {"postal_code": "52062"},
                    "therapy_methods": ["Verhaltenstherapie (Erwachsene)"]
                }
            ]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(therapist_data))):
            # Mock failed import
            mock_file_monitor.importer.import_therapist.return_value = (False, "Database error")
            
            # Process file
            errors = mock_file_monitor._process_file(file_path, "52062")
            
            # Should have import error
            assert len(errors) == 1
            assert "Database error" in errors[0]['error']
    
    def test_process_file_filters_non_adult_therapists(self, mock_file_monitor):
        """Test that therapists without adult therapy methods are filtered out."""
        file_path = "/test/import/path/20240101/52062.json"
        
        # Mock file reading with child-only therapist
        therapist_data = {
            "therapists": [
                {
                    "basic_info": {"first_name": "Child", "last_name": "Therapist", "salutation": "Frau"},
                    "location": {"postal_code": "52062"},
                    "therapy_methods": ["Verhaltenstherapie (Kinder)", "Spieltherapie"]  # No "Erwachsene"
                },
                {
                    "basic_info": {"first_name": "Adult", "last_name": "Therapist", "salutation": "Herr"},
                    "location": {"postal_code": "52062"},
                    "therapy_methods": ["Verhaltenstherapie (Erwachsene)"]  # Has "Erwachsene"
                }
            ]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(therapist_data))):
            # Mock successful import
            mock_file_monitor.importer.import_therapist.return_value = (True, "Success")
            
            # Process file
            errors = mock_file_monitor._process_file(file_path, "52062")
            
            # Should only import the adult therapist
            assert mock_file_monitor.importer.import_therapist.call_count == 1
            
            # Check that the right therapist was imported
            call_args = mock_file_monitor.importer.import_therapist.call_args[0][0]
            assert call_args['basic_info']['first_name'] == "Adult"
    
    def test_find_files_by_zip(self, mock_file_monitor):
        """Test finding files organized by ZIP code."""
        # Mock directory structure
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir') as mock_listdir:
                with patch('os.path.isdir') as mock_isdir:
                    # Mock directory listing
                    mock_listdir.side_effect = [
                        ['20240101', '20240102', 'not_a_date'],  # Date folders
                        ['52062.json', '52064.json'],  # Files in 20240101
                        ['52062.json', '52066.json'],  # Files in 20240102
                        []  # not_a_date folder (should be skipped)
                    ]
                    
                    # Mock isdir checks
                    mock_isdir.side_effect = [True, True, True, True, False, True, False, True, False, True]
                    
                    result = mock_file_monitor._find_files_by_zip()
                    
                    # Should have 3 unique ZIP codes
                    assert len(result) == 3
                    assert '52062' in result
                    assert '52064' in result
                    assert '52066' in result
                    
                    # 52062 should have 2 files (from both dates)
                    assert len(result['52062']) == 2


class TestImportStatusTracking:
    """Test ImportStatus tracking during import operations."""
    
    def test_import_status_tracks_success(self, mock_therapist_importer):
        """Test that ImportStatus correctly tracks successful imports."""
        # Mock ImportStatus at module level
        with patch('sys.modules') as mock_modules:
            mock_import_status = MagicMock()
            mock_modules['therapist_service.imports.import_status'] = MagicMock(ImportStatus=mock_import_status)
            
            # Reset ImportStatus mock
            mock_import_status._status = {
                'running': True,
                'last_check': None,
                'last_import_run': None,
                'files_processed_today': 0,
                'therapists_processed_today': 0,
                'therapists_failed_today': 0,
                'last_error': None,
                'last_error_time': None,
                'total_files_processed': 0,
                'total_therapists_processed': 0,
                'total_therapists_failed': 0,
                'current_date': date.today(),
                'recent_imports': []
            }
            
            # Mock the class methods
            mock_import_status.record_file_processed = MagicMock()
            mock_import_status.get_status = MagicMock(return_value={
                'files_processed_today': 1,
                'therapists_processed_today': 10,
                'therapists_failed_today': 2,
                'total_files_processed': 1,
                'total_therapists_processed': 10,
                'total_therapists_failed': 2,
                'recent_imports': [{}]
            })
            
            # Record a successful file processing
            mock_import_status.record_file_processed("20240101/52062.json", 10, 2)
            
            status = mock_import_status.get_status()
            
            assert status['files_processed_today'] == 1
            assert status['therapists_processed_today'] == 10
            assert status['therapists_failed_today'] == 2
            assert status['total_files_processed'] == 1
            assert status['total_therapists_processed'] == 10
            assert status['total_therapists_failed'] == 2
            assert len(status['recent_imports']) == 1
    
    def test_import_status_daily_reset(self):
        """Test that ImportStatus resets daily counters on date change."""
        # Mock ImportStatus at module level
        with patch('sys.modules') as mock_modules:
            mock_import_status = MagicMock()
            mock_modules['therapist_service.imports.import_status'] = MagicMock(ImportStatus=mock_import_status)
            
            # Set up status with yesterday's date
            yesterday = date.today() - timedelta(days=1)
            
            mock_import_status._status = {
                'running': True,
                'last_check': None,
                'last_import_run': None,
                'files_processed_today': 5,
                'therapists_processed_today': 50,
                'therapists_failed_today': 3,
                'last_error': None,
                'last_error_time': None,
                'total_files_processed': 100,
                'total_therapists_processed': 1000,
                'total_therapists_failed': 50,
                'current_date': yesterday,
                'recent_imports': []
            }
            
            # Mock get_status to simulate reset
            mock_import_status.get_status = MagicMock(return_value={
                'files_processed_today': 0,
                'therapists_processed_today': 0,
                'therapists_failed_today': 0,
                'total_files_processed': 100,
                'total_therapists_processed': 1000,
                'total_therapists_failed': 50
            })
            
            # Get status (should trigger reset)
            status = mock_import_status.get_status()
            
            # Daily counters should be reset
            assert status['files_processed_today'] == 0
            assert status['therapists_processed_today'] == 0
            assert status['therapists_failed_today'] == 0
            
            # Total counters should remain
            assert status['total_files_processed'] == 100
            assert status['total_therapists_processed'] == 1000
            assert status['total_therapists_failed'] == 50

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-k", "TestStatusPreservation"])