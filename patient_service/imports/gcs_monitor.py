"""GCS monitoring and import orchestration for patient files - simplified."""
import os
import time
import logging
import json
from datetime import datetime
from typing import List, Optional

from google.cloud import storage
from google.api_core import exceptions as gcs_exceptions

from shared.config import get_config
from .patient_importer import PatientImporter
from .import_status import ImportStatus

logger = logging.getLogger(__name__)


class GCSMonitor:
    """Monitor GCS bucket for new patient files and orchestrate imports.
    
    Simplified version: 
    - Successful files stay in base path
    - Failed files are moved to failed/ folder
    - All files are deleted from GCS after processing
    """
    
    def __init__(self):
        """Initialize the GCS monitor."""
        self.config = get_config()
        self.bucket_name = os.environ.get('GCS_IMPORT_BUCKET', 'dev-patient-import')
        self.local_base_path = os.environ.get('PATIENT_IMPORT_LOCAL_PATH', '/data/patient_imports/development')
        self.check_interval = int(os.environ.get('PATIENT_IMPORT_CHECK_INTERVAL_SECONDS', '300'))
        
        # Initialize GCS clients
        self.reader_client = self._init_gcs_client('reader')
        self.deleter_client = self._init_gcs_client('deleter')
        
        # Initialize importer
        self.importer = PatientImporter()
        
        # Ensure local directories exist
        os.makedirs(self.local_base_path, exist_ok=True)
        os.makedirs(os.path.join(self.local_base_path, 'failed'), exist_ok=True)
        
        logger.info(f"GCS Monitor initialized for bucket: {self.bucket_name}")
        logger.info(f"Local storage path: {self.local_base_path}")
        logger.info(f"Check interval: {self.check_interval} seconds")
    
    def _init_gcs_client(self, client_type: str) -> storage.Client:
        """Initialize a GCS client with appropriate credentials.
        
        Args:
            client_type: 'reader' or 'deleter'
            
        Returns:
            Initialized GCS client
        """
        if client_type == 'reader':
            creds_path = os.environ.get('GCS_READER_CREDENTIALS_PATH', '/credentials/gcs-reader.json')
        else:
            creds_path = os.environ.get('GCS_DELETER_CREDENTIALS_PATH', '/credentials/gcs-deleter.json')
        
        if not os.path.exists(creds_path):
            raise ValueError(f"Credentials file not found: {creds_path}")
        
        return storage.Client.from_service_account_json(creds_path)
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Starting GCS patient import monitoring...")
        
        while True:
            try:
                # Update status
                ImportStatus.update_last_check()
                
                # List and process files
                files = self._list_bucket_files()
                if files:
                    logger.info(f"Found {len(files)} files to process")
                    for file_name in files:
                        self._process_file(file_name)
                else:
                    logger.debug("No files found in bucket")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                ImportStatus.record_error(str(e))
            
            # Wait before next check
            time.sleep(self.check_interval)
    
    def _list_bucket_files(self) -> List[str]:
        """List all JSON files in the bucket.
        
        Returns:
            List of file names
        """
        try:
            bucket = self.reader_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs()
            
            # Filter for JSON files only
            json_files = [blob.name for blob in blobs if blob.name.endswith('.json')]
            return json_files
            
        except Exception as e:
            logger.error(f"Error listing bucket files: {str(e)}")
            return []
    
    def _process_file(self, file_name: str):
        """Process a single file from GCS - simplified version.
        
        Args:
            file_name: Name of the file in GCS
        """
        logger.info(f"Processing file: {file_name}")
        local_path = os.path.join(self.local_base_path, file_name)
        
        try:
            # Download file
            if not self._download_file(file_name, local_path):
                ImportStatus.record_failure(file_name, "Failed to download file")
                return
            
            # Parse and validate JSON
            with open(local_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import patient
            success, message = self.importer.import_patient(data)
            
            if success:
                # Success: file stays in base path
                logger.info(f"Successfully imported: {file_name}")
                ImportStatus.record_success(file_name)
            else:
                # Failure: move to failed folder
                failed_path = os.path.join(self.local_base_path, 'failed', file_name)
                try:
                    os.rename(local_path, failed_path)
                    logger.error(f"Import failed, moved to failed/: {file_name}. Reason: {message}")
                except Exception as move_error:
                    logger.error(f"Failed to move file to failed/: {move_error}")
                    # Keep the file where it is if move fails
                
                ImportStatus.record_failure(file_name, message)
                
                # Send error notification
                self.importer.send_error_notification(
                    f"Failed to import patient file: {file_name}",
                    f"Error: {message}\n\nFile has been saved to local failed/ folder."
                )
            
            # Always delete from GCS after processing (success or failure)
            if self._delete_from_gcs(file_name):
                logger.info(f"Deleted from GCS: {file_name}")
            else:
                logger.error(f"Could not delete from GCS: {file_name}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_name}: {str(e)}")
            # Try to move to failed folder
            try:
                failed_path = os.path.join(self.local_base_path, 'failed', file_name)
                if os.path.exists(local_path):
                    os.rename(local_path, failed_path)
            except:
                pass
            
            ImportStatus.record_failure(file_name, f"Invalid JSON: {str(e)}")
            
            # Delete from GCS
            self._delete_from_gcs(file_name)
            
            # Send notification
            self.importer.send_error_notification(
                f"Invalid JSON in patient file: {file_name}",
                f"JSON parsing error: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error processing file {file_name}: {str(e)}", exc_info=True)
            # Try to move to failed folder
            try:
                if os.path.exists(local_path):
                    failed_path = os.path.join(self.local_base_path, 'failed', file_name)
                    os.rename(local_path, failed_path)
            except:
                pass
            
            ImportStatus.record_failure(file_name, str(e))
            
            # Delete from GCS
            self._delete_from_gcs(file_name)
            
            # Send notification
            self.importer.send_error_notification(
                f"Error processing patient file: {file_name}",
                f"Exception: {str(e)}"
            )
    
    def _download_file(self, file_name: str, local_path: str, max_retries: int = 2) -> bool:
        """Download file from GCS with retry logic.
        
        Args:
            file_name: Name of file in GCS
            local_path: Local path to save file
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if download successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                bucket = self.reader_client.bucket(self.bucket_name)
                blob = bucket.blob(file_name)
                
                # Download to temporary file first
                temp_path = f"{local_path}.tmp"
                blob.download_to_filename(temp_path)
                
                # Verify file is valid JSON
                with open(temp_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                
                # Move to final location
                os.rename(temp_path, local_path)
                logger.info(f"Successfully downloaded: {file_name}")
                return True
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in file {file_name}: {str(e)}")
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False
                
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {file_name}: {str(e)}")
                # Clean up temp file
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to download {file_name} after {max_retries} attempts")
                    return False
        
        return False
    
    def _delete_from_gcs(self, file_name: str) -> bool:
        """Delete file from GCS bucket.
        
        Args:
            file_name: Name of file to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            bucket = self.deleter_client.bucket(self.bucket_name)
            blob = bucket.blob(file_name)
            blob.delete()
            logger.info(f"Deleted from GCS: {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete {file_name} from GCS: {str(e)}")
            return False


def start_patient_import_monitor():
    """Start the patient import monitoring in a background thread."""
    try:
        monitor = GCSMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to start GCS monitor: {str(e)}", exc_info=True)
        ImportStatus.record_error(f"Monitor startup failed: {str(e)}")
