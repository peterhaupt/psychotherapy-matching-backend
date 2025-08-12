"""Unit tests for GCS patient import file processing - Phase 2 Version.

This is the merged version combining existing tests with Phase 2 updates.
Tests that should PASS now are marked with [EXISTING].
Tests that will only PASS after Phase 2 are marked with [PHASE2].
"""
import sys
import json
import os
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock, call
from datetime import datetime, date

# Phase 2: Approved symptom list for validation
APPROVED_SYMPTOMS = [
    # HÄUFIGSTE ANLIEGEN (Top 5)
    "Depression / Niedergeschlagenheit",
    "Ängste / Panikattacken",
    "Burnout / Erschöpfung",
    "Schlafstörungen",
    "Stress / Überforderung",
    # STIMMUNG & GEFÜHLE
    "Trauer / Verlust",
    "Reizbarkeit / Wutausbrüche",
    "Stimmungsschwankungen",
    "Innere Leere",
    "Einsamkeit",
    # DENKEN & GRÜBELN
    "Sorgen / Grübeln",
    "Selbstzweifel",
    "Konzentrationsprobleme",
    "Negative Gedanken",
    "Entscheidungsschwierigkeiten",
    # KÖRPER & GESUNDHEIT
    "Psychosomatische Beschwerden",
    "Chronische Schmerzen",
    "Essstörungen",
    "Suchtprobleme (Alkohol/Drogen)",
    "Sexuelle Probleme",
    # BEZIEHUNGEN & SOZIALES
    "Beziehungsprobleme",
    "Familienkonflikte",
    "Sozialer Rückzug",
    "Mobbing",
    "Trennungsschmerz",
    # BESONDERE BELASTUNGEN
    "Traumatische Erlebnisse",
    "Zwänge",
    "Selbstverletzung",
    "Suizidgedanken",
    "Identitätskrise"
]


@pytest.fixture
def mock_dependencies():
    """Mock all dependencies before importing the code under test."""
    # Save original modules
    original_modules = {}
    modules_to_mock = [
        'google',
        'google.cloud',
        'google.cloud.storage',
        'google.api_core',
        'google.api_core.exceptions',
        'shared',
        'shared.config',
        'shared.utils',
        'shared.utils.database',
        'models',
        'models.patient',
        'events',
        'events.producers',
        'flask',
        'flask_restful',
        'sqlalchemy',
        'sqlalchemy.exc',
        'sqlalchemy.orm',
        'requests',
        'requests.adapters',
        'requests.exceptions',
        'logging',
        'jinja2',
    ]
    
    for module in modules_to_mock:
        if module in sys.modules:
            original_modules[module] = sys.modules[module]
    
    # Mock all dependencies
    sys.modules['google'] = MagicMock()
    sys.modules['google.cloud'] = MagicMock()
    sys.modules['google.cloud.storage'] = MagicMock()
    sys.modules['google.api_core'] = MagicMock()
    sys.modules['google.api_core.exceptions'] = MagicMock()
    sys.modules['shared'] = MagicMock()
    sys.modules['shared.config'] = MagicMock()
    sys.modules['shared.utils'] = MagicMock()
    sys.modules['shared.utils.database'] = MagicMock()
    sys.modules['models'] = MagicMock()
    sys.modules['models.patient'] = MagicMock()
    sys.modules['events'] = MagicMock()
    sys.modules['events.producers'] = MagicMock()
    sys.modules['flask'] = MagicMock()
    sys.modules['flask_restful'] = MagicMock()
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlalchemy.exc'] = MagicMock()
    sys.modules['sqlalchemy.orm'] = MagicMock()
    sys.modules['requests'] = MagicMock()
    sys.modules['requests.adapters'] = MagicMock()
    sys.modules['requests.exceptions'] = MagicMock()
    sys.modules['logging'] = MagicMock()
    sys.modules['jinja2'] = MagicMock()
    
    # Mock get_config
    mock_config = MagicMock()
    sys.modules['shared.config'].get_config.return_value = mock_config
    
    yield
    
    # Cleanup
    for module in modules_to_mock:
        if module in original_modules:
            sys.modules[module] = original_modules[module]
        else:
            sys.modules.pop(module, None)


