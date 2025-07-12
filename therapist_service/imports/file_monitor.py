"""Local file monitoring and import orchestration for therapist files."""
import os
import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from shared.config import get_config
from .therapist_importer import TherapistImporter
from .import_status import ImportStatus

logger = logging.getLogger(__name__)


class LocalFileMonitor:
    """Monitor local file system for therapist JSON files and orchestrate imports.
    
    - Processes files from scraper output directory
    - Runs once every 24 hours
    - For each ZIP code, processes only the latest file
    - Handles errors gracefully and sends notifications
    """
    
    def __init__(self):
        """Initialize the local file monitor."""
        self.config = get_config()
        
        # Get configuration from environment variables (no defaults)
        self.base_path = os.environ.get('THERAPIST_IMPORT_FOLDER_PATH')
        check_interval_str = os.environ.get('THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS')
        
        # Validate required environment variables
        if not self.base_path:
            raise ValueError("THERAPIST_IMPORT_FOLDER_PATH environment variable is required")
        if not check_interval_str:
            raise ValueError("THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS environment variable is required")
        
        try:
            self.check_interval = int(check_interval_str)
        except ValueError:
            raise ValueError(f"THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS must be a valid integer, got: {check_interval_str}")
        
        # Initialize importer
        self.importer = TherapistImporter()
        
        logger.info(f"Local File Monitor initialized")
        logger.info(f"Base path: {self.base_path}")
        logger.info(f"Check interval: {self.check_interval} seconds ({self.check_interval / 3600} hours)")
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Starting therapist import monitoring...")
        
        while True:
            try:
                # Update status
                ImportStatus.update_last_check()
                
                # Find and process files
                self._process_latest_files()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                ImportStatus.record_error(str(e))
                
                # Send notification about monitoring error
                self.importer.send_error_notification(
                    "Therapist Import Monitor Error",
                    f"The therapist import monitor encountered an error:\n\n{str(e)}"
                )
            
            # Wait before next check
            logger.info(f"Waiting {self.check_interval / 3600} hours until next check...")
            time.sleep(self.check_interval)
    
    def _process_latest_files(self):
        """Find and process the latest file for each ZIP code."""
        logger.info("Starting daily therapist import run...")
        
        # Find all JSON files grouped by ZIP code
        files_by_zip = self._find_files_by_zip()
        
        if not files_by_zip:
            logger.info("No files found to process")
            return
        
        logger.info(f"Found files for {len(files_by_zip)} ZIP codes")
        
        # Track errors across all files
        all_errors = []
        total_processed = 0
        total_failed = 0
        
        # Process the latest file for each ZIP code
        for zip_code, files in files_by_zip.items():
            # Sort by date folder (newest first)
            files.sort(key=lambda x: x[0], reverse=True)
            
            # Get the latest file
            date_folder, file_path = files[0]
            logger.info(f"Processing ZIP {zip_code}: {date_folder}/{os.path.basename(file_path)}")
            
            # Process the file
            file_errors = self._process_file(file_path, zip_code)
            
            if file_errors:
                all_errors.extend(file_errors)
                total_failed += len(file_errors)
            
            # Count total therapists processed (including failures)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    therapist_count = len(data.get('therapists', []))
                    total_processed += therapist_count
                    ImportStatus.record_file_processed(
                        f"{date_folder}/{os.path.basename(file_path)}",
                        therapist_count,
                        len(file_errors)
                    )
            except:
                pass
        
        # Send summary notification if there were errors
        if all_errors:
            self._send_error_summary(all_errors, total_processed, total_failed)
        
        logger.info(f"Daily import run completed. Processed: {total_processed}, Failed: {total_failed}")
    
    def _find_files_by_zip(self) -> Dict[str, List[Tuple[str, str]]]:
        """Find all JSON files grouped by ZIP code.
        
        Returns:
            Dict mapping ZIP code to list of (date_folder, file_path) tuples
        """
        files_by_zip = defaultdict(list)
        
        if not os.path.exists(self.base_path):
            logger.error(f"Base path does not exist: {self.base_path}")
            return files_by_zip
        
        try:
            # List all date folders
            for date_folder in os.listdir(self.base_path):
                folder_path = os.path.join(self.base_path, date_folder)
                
                # Skip if not a directory or doesn't look like a date
                if not os.path.isdir(folder_path):
                    continue
                
                # Simple date folder validation (YYYYMMDD format)
                if not (len(date_folder) == 8 and date_folder.isdigit()):
                    continue
                
                # List JSON files in the date folder
                for file_name in os.listdir(folder_path):
                    if not file_name.endswith('.json'):
                        continue
                    
                    # Extract ZIP code from filename (e.g., "52062.json")
                    zip_code = file_name.replace('.json', '')
                    
                    # Add to the list for this ZIP code
                    file_path = os.path.join(folder_path, file_name)
                    files_by_zip[zip_code].append((date_folder, file_path))
            
        except Exception as e:
            logger.error(f"Error scanning directories: {str(e)}")
        
        return dict(files_by_zip)
    
    def _process_file(self, file_path: str, zip_code: str) -> List[Dict]:
        """Process a single therapist file.
        
        Args:
            file_path: Path to the JSON file
            zip_code: ZIP code being processed
            
        Returns:
            List of error dictionaries for failed imports
        """
        errors = []
        
        try:
            # Read and parse JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if 'therapists' not in data:
                logger.error(f"Invalid file structure in {file_path}: missing 'therapists' array")
                errors.append({
                    'file': file_path,
                    'error': 'Invalid file structure: missing therapists array'
                })
                return errors
            
            therapists = data.get('therapists', [])
            logger.info(f"Processing {len(therapists)} therapists from {os.path.basename(file_path)}")
            
            # Process each therapist
            for idx, therapist_data in enumerate(therapists):
                try:
                    # Check if therapist works with adults (import criteria)
                    therapy_methods = therapist_data.get('therapy_methods', [])
                    if not any('Erwachsene' in method for method in therapy_methods):
                        logger.debug(f"Skipping therapist {idx + 1}: No adult therapy methods")
                        continue
                    
                    # Import the therapist
                    success, message = self.importer.import_therapist(therapist_data)
                    
                    if not success:
                        errors.append({
                            'file': file_path,
                            'therapist': f"{therapist_data.get('basic_info', {}).get('first_name', '')} "
                                        f"{therapist_data.get('basic_info', {}).get('last_name', '')}",
                            'error': message,
                            'data': therapist_data
                        })
                        logger.error(f"Failed to import therapist {idx + 1}: {message}")
                
                except Exception as e:
                    logger.error(f"Error processing therapist {idx + 1}: {str(e)}", exc_info=True)
                    errors.append({
                        'file': file_path,
                        'therapist': f"Index {idx + 1}",
                        'error': str(e)
                    })
            
            logger.info(f"Completed processing {file_path}: "
                       f"{len(therapists) - len(errors)} successful, {len(errors)} failed")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
            errors.append({
                'file': file_path,
                'error': f'Invalid JSON: {str(e)}'
            })
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
            errors.append({
                'file': file_path,
                'error': str(e)
            })
        
        return errors
    
    def _send_error_summary(self, errors: List[Dict], total_processed: int, total_failed: int):
        """Send a summary email of all import errors.
        
        Args:
            errors: List of error dictionaries
            total_processed: Total number of therapists processed
            total_failed: Total number of failed imports
        """
        # Group errors by type
        error_summary = defaultdict(list)
        
        for error in errors:
            error_type = error.get('error', 'Unknown error')
            # Simplify error messages for grouping
            if 'already exists' in error_type:
                error_type = 'Duplicate therapist'
            elif 'Invalid' in error_type:
                error_type = error_type.split(':')[0]  # Get the general error type
            
            error_summary[error_type].append(error)
        
        # Build email body
        body = f"""Therapist Import Summary

Total Therapists Processed: {total_processed}
Failed Imports: {total_failed}
Success Rate: {((total_processed - total_failed) / total_processed * 100):.1f}%

Errors by Type:
"""
        
        for error_type, error_list in error_summary.items():
            body += f"\n{error_type}: {len(error_list)} occurrences\n"
            
            # Show first 3 examples
            for i, error in enumerate(error_list[:3]):
                therapist = error.get('therapist', 'Unknown')
                file_name = os.path.basename(error.get('file', 'Unknown file'))
                body += f"  - {therapist} ({file_name})\n"
            
            if len(error_list) > 3:
                body += f"  ... and {len(error_list) - 3} more\n"
        
        # Add details section
        body += "\n\nDetailed Error List:\n"
        for i, error in enumerate(errors[:20]):  # Limit to first 20 errors
            body += f"\n{i + 1}. File: {os.path.basename(error.get('file', 'Unknown'))}\n"
            body += f"   Therapist: {error.get('therapist', 'Unknown')}\n"
            body += f"   Error: {error.get('error', 'Unknown error')}\n"
        
        if len(errors) > 20:
            body += f"\n... and {len(errors) - 20} more errors"
        
        # Send notification
        self.importer.send_error_notification(
            f"Therapist Import - {total_failed} Failures",
            body
        )


def start_therapist_import_monitor():
    """Start the therapist import monitoring in a background thread."""
    try:
        monitor = LocalFileMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to start therapist import monitor: {str(e)}", exc_info=True)
        ImportStatus.record_error(f"Monitor startup failed: {str(e)}")
