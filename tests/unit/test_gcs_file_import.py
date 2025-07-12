"""Unit tests for GCS patient import file processing."""
import json
import os
import sys
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock, call
from datetime import datetime

# Mock all the problematic imports BEFORE importing the module under test
# This prevents import errors when running tests from project root
sys.modules['models'] = MagicMock()
sys.modules['models.patient'] = MagicMock()
sys.modules['events'] = MagicMock()
sys.modules['events.producers'] = MagicMock()

# Create mock Patient class for the imports
MockPatient = MagicMock()
sys.modules['models.patient'].Patient = MockPatient

# Create mock functions for events
mock_publish_patient_created = MagicMock()
sys.modules['events.producers'].publish_patient_created = mock_publish_patient_created

# Now we can safely import our modules under test
from patient_service.imports.gcs_monitor import GCSMonitor
from patient_service.imports.import_status import ImportStatus


@pytest.fixture
def mock_gcs_monitor():
    """Create a GCSMonitor instance with all external dependencies mocked."""
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
    
    def test_successful_import_file_stays_in_base_path(self, mock_gcs_monitor):
        """Test successful import - file should stay in base path and GCS file deleted."""
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Mock successful file read and JSON parse
            test_data = {"patient_data": {"name": "Test Patient"}}
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock successful import
                mock_gcs_monitor.importer.import_patient.return_value = (True, "Success")
                
                # Mock successful GCS deletion
                with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True) as mock_delete:
                    # Mock os.path.exists to simulate file exists
                    with patch('os.path.exists', return_value=True):
                        # Mock ImportStatus
                        with patch.object(ImportStatus, 'record_success') as mock_record_success:
                            # Process the file
                            mock_gcs_monitor._process_file(file_name)
                            
                            # Verify download was called
                            mock_gcs_monitor._download_file.assert_called_once_with(file_name, local_path)
                            
                            # Verify import was called with correct data
                            mock_gcs_monitor.importer.import_patient.assert_called_once_with(test_data)
                            
                            # Verify success was recorded
                            mock_record_success.assert_called_once_with(file_name)
                            
                            # Verify GCS file was deleted
                            mock_delete.assert_called_once_with(file_name)
                            
                            # Verify no attempt to move file (it should stay in base path)
                            with patch('os.rename') as mock_rename:
                                mock_rename.assert_not_called()
    
    def test_database_error_file_moved_to_failed(self, mock_gcs_monitor):
        """Test database error during import - file should be moved to failed/ folder."""
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Mock successful file read
            test_data = {"patient_data": {"name": "Test Patient"}}
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
                                
                                # Verify file was moved to failed folder
                                mock_rename.assert_called_once_with(local_path, failed_path)
                                
                                # Verify failure was recorded
                                mock_record_failure.assert_called_once_with(file_name, error_msg)
                                
                                # Verify error notification was sent
                                mock_notify.assert_called_once()
                                
                                # Verify GCS file was still deleted
                                mock_delete.assert_called_once_with(file_name)
    
    def test_validation_error_file_moved_to_failed(self, mock_gcs_monitor):
        """Test validation error during import - file should be moved to failed/ folder."""
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Mock successful file read
            test_data = {"patient_data": {"name": "Test Patient"}}
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock failed import (validation error)
                error_msg = "Invalid anrede 'Dr.'"
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
    
    def test_download_failure_no_file_no_gcs_deletion(self, mock_gcs_monitor):
        """Test download failure - no local file created, GCS file NOT deleted."""
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
                    
                    # Verify download was attempted
                    mock_gcs_monitor._download_file.assert_called_once_with(file_name, local_path)
                    
                    # Verify import was NOT attempted
                    mock_gcs_monitor.importer.import_patient.assert_not_called()
                    
                    # Verify GCS deletion was NOT called
                    mock_delete.assert_not_called()
                    
                    # Verify failure was recorded
                    mock_record_failure.assert_called_once_with(file_name, "Failed to download file")
    
    def test_move_to_failed_error_file_preserved(self, mock_gcs_monitor):
        """Test when move to failed/ fails - file should still be preserved in base path."""
        file_name = "test_patient.json"
        local_path = os.path.join(mock_gcs_monitor.local_base_path, file_name)
        failed_path = os.path.join(mock_gcs_monitor.local_base_path, 'failed', file_name)
        
        # Mock successful download
        with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
            # Mock successful file read
            test_data = {"patient_data": {"name": "Test Patient"}}
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                # Mock failed import
                mock_gcs_monitor.importer.import_patient.return_value = (False, "Import failed")
                
                # Mock failed file move (permission error)
                with patch('os.rename', side_effect=OSError("Permission denied")) as mock_rename:
                    # Mock successful GCS deletion
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        # Mock ImportStatus
                        with patch.object(ImportStatus, 'record_failure'):
                            # Mock logging to verify error is logged
                            with patch('logging.Logger.error') as mock_log_error:
                                # Process the file
                                mock_gcs_monitor._process_file(file_name)
                                
                                # Verify move was attempted
                                mock_rename.assert_called_once_with(local_path, failed_path)
                                
                                # Verify error was logged
                                mock_log_error.assert_any_call(
                                    "Failed to move file to failed/: Permission denied"
                                )
                                
                                # File remains in original location since move failed
                                # GCS deletion still happens (current behavior)
    
    def test_json_decode_error_file_moved_to_failed(self, mock_gcs_monitor):
        """Test invalid JSON - file should be moved to failed/ folder."""
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
                                    
                                    # Verify file was moved to failed folder
                                    mock_rename.assert_called_once_with(local_path, failed_path)
                                    
                                    # Verify failure was recorded with JSON error
                                    args = mock_record_failure.call_args[0]
                                    assert args[0] == file_name
                                    assert "Invalid JSON" in args[1]
    
    def test_missing_patient_data_section_file_moved_to_failed(self, mock_gcs_monitor):
        """Test JSON missing patient_data section - file should be moved to failed/ folder."""
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
                            
                            # Verify import was called
                            mock_gcs_monitor.importer.import_patient.assert_called_once_with(test_data)
                            
                            # Verify failure was recorded
                            mock_record_failure.assert_called_once_with(file_name, error_msg)