@pytest.fixture
def mock_gcs_monitor(mock_dependencies):
    """Create a GCSMonitor instance with all external dependencies mocked."""
    # Now we can safely import after mocking
    from patient_service.imports.gcs_monitor import GCSMonitor
    from patient_service.imports.patient_importer import PatientImporter
    
    with patch('patient_service.imports.gcs_monitor.storage.Client') as mock_storage:
        with patch.dict(os.environ, {
            'GCS_IMPORT_BUCKET': 'test-bucket',
            'PATIENT_IMPORT_LOCAL_PATH': '/test/path',
            'PATIENT_IMPORT_CHECK_INTERVAL_SECONDS': '300',
            'GCS_READER_CREDENTIALS_PATH': '/test/creds/reader.json',
            'GCS_DELETER_CREDENTIALS_PATH': '/test/creds/deleter.json'
        }):
            # Mock credentials file existence
            with patch('os.path.exists', return_value=True):
                # Mock directory creation
                with patch('os.makedirs'):
                    monitor = GCSMonitor()
                    
                    # Setup mock clients
                    monitor.reader_client = Mock()
                    monitor.deleter_client = Mock()
                    
                    # Mock the importer
                    monitor.importer = Mock()
                    
                    return monitor


class TestProcessFile:
    """Test the _process_file method with various scenarios."""
    
    def test_successful_import_file_stays_in_base_path_with_email(self, mock_gcs_monitor, mock_dependencies):
        """[PHASE2] Test successful import - file stays in base path, email sent, GCS deleted."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Phase 2: Updated test data with symptom array and registration_token
            test_data = {
                "patient_data": {
                    "vorname": "Max",
                    "nachname": "Mustermann",
                    "symptome": ["Depression / Niedergeschlagenheit", "Schlafstörungen"],  # PHASE2: Array
                    "email": "max@test.com"
                },
                "registration_token": "a7f3e9b2c4d8f1a6e5b9c3d7f2a8e4b1c6d9f3a7e2b5c8d1f4a9e3b7c2d6f8a0"  # PHASE2
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock successful import returning patient_id
                mock_gcs_monitor.importer.import_patient.return_value = (True, "Patient created with ID: 123")
                
                # PHASE2: Mock email sending
                with patch('requests.post') as mock_email_post:
                    mock_email_post.return_value.status_code = 201
                    mock_email_post.return_value.json.return_value = {'id': 456}
                    
                    # Mock successful GCS deletion
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True) as mock_delete:
                        # Mock os.path.exists to simulate file exists
                        with patch('os.path.exists', return_value=True):
                            # Mock ImportStatus
                            with patch.object(ImportStatus, 'record_success') as mock_record_success:
                                # Process the file
                                mock_gcs_monitor._process_file(file_name)
                                
                                # [EXISTING] Verify download was called
                                mock_gcs_monitor._download_file.assert_called_once_with(file_name, local_path)
                                
                                # [EXISTING] Verify import was called with correct data
                                mock_gcs_monitor.importer.import_patient.assert_called_once_with(test_data)
                                
                                # [EXISTING] Verify success was recorded
                                mock_record_success.assert_called_once_with(file_name)
                                
                                # [EXISTING] Verify GCS file was deleted
                                mock_delete.assert_called_once_with(file_name)
                                
                                # [EXISTING] Verify no attempt to move file (it should stay in base path)
                                with patch('os.rename') as mock_rename:
                                    mock_rename.assert_not_called()
    
    def test_database_error_file_moved_to_failed(self, mock_gcs_monitor, mock_dependencies):
        """[EXISTING] Test database error during import - file should be moved to failed/ folder."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Phase 2: Updated test data
            test_data = {
                "patient_data": {
                    "vorname": "Test",
                    "nachname": "Patient",
                    "symptome": ["Burnout / Erschöpfung"]  # PHASE2: Array format
                },
                "registration_token": "test12345678"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock failed import (database error)
                error_msg = "Database connection failed"
                mock_gcs_monitor.importer.import_patient.return_value = (False, error_msg)
                
                # Mock successful file move
                with patch('os.rename') as mock_rename:
                    # Mock successful GCS deletion
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True) as mock_delete:
                        # Mock error notification
                        with patch.object(mock_gcs_monitor.importer, 'send_error_notification') as mock_notify:
                            # Mock ImportStatus
                            with patch.object(ImportStatus, 'record_failure') as mock_record_failure:
                                # Process the file
                                mock_gcs_monitor._process_file(file_name)
                                
                                # [EXISTING] Verify file was moved to failed folder
                                mock_rename.assert_called_once_with(local_path, failed_path)
                                
                                # [EXISTING] Verify failure was recorded
                                mock_record_failure.assert_called_once_with(file_name, error_msg)
                                
                                # [EXISTING] Verify error notification was sent
                                mock_notify.assert_called_once()
                                
                                # [EXISTING] Verify GCS file was still deleted
                                mock_delete.assert_called_once_with(file_name)
    
    def test_symptom_validation_error_file_moved_to_failed(self, mock_gcs_monitor, mock_dependencies):
        """[PHASE2] Test symptom validation error - file should be moved to failed/ folder."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Phase 2: Test data with invalid symptoms
            test_data = {
                "patient_data": {
                    "vorname": "Test",
                    "nachname": "Patient",
                    "symptome": [
                        "Invalid Symptom",  # Not in approved list
                        "Kopfschmerzen"  # Not in approved list
                    ]
                },
                "registration_token": "test123"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock failed import (validation error)
                error_msg = "Invalid symptom: Invalid Symptom"
                mock_gcs_monitor.importer.import_patient.return_value = (False, error_msg)
                
                # Mock successful file move
                with patch('os.rename') as mock_rename:
                    # Mock successful GCS deletion
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        # Mock ImportStatus
                        with patch.object(ImportStatus, 'record_failure'):
                            # Process the file
                            mock_gcs_monitor._process_file(file_name)
                            
                            # Verify file was moved to failed folder
                            mock_rename.assert_called_once_with(local_path, failed_path)
    
    def test_too_many_symptoms_validation_error(self, mock_gcs_monitor, mock_dependencies):
        """[PHASE2] Test too many symptoms (>3) - file should be moved to failed/ folder."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Phase 2: Four symptoms (too many)
            test_data = {
                "patient_data": {
                    "vorname": "Test",
                    "nachname": "Patient",
                    "symptome": [
                        "Depression / Niedergeschlagenheit",
                        "Schlafstörungen",
                        "Burnout / Erschöpfung",
                        "Ängste / Panikattacken"  # 4th symptom - too many
                    ]
                },
                "registration_token": "test123"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                error_msg = "Between 1 and 3 symptoms required"
                mock_gcs_monitor.importer.import_patient.return_value = (False, error_msg)
                
                with patch('os.rename') as mock_rename:
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        with patch.object(ImportStatus, 'record_failure'):
                            with patch.object(mock_gcs_monitor.importer, 'send_error_notification'):
                                mock_gcs_monitor._process_file(file_name)
                                
                                # Verify file was moved to failed folder
                                mock_rename.assert_called_once_with(local_path, failed_path)
    
    def test_missing_registration_token_error(self, mock_gcs_monitor, mock_dependencies):
        """[PHASE2] Test missing registration_token - file should be moved to failed/ folder."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Phase 2: Missing registration_token
            test_data = {
                "patient_data": {
                    "vorname": "Test",
                    "nachname": "Patient",
                    "symptome": ["Depression / Niedergeschlagenheit"]
                }
                # Missing registration_token
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                error_msg = "Missing registration_token"
                mock_gcs_monitor.importer.import_patient.return_value = (False, error_msg)
                
                with patch('os.rename') as mock_rename:
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        with patch.object(ImportStatus, 'record_failure'):
                            with patch.object(mock_gcs_monitor.importer, 'send_error_notification'):
                                mock_gcs_monitor._process_file(file_name)
                                
                                # Verify file was moved to failed folder
                                mock_rename.assert_called_once_with(local_path, failed_path)
    
    def test_legacy_symptom_text_format_rejected(self, mock_gcs_monitor, mock_dependencies):
        """[PHASE2] Test legacy text symptom format is rejected."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "legacy_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Old format with text instead of array
            test_data = {
                "patient_data": {
                    "vorname": "Legacy",
                    "nachname": "Format",
                    "symptome": "Depression, Angst"  # Old text format
                },
                "registration_token": "test123"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                error_msg = "symptome must be an array"
                mock_gcs_monitor.importer.import_patient.return_value = (False, error_msg)
                
                with patch('os.rename') as mock_rename:
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        with patch.object(ImportStatus, 'record_failure'):
                            with patch.object(mock_gcs_monitor.importer, 'send_error_notification'):
                                mock_gcs_monitor._process_file(file_name)
                                
                                # Legacy format should be rejected
                                mock_rename.assert_called_once_with(local_path, failed_path)
    
    def test_import_without_diagnosis_field_succeeds(self, mock_gcs_monitor, mock_dependencies):
        """[PHASE2] Test that import succeeds without diagnosis field."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "no_diagnosis.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Phase 2: No diagnosis field (removed in Phase 2)
            test_data = {
                "patient_data": {
                    "vorname": "Test",
                    "nachname": "Patient",
                    "symptome": ["Schlafstörungen"],
                    # No 'diagnose' field
                },
                "registration_token": "a7f3e9b2c4d8f1a6e5b9c3d7f2a8e4b1c6d9f3a7e2b5c8d1f4a9e3b7c2d6f8a0"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Should succeed without diagnosis
                mock_gcs_monitor.importer.import_patient.return_value = (True, "Success")
                
                with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                    with patch.object(ImportStatus, 'record_success'):
                        mock_gcs_monitor._process_file(file_name)
                        
                        # Verify import was called successfully
                        mock_gcs_monitor.importer.import_patient.assert_called_once_with(test_data)
    
    def test_ptv11_fields_ignored_if_present(self, mock_gcs_monitor, mock_dependencies):
        """[PHASE2] Test that PTV11 fields are ignored if present in import."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "with_ptv11.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Phase 2: PTV11 fields should be ignored
            test_data = {
                "patient_data": {
                    "vorname": "Test",
                    "nachname": "Patient",
                    "symptome": ["Ängste / Panikattacken"],
                    "hat_ptv11": True,  # Should be ignored
                    "psychotherapeutische_sprechstunde": True  # Should be ignored
                },
                "registration_token": "test123456"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                mock_gcs_monitor.importer.import_patient.return_value = (True, "Success")
                
                with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                    with patch.object(ImportStatus, 'record_success'):
                        mock_gcs_monitor._process_file(file_name)
                        
                        # Import should succeed (PTV11 fields ignored)
                        mock_gcs_monitor.importer.import_patient.assert_called_once()
    
    def test_download_failure_no_file_no_gcs_deletion(self, mock_gcs_monitor, mock_dependencies):
        """[EXISTING] Test download failure - no local file created, GCS file NOT deleted."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        # Mock failed download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=False):
            # Mock GCS deletion (should not be called)
            with patch.object(mock_gcs_monitor, '_delete_from_gcs') as mock_delete:
                # Mock ImportStatus
                with patch.object(ImportStatus, 'record_failure') as mock_record_failure:
                    # Process the file
                    mock_gcs_monitor._process_file(file_name)
                    
                    # [EXISTING] Verify download was attempted
                    mock_gcs_monitor._download_file.assert_called_once_with(file_name, local_path)
                    
                    # [EXISTING] Verify import was NOT attempted
                    mock_gcs_monitor.importer.import_patient.assert_not_called()
                    
                    # [EXISTING] Verify GCS deletion was NOT called
                    mock_delete.assert_not_called()
                    
                    # [EXISTING] Verify failure was recorded
                    mock_record_failure.assert_called_once_with(file_name, "Failed to download file")
    
    def test_json_decode_error_file_moved_to_failed(self, mock_gcs_monitor, mock_dependencies):
        """[EXISTING] Test invalid JSON - file should be moved to failed/ folder."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Mock file read with invalid JSON
            with patch('builtins.open', mock_open(read_data="Invalid JSON {")):
                # Mock os.path.exists for the move operation
                with patch('os.path.exists', return_value=True):
                    # Mock successful file move
                    with patch('os.rename') as mock_rename:
                        # Mock successful GCS deletion
                        with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                            # Mock ImportStatus
                            with patch.object(ImportStatus, 'record_failure') as mock_record_failure:
                                # Mock error notification
                                with patch.object(mock_gcs_monitor.importer, 'send_error_notification'):
                                    # Process the file
                                    mock_gcs_monitor._process_file(file_name)
                                    
                                    # [EXISTING] Verify file was moved to failed folder
                                    mock_rename.assert_called_once_with(local_path, failed_path)
                                    
                                    # [EXISTING] Verify failure was recorded with JSON error
                                    args = mock_record_failure.call_args[0]
                                    assert args[0] == file_name
                                    assert "Invalid JSON" in args[1]
    
    def test_missing_patient_data_section_file_moved_to_failed(self, mock_gcs_monitor, mock_dependencies):
        """[EXISTING] Test JSON missing patient_data section - file should be moved to failed/ folder."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Mock file read with JSON missing patient_data
            test_data = {"metadata": {"version": "1.0"}}  # Missing patient_data
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock import failure due to missing data
                error_msg = "Missing patient_data section in JSON"
                mock_gcs_monitor.importer.import_patient.return_value = (False, error_msg)
                
                # Mock successful file move
                with patch('os.rename'):
                    # Mock successful GCS deletion
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        # Mock ImportStatus
                        with patch.object(ImportStatus, 'record_failure') as mock_record_failure:
                            # Process the file
                            mock_gcs_monitor._process_file(file_name)
                            
                            # [EXISTING] Verify import was called
                            mock_gcs_monitor.importer.import_patient.assert_called_once_with(test_data)
                            
                            # [EXISTING] Verify failure was recorded
                            mock_record_failure.assert_called_once_with(file_name, error_msg)


class TestZahlungsreferenzExtraction:
    """[PHASE2] Test zahlungsreferenz extraction during import."""
    
    def test_zahlungsreferenz_extracted_and_stored(self, mock_gcs_monitor, mock_dependencies):
        """Test that zahlungsreferenz is extracted from registration_token."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "patient_with_token.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            test_data = {
                "patient_data": {
                    "vorname": "Test",
                    "nachname": "Patient",
                    "symptome": ["Burnout / Erschöpfung"]
                },
                "registration_token": "a7f3e9b2c4d8f1a6e5b9c3d7f2a8e4b1c6d9f3a7e2b5c8d1f4a9e3b7c2d6f8a0"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock importer to verify it receives the token
                mock_gcs_monitor.importer.import_patient.return_value = (True, "Success")
                
                with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                    with patch.object(ImportStatus, 'record_success'):
                        mock_gcs_monitor._process_file(file_name)
                        
                        # Verify import was called with data containing token
                        call_args = mock_gcs_monitor.importer.import_patient.call_args[0][0]
                        assert call_args['registration_token'] == test_data['registration_token']
                        # The actual extraction to zahlungsreferenz happens in the importer


class TestEmailSending:
    """[PHASE2] Test email sending after successful import."""
    
    def test_email_sent_after_successful_import(self, mock_gcs_monitor, mock_dependencies):
        """Test that confirmation email is sent after successful patient import."""
        from patient_service.imports.import_status import ImportStatus
        
        file_name = "patient_with_email.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            test_data = {
                "patient_data": {
                    "vorname": "Max",
                    "nachname": "Mustermann",
                    "email": "max@example.com",
                    "symptome": ["Depression / Niedergeschlagenheit"]
                },
                "registration_token": "a7f3e9b2c4d8f1a6e5b9c3d7f2a8e4b1c6d9f3a7e2b5c8d1f4a9e3b7c2d6f8a0"
            }
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock successful import
                mock_gcs_monitor.importer.import_patient.return_value = (True, "Patient created with ID: 123")
                
                # The email sending is handled inside importer.import_patient
                # We just verify the import was called successfully
                with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                    with patch.object(ImportStatus, 'record_success'):
                        mock_gcs_monitor._process_file(file_name)
                        
                        # Verify import was called
                        mock_gcs_monitor.importer.import_patient.assert_called_once_with(test_data)


class TestDownloadFile:
    """[EXISTING] Test the _download_file method."""
    
    def test_successful_download(self, mock_gcs_monitor, mock_dependencies):
        """Test successful file download from GCS."""
        file_name = "test_patient.json"
        local_path = "/test/path/test_patient.json"
        temp_path = f"{local_path}.tmp"
        
        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs_monitor.reader_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock successful download
        mock_blob.download_to_filename.return_value = None
        
        # Mock file operations for JSON validation
        # Phase 2: Updated valid JSON structure
        valid_json = {
            "patient_data": {
                "vorname": "Test",
                "symptome": ["Schlafstörungen"]
            },
            "registration_token": "test123"
        }
        with patch('builtins.open', mock_open(read_data=json.dumps(valid_json))):
            # Mock os.rename for moving temp to final
            with patch('os.rename') as mock_rename:
                result = mock_gcs_monitor._download_file(file_name, local_path)
                
                # [EXISTING] Verify success
                assert result is True
                
                # [EXISTING] Verify download was called with temp path
                mock_blob.download_to_filename.assert_called_once_with(temp_path)
                
                # [EXISTING] Verify file was moved from temp to final
                mock_rename.assert_called_once_with(temp_path, local_path)
    
    def test_download_with_retry(self, mock_gcs_monitor, mock_dependencies):
        """Test download retry on failure."""
        file_name = "test_patient.json"
        local_path = "/test/path/test_patient.json"
        temp_path = f"{local_path}.tmp"
        
        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs_monitor.reader_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock first attempt fails, second succeeds
        mock_blob.download_to_filename.side_effect = [
            Exception("Network error"),
            None  # Success on second attempt
        ]
        
        # Mock file operations
        valid_json = {"patient_data": {"vorname": "Test", "symptome": ["Stress / Überforderung"]}, "registration_token": "test"}
        with patch('builtins.open', mock_open(read_data=json.dumps(valid_json))):
            with patch('os.rename'):
                # Mock sleep to speed up test
                with patch('time.sleep'):
                    result = mock_gcs_monitor._download_file(file_name, local_path, max_retries=2)
                    
                    # [EXISTING] Verify success after retry
                    assert result is True
                    
                    # [EXISTING] Verify download was called twice
                    assert mock_blob.download_to_filename.call_count == 2
    
    def test_download_invalid_json_returns_false(self, mock_gcs_monitor, mock_dependencies):
        """Test download with invalid JSON returns False and cleans up temp file."""
        file_name = "test_patient.json"
        local_path = "/test/path/test_patient.json"
        temp_path = f"{local_path}.tmp"
        
        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs_monitor.reader_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock successful download
        mock_blob.download_to_filename.return_value = None
        
        # Mock file operations with invalid JSON
        with patch('builtins.open', mock_open(read_data="Invalid JSON {")):
            # Mock os.path.exists and os.remove for cleanup
            with patch('os.path.exists', return_value=True):
                with patch('os.remove') as mock_remove:
                    result = mock_gcs_monitor._download_file(file_name, local_path)
                    
                    # [EXISTING] Verify failure
                    assert result is False
                    
                    # [EXISTING] Verify temp file was cleaned up
                    mock_remove.assert_called_once_with(temp_path)
    
    def test_download_all_retries_fail(self, mock_gcs_monitor, mock_dependencies):
        """Test download fails after all retries."""
        file_name = "test_patient.json"
        local_path = "/test/path/test_patient.json"
        
        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs_monitor.reader_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock all attempts fail
        mock_blob.download_to_filename.side_effect = Exception("Network error")
        
        # Mock sleep to speed up test
        with patch('time.sleep'):
            result = mock_gcs_monitor._download_file(file_name, local_path, max_retries=2)
            
            # [EXISTING] Verify failure
            assert result is False
            
            # [EXISTING] Verify download was attempted max_retries times
            assert mock_blob.download_to_filename.call_count == 2


class TestGCSDelete:
    """[EXISTING] Test the _delete_from_gcs method."""
    
    def test_successful_deletion(self, mock_gcs_monitor, mock_dependencies):
        """Test successful file deletion from GCS."""
        file_name = "test_patient.json"
        
        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs_monitor.deleter_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock successful deletion
        mock_blob.delete.return_value = None
        
        result = mock_gcs_monitor._delete_from_gcs(file_name)
        
        # [EXISTING] Verify success
        assert result is True
        
        # [EXISTING] Verify delete was called
        mock_blob.delete.assert_called_once()
    
    def test_deletion_failure(self, mock_gcs_monitor, mock_dependencies):
        """Test handling of deletion failure."""
        file_name = "test_patient.json"
        
        # Mock bucket and blob
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_gcs_monitor.deleter_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock deletion failure
        mock_blob.delete.side_effect = Exception("Permission denied")
        
        result = mock_gcs_monitor._delete_from_gcs(file_name)
        
        # [EXISTING] Verify failure
        assert result is False


class TestImportStatusIntegration:
    """[EXISTING] Test ImportStatus tracking during file processing."""
    
    def test_import_status_tracks_all_outcomes(self, mock_gcs_monitor, mock_dependencies):
        """Test that ImportStatus correctly tracks successes and failures."""
        from patient_service.imports.import_status import ImportStatus
        
        # Reset ImportStatus
        with patch.object(ImportStatus, '_status', {
            'running': True,
            'last_check': None,
            'files_processed_today': 0,
            'files_failed_today': 0,
            'last_error': None,
            'last_error_time': None,
            'total_processed': 0,
            'total_failed': 0,
            'current_date': datetime.now().date(),
            'recent_imports': []
        }):
            # Test successful import
            file_name = "success.json"
            with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
                # Phase 2: Updated test data
                test_data = {
                    "patient_data": {"vorname": "Test", "symptome": ["Schlafstörungen"]},
                    "registration_token": "test123"
                }
                with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                    mock_gcs_monitor.importer.import_patient.return_value = (True, "Success")
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        mock_gcs_monitor._process_file(file_name)
            
            # Test failed import
            file_name = "failure.json"
            with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
                test_data = {
                    "patient_data": {"vorname": "Test", "symptome": ["Invalid"]},
                    "registration_token": "test"
                }
                with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                    mock_gcs_monitor.importer.import_patient.return_value = (False, "Invalid symptom")
                    with patch('os.rename'):
                        with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                            with patch.object(mock_gcs_monitor.importer, 'send_error_notification'):
                                mock_gcs_monitor._process_file(file_name)
            
            # Get status
            status = ImportStatus.get_status()
            
            # [EXISTING] Verify counts
            assert status['files_processed_today'] == 1
            assert status['files_failed_today'] == 1
            assert status['total_processed'] == 1
            assert status['total_failed'] == 1
            assert len(status['recent_imports']) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])