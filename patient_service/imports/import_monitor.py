"""Object Storage monitoring and import orchestration for patient files.

Monitors Infomaniak Object Storage for new patient registration files and orchestrates imports.
Keeps local copies for debugging/analysis.
"""
import os
import time
import logging
import json
from datetime import datetime
from typing import List, Optional

from shared.config import get_config
from shared.utils.object_storage import ObjectStorageClient
from .patient_importer import PatientImporter
from .import_status import ImportStatus

logger = logging.getLogger(__name__)


class ObjectStorageMonitor:
    """Monitor Object Storage for new patient files and orchestrate imports.
    
    Downloads files from Object Storage, keeps local copies for analysis,
    and deletes from Object Storage after processing (success or failure).
    """
    
    def __init__(self):
        """Initialize the Object Storage monitor."""
        self.config = get_config()
        
        # Get configuration from environment variables
        self.local_base_path = os.environ.get('PATIENT_IMPORT_LOCAL_PATH')
        check_interval_str = os.environ.get('PATIENT_IMPORT_CHECK_INTERVAL_SECONDS')
        
        # Validate required environment variables
        if not self.local_base_path:
            raise ValueError("PATIENT_IMPORT_LOCAL_PATH environment variable is required")
        if not check_interval_str:
            raise ValueError("PATIENT_IMPORT_CHECK_INTERVAL_SECONDS environment variable is required")
        
        try:
            self.check_interval = int(check_interval_str)
        except ValueError:
            raise ValueError(f"PATIENT_IMPORT_CHECK_INTERVAL_SECONDS must be a valid integer, got: {check_interval_str}")
        
        # Initialize Object Storage client
        self.storage_client = ObjectStorageClient()
        
        # Initialize importer
        self.importer = PatientImporter()
        
        # Ensure local directories exist
        os.makedirs(self.local_base_path, exist_ok=True)
        os.makedirs(os.path.join(self.local_base_path, 'failed'), exist_ok=True)
        
        logger.info(f"Object Storage Monitor initialized")
        logger.info(f"Container: {self.storage_client.container}")
        logger.info(f"Local storage path: {self.local_base_path}")
        logger.info(f"Check interval: {self.check_interval} seconds")
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Starting patient import monitoring from Object Storage...")
        
        while True:
            try:
                # Update status
                ImportStatus.update_last_check()
                
                # List and process files
                files = self.storage_client.list_files('registrations')
                if files:
                    logger.info(f"Found {len(files)} files to process")
                    for file_name in files:
                        self._process_file(file_name)
                else:
                    logger.debug("No files found in registrations folder")
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                ImportStatus.record_error(str(e))
            
            # Wait before next check
            time.sleep(self.check_interval)
    
    def _process_file(self, file_name: str):
        """Process a single file from Object Storage.
        
        Downloads file, saves locally for analysis, processes patient,
        and always deletes from Object Storage after processing.
        
        Args:
            file_name: Name of the file in Object Storage
        """
        logger.info(f"Processing file: {file_name}")
        local_path = os.path.join(self.local_base_path, file_name)
        
        try:
            # Download and verify file (HMAC verification happens here)
            try:
                data = self.storage_client.download_file('registrations', file_name)
            except ValueError as e:
                # HMAC verification failed or other validation error
                logger.error(f"Validation failed for {file_name}: {str(e)}")
                ImportStatus.record_failure(file_name, str(e))
                
                # Save to failed folder for analysis (if we can)
                self._save_failed_file(file_name, str(e))
                
                # Delete from Object Storage
                self.storage_client.delete_file('registrations', file_name)
                
                # Send notification
                self.importer.send_error_notification(
                    f"Validation failed for patient file: {file_name}",
                    f"Error: {str(e)}"
                )
                return
            except Exception as e:
                logger.error(f"Failed to download {file_name}: {str(e)}")
                ImportStatus.record_failure(file_name, f"Download failed: {str(e)}")
                
                # Try to delete from Object Storage anyway
                self.storage_client.delete_file('registrations', file_name)
                return
            
            # Save to local file for analysis/debugging
            try:
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.debug(f"Saved local copy: {local_path}")
            except Exception as e:
                logger.warning(f"Failed to save local copy: {str(e)}")
                # Continue processing even if local save fails
            
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
                    if os.path.exists(local_path):
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
            
            # Always delete from Object Storage after processing (success or failure)
            if self.storage_client.delete_file('registrations', file_name):
                logger.info(f"Deleted from Object Storage: {file_name}")
            else:
                logger.error(f"Could not delete from Object Storage: {file_name}")
                
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
            
            # Delete from Object Storage
            self.storage_client.delete_file('registrations', file_name)
            
            # Send notification
            self.importer.send_error_notification(
                f"Error processing patient file: {file_name}",
                f"Exception: {str(e)}"
            )
    
    def _save_failed_file(self, file_name: str, error: str):
        """Try to save a failed file locally for debugging.
        
        Args:
            file_name: Name of the file
            error: Error message to include
        """
        try:
            failed_path = os.path.join(self.local_base_path, 'failed', file_name)
            error_data = {
                "error": error,
                "timestamp": datetime.utcnow().isoformat(),
                "file_name": file_name
            }
            with open(failed_path, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2)
            logger.info(f"Saved error info to failed/: {file_name}")
        except Exception as e:
            logger.warning(f"Could not save failed file info: {str(e)}")


def start_patient_import_monitor():
    """Start the patient import monitoring in a background thread."""
    try:
        monitor = ObjectStorageMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to start Object Storage monitor: {str(e)}", exc_info=True)
        ImportStatus.record_error(f"Monitor startup failed: {str(e)}")