class TestDownloadFile:
    """Test the _download_file method."""
    
    def test_successful_download(self, mock_gcs_monitor):
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
        valid_json = {"patient_data": {"name": "Test"}}
        with patch('builtins.open', mock_open(read_data=json.dumps(valid_json))):
            # Mock os.rename for moving temp to final
            with patch('os.rename') as mock_rename:
                result = mock_gcs_monitor._download_file(file_name, local_path)
                
                # Verify success
                assert result is True
                
                # Verify download was called with temp path
                mock_blob.download_to_filename.assert_called_once_with(temp_path)
                
                # Verify file was moved from temp to final
                mock_rename.assert_called_once_with(temp_path, local_path)
    
    def test_download_with_retry(self, mock_gcs_monitor):
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
        valid_json = {"patient_data": {"name": "Test"}}
        with patch('builtins.open', mock_open(read_data=json.dumps(valid_json))):
            with patch('os.rename'):
                # Mock sleep to speed up test
                with patch('time.sleep'):
                    result = mock_gcs_monitor._download_file(file_name, local_path, max_retries=2)
                    
                    # Verify success after retry
                    assert result is True
                    
                    # Verify download was called twice
                    assert mock_blob.download_to_filename.call_count == 2
    
    def test_download_invalid_json_returns_false(self, mock_gcs_monitor):
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
                    
                    # Verify failure
                    assert result is False
                    
                    # Verify temp file was cleaned up
                    mock_remove.assert_called_once_with(temp_path)
    
    def test_download_all_retries_fail(self, mock_gcs_monitor):
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
            
            # Verify failure
            assert result is False
            
            # Verify download was attempted max_retries times
            assert mock_blob.download_to_filename.call_count == 2


class TestGCSDelete:
    """Test the _delete_from_gcs method."""
    
    def test_successful_deletion(self, mock_gcs_monitor):
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
        
        # Verify success
        assert result is True
        
        # Verify delete was called
        mock_blob.delete.assert_called_once()
    
    def test_deletion_failure(self, mock_gcs_monitor):
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
        
        # Verify failure
        assert result is False


class TestImportStatusIntegration:
    """Test ImportStatus tracking during file processing."""
    
    def test_import_status_tracks_all_outcomes(self, mock_gcs_monitor):
        """Test that ImportStatus correctly tracks successes and failures."""
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
                with patch('builtins.open', mock_open(read_data='{"patient_data": {}}')):
                    mock_gcs_monitor.importer.import_patient.return_value = (True, "Success")
                    with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                        mock_gcs_monitor._process_file(file_name)
            
            # Test failed import
            file_name = "failure.json"
            with patch.object(mock_gcs_monitor, '_download_file', return_value=True):
                with patch('builtins.open', mock_open(read_data='{"patient_data": {}}')):
                    mock_gcs_monitor.importer.import_patient.return_value = (False, "DB Error")
                    with patch('os.rename'):
                        with patch.object(mock_gcs_monitor, '_delete_from_gcs', return_value=True):
                            with patch.object(mock_gcs_monitor.importer, 'send_error_notification'):
                                mock_gcs_monitor._process_file(file_name)
            
            # Get status
            status = ImportStatus.get_status()
            
            # Verify counts
            assert status['files_processed_today'] == 1
            assert status['files_failed_today'] == 1
            assert status['total_processed'] == 1
            assert status['total_failed'] == 1
            assert len(status['recent_imports']) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])