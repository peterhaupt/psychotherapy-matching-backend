"""Object Storage monitoring and orchestration for verification emails and contact forms.

Monitors Infomaniak Object Storage for new verification and contact files,
processes them, and deletes after processing.
"""
import os
import time
import logging
from datetime import datetime
from typing import Optional

from shared.config import get_config
from shared.utils.object_storage import ObjectStorageClient
from .verification_processor import VerificationProcessor
from .contact_processor import ContactProcessor
from .waitlist_processor import WaitlistProcessor
from .processor_status import ProcessorStatus

logger = logging.getLogger(__name__)


class StorageMonitor:
    """Monitor Object Storage for verification emails and contact forms.
    
    Downloads files from Object Storage, processes them, and deletes after processing.
    """
    
    def __init__(self):
        """Initialize the Storage monitor."""
        self.config = get_config()
        
        # Get check interval from environment
        check_interval_str = os.environ.get('STORAGE_CHECK_INTERVAL_SECONDS', '30')
        
        try:
            self.check_interval = int(check_interval_str)
        except ValueError:
            # Fallback to 30 seconds
            self.check_interval = 30
            logger.warning(f"Invalid check interval, using default: {self.check_interval} seconds")
        
        # Initialize Object Storage client
        self.storage_client = ObjectStorageClient()
        
        # Initialize processors
        self.verification_processor = VerificationProcessor()
        self.contact_processor = ContactProcessor()
        self.waitlist_processor = WaitlistProcessor()
        
        logger.info(f"Storage Monitor initialized")
        logger.info(f"Container: {self.storage_client.container}")
        logger.info(f"Check interval: {self.check_interval} seconds")
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Starting storage monitoring for verifications, contacts, and waitlist...")

        while True:
            try:
                # Update status
                ProcessorStatus.update_last_check()

                # Process verification emails
                try:
                    verification_files = self.storage_client.list_files('verifications')
                    if verification_files:
                        logger.info(f"Found {len(verification_files)} verification files to process")
                        for file_name in verification_files:
                            self._process_verification(file_name)
                    else:
                        logger.debug("No verification files found")
                except Exception as e:
                    logger.error(f"Error processing verifications: {str(e)}")
                    ProcessorStatus.record_error(f"Verification check failed: {str(e)}")

                # Process contact forms
                try:
                    contact_files = self.storage_client.list_files('contacts')
                    if contact_files:
                        logger.info(f"Found {len(contact_files)} contact files to process")
                        for file_name in contact_files:
                            self._process_contact(file_name)
                    else:
                        logger.debug("No contact files found")
                except Exception as e:
                    logger.error(f"Error processing contacts: {str(e)}")
                    ProcessorStatus.record_error(f"Contact check failed: {str(e)}")

                # Process waitlist verifications
                try:
                    waitlist_files = self.storage_client.list_files('waitlist')
                    if waitlist_files:
                        logger.info(f"Found {len(waitlist_files)} waitlist files to process")
                        for file_name in waitlist_files:
                            self._process_waitlist(file_name)
                    else:
                        logger.debug("No waitlist files found")
                except Exception as e:
                    logger.error(f"Error processing waitlist: {str(e)}")
                    ProcessorStatus.record_error(f"Waitlist check failed: {str(e)}")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                ProcessorStatus.record_error(str(e))

            # Wait before next check
            time.sleep(self.check_interval)
    
    def _process_verification(self, file_name: str):
        """Process a single verification file.
        
        Args:
            file_name: Name of the file in Object Storage
        """
        logger.info(f"Processing verification file: {file_name}")
        
        try:
            # Download and verify file
            try:
                data = self.storage_client.download_file('verifications', file_name)
            except ValueError as e:
                # HMAC verification failed or other validation error
                logger.error(f"Validation failed for verification {file_name}: {str(e)}")
                ProcessorStatus.record_verification_failure(file_name, str(e))
                
                # Delete from Object Storage
                self.storage_client.delete_file('verifications', file_name)
                
                # Send notification
                self._send_error_notification(
                    f"Validation failed for verification file: {file_name}",
                    f"Error: {str(e)}"
                )
                return
            except Exception as e:
                logger.error(f"Failed to download verification {file_name}: {str(e)}")
                ProcessorStatus.record_verification_failure(file_name, f"Download failed: {str(e)}")
                
                # Try to delete from Object Storage anyway
                self.storage_client.delete_file('verifications', file_name)
                return
            
            # Process verification
            success, message = self.verification_processor.process_verification(data)
            
            if success:
                logger.info(f"Successfully processed verification: {file_name}")
                ProcessorStatus.record_verification_success(file_name)
            else:
                logger.error(f"Failed to process verification {file_name}: {message}")
                ProcessorStatus.record_verification_failure(file_name, message)
                
                # Send error notification
                self._send_error_notification(
                    f"Failed to process verification file: {file_name}",
                    f"Error: {message}"
                )
            
            # Always delete from Object Storage after processing
            if self.storage_client.delete_file('verifications', file_name):
                logger.info(f"Deleted from Object Storage: verifications/{file_name}")
            else:
                logger.error(f"Could not delete from Object Storage: verifications/{file_name}")
                
        except Exception as e:
            logger.error(f"Unexpected error processing verification {file_name}: {str(e)}", exc_info=True)
            ProcessorStatus.record_verification_failure(file_name, str(e))
            
            # Delete from Object Storage
            self.storage_client.delete_file('verifications', file_name)
            
            # Send notification
            self._send_error_notification(
                f"Error processing verification file: {file_name}",
                f"Exception: {str(e)}"
            )
    
    def _process_contact(self, file_name: str):
        """Process a single contact form file.
        
        Args:
            file_name: Name of the file in Object Storage
        """
        logger.info(f"Processing contact file: {file_name}")
        
        try:
            # Download and verify file
            try:
                data = self.storage_client.download_file('contacts', file_name)
            except ValueError as e:
                # HMAC verification failed or other validation error
                logger.error(f"Validation failed for contact {file_name}: {str(e)}")
                ProcessorStatus.record_contact_failure(file_name, str(e))
                
                # Delete from Object Storage
                self.storage_client.delete_file('contacts', file_name)
                
                # Send notification
                self._send_error_notification(
                    f"Validation failed for contact file: {file_name}",
                    f"Error: {str(e)}"
                )
                return
            except Exception as e:
                logger.error(f"Failed to download contact {file_name}: {str(e)}")
                ProcessorStatus.record_contact_failure(file_name, f"Download failed: {str(e)}")
                
                # Try to delete from Object Storage anyway
                self.storage_client.delete_file('contacts', file_name)
                return
            
            # Process contact
            success, message = self.contact_processor.process_contact(data)
            
            if success:
                logger.info(f"Successfully processed contact: {file_name}")
                ProcessorStatus.record_contact_success(file_name)
            else:
                logger.error(f"Failed to process contact {file_name}: {message}")
                ProcessorStatus.record_contact_failure(file_name, message)
                
                # Send error notification
                self._send_error_notification(
                    f"Failed to process contact file: {file_name}",
                    f"Error: {message}"
                )
            
            # Always delete from Object Storage after processing
            if self.storage_client.delete_file('contacts', file_name):
                logger.info(f"Deleted from Object Storage: contacts/{file_name}")
            else:
                logger.error(f"Could not delete from Object Storage: contacts/{file_name}")
                
        except Exception as e:
            logger.error(f"Unexpected error processing contact {file_name}: {str(e)}", exc_info=True)
            ProcessorStatus.record_contact_failure(file_name, str(e))
            
            # Delete from Object Storage
            self.storage_client.delete_file('contacts', file_name)
            
            # Send notification
            self._send_error_notification(
                f"Error processing contact file: {file_name}",
                f"Exception: {str(e)}"
            )

    def _process_waitlist(self, file_name: str):
        """Process a single waitlist verification file.

        Args:
            file_name: Name of the file in Object Storage
        """
        logger.info(f"Processing waitlist file: {file_name}")

        try:
            # Download and verify file
            try:
                data = self.storage_client.download_file('waitlist', file_name)
            except ValueError as e:
                # HMAC verification failed or other validation error
                logger.error(f"Validation failed for waitlist {file_name}: {str(e)}")
                ProcessorStatus.record_waitlist_failure(file_name, str(e))

                # Delete from Object Storage
                self.storage_client.delete_file('waitlist', file_name)

                # Send notification
                self._send_error_notification(
                    f"Validation failed for waitlist file: {file_name}",
                    f"Error: {str(e)}"
                )
                return
            except Exception as e:
                logger.error(f"Failed to download waitlist {file_name}: {str(e)}")
                ProcessorStatus.record_waitlist_failure(file_name, f"Download failed: {str(e)}")

                # Try to delete from Object Storage anyway
                self.storage_client.delete_file('waitlist', file_name)
                return

            # Process waitlist verification
            success, message = self.waitlist_processor.process_waitlist_verification(data)

            if success:
                logger.info(f"Successfully processed waitlist: {file_name}")
                ProcessorStatus.record_waitlist_success(file_name)
            else:
                logger.error(f"Failed to process waitlist {file_name}: {message}")
                ProcessorStatus.record_waitlist_failure(file_name, message)

                # Send error notification
                self._send_error_notification(
                    f"Failed to process waitlist file: {file_name}",
                    f"Error: {message}"
                )

            # Always delete from Object Storage after processing
            if self.storage_client.delete_file('waitlist', file_name):
                logger.info(f"Deleted from Object Storage: waitlist/{file_name}")
            else:
                logger.error(f"Could not delete from Object Storage: waitlist/{file_name}")

        except Exception as e:
            logger.error(f"Unexpected error processing waitlist {file_name}: {str(e)}", exc_info=True)
            ProcessorStatus.record_waitlist_failure(file_name, str(e))

            # Delete from Object Storage
            self.storage_client.delete_file('waitlist', file_name)

            # Send notification
            self._send_error_notification(
                f"Error processing waitlist file: {file_name}",
                f"Exception: {str(e)}"
            )

    def _send_error_notification(self, subject: str, body: str):
        """Send error notification via system messages endpoint.
        
        Args:
            subject: Error subject
            body: Error details
        """
        try:
            import requests
            
            comm_service_url = self.config.get_service_url('communication', internal=True)
            
            notification_data = {
                'subject': subject,
                'message': body,
                'sender_name': 'Storage Processor'
            }
            
            response = requests.post(
                f"{comm_service_url}/api/system-messages",
                json=notification_data,
                timeout=10
            )
            
            if response.ok:
                logger.info(f"Error notification sent: {subject}")
            else:
                logger.error(f"Failed to send error notification: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")


def start_storage_monitor():
    """Start the storage monitoring in a background thread."""
    try:
        monitor = StorageMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to start Storage monitor: {str(e)}", exc_info=True)
        ProcessorStatus.record_error(f"Monitor startup failed: {str(e)}")