"""PDF management utility for therapist forms."""
import os
import re
import logging
from typing import List, Tuple, Optional
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


class PDFManager:
    """Manage PDF forms for therapists."""
    
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size
    
    def __init__(self):
        """Initialize the PDF manager with environment-based storage path."""
        # Get base path from environment variable
        self.base_dir = os.environ.get('THERAPIST_PDF_STORAGE_PATH', '/data/therapist_pdfs/development')
        
        # Ensure base directory exists
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            logger.info(f"PDF storage initialized at: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to create PDF storage directory: {str(e)}")
            raise
    
    def _get_therapist_dir(self, therapist_id: int) -> str:
        """Get the directory path for a specific therapist.
        
        Args:
            therapist_id: ID of the therapist
            
        Returns:
            Path to therapist's PDF directory
        """
        return os.path.join(self.base_dir, str(therapist_id))
    
    def _ensure_therapist_dir(self, therapist_id: int) -> str:
        """Ensure therapist directory exists.
        
        Args:
            therapist_id: ID of the therapist
            
        Returns:
            Path to therapist's PDF directory
        """
        therapist_dir = self._get_therapist_dir(therapist_id)
        os.makedirs(therapist_dir, exist_ok=True)
        return therapist_dir
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file extension is allowed
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in PDFManager.ALLOWED_EXTENSIONS
    
    @staticmethod
    def sanitize_filename(filename: str, therapist_id: int) -> str:
        """Sanitize filename while keeping it recognizable, preserving German characters.
        
        Args:
            filename: Original filename
            therapist_id: ID of the therapist (for uniqueness if needed)
            
        Returns:
            Sanitized filename
        """
        # First use werkzeug's secure_filename
        # This removes/replaces many special characters but keeps German umlauts
        secure_name = secure_filename(filename)
        
        # If secure_filename removed everything (or too much), create a fallback
        if not secure_name or secure_name == 'pdf':
            # Create a default name with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            secure_name = f"dokument_{therapist_id}_{timestamp}.pdf"
        
        # Ensure it ends with .pdf
        if not secure_name.lower().endswith('.pdf'):
            secure_name = secure_name.rsplit('.', 1)[0] + '.pdf' if '.' in secure_name else secure_name + '.pdf'
        
        # Handle common German document names specifically
        name_mapping = {
            'anamnesebogen': 'Anamnesebogen',
            'einverstaendniserklaerung': 'Einverstaendniserklaerung',
            'einverstandniserklarung': 'Einverstaendniserklaerung',  # Common typo
            'fragebogen': 'Fragebogen',
            'fragebogen_erwachsene': 'Fragebogen_Erwachsene',
            'fragebogen_kinder': 'Fragebogen_Kinder',
            'datenschutz': 'Datenschutzerklaerung',
            'schweigepflicht': 'Schweigepflichtentbindung'
        }
        
        # Check if the lowercase name (without .pdf) matches any standard name
        name_without_ext = secure_name.rsplit('.', 1)[0].lower()
        for pattern, replacement in name_mapping.items():
            if pattern in name_without_ext:
                secure_name = replacement + '.pdf'
                break
        
        return secure_name
    
    def get_therapist_forms(self, therapist_id: int) -> List[str]:
        """Get list of PDF forms for a therapist.
        
        Args:
            therapist_id: ID of the therapist
            
        Returns:
            List of full file paths to PDFs
        """
        therapist_dir = self._get_therapist_dir(therapist_id)
        
        if not os.path.exists(therapist_dir):
            return []
        
        try:
            files = []
            for filename in os.listdir(therapist_dir):
                if filename.lower().endswith('.pdf'):
                    full_path = os.path.join(therapist_dir, filename)
                    if os.path.isfile(full_path):
                        files.append(full_path)
            
            return sorted(files)  # Sort for consistent ordering
            
        except Exception as e:
            logger.error(f"Error listing PDFs for therapist {therapist_id}: {str(e)}")
            return []
    
    def get_therapist_forms_info(self, therapist_id: int) -> List[dict]:
        """Get detailed information about PDF forms for a therapist.
        
        Args:
            therapist_id: ID of the therapist
            
        Returns:
            List of dictionaries with file information
        """
        therapist_dir = self._get_therapist_dir(therapist_id)
        
        if not os.path.exists(therapist_dir):
            return []
        
        try:
            files = []
            for filename in os.listdir(therapist_dir):
                if filename.lower().endswith('.pdf'):
                    full_path = os.path.join(therapist_dir, filename)
                    if os.path.isfile(full_path):
                        stat = os.stat(full_path)
                        files.append({
                            'filename': filename,
                            'path': full_path,
                            'size': stat.st_size,
                            'size_mb': round(stat.st_size / (1024 * 1024), 2),
                            'modified': stat.st_mtime,
                            'modified_datetime': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
            
            # Sort by filename for consistent ordering
            return sorted(files, key=lambda x: x['filename'])
            
        except Exception as e:
            logger.error(f"Error getting PDF info for therapist {therapist_id}: {str(e)}")
            return []
    
    def upload_form(self, therapist_id: int, file, original_filename: str = None) -> Tuple[bool, str, Optional[str]]:
        """Upload a PDF form for a therapist.
        
        Args:
            therapist_id: ID of the therapist
            file: File object (from Flask request.files)
            original_filename: Original filename (if not available from file object)
            
        Returns:
            Tuple of (success, message, saved_filename)
        """
        try:
            # Get filename
            filename = original_filename or getattr(file, 'filename', None)
            if not filename:
                return False, "No filename provided", None
            
            # Check if file is allowed
            if not self.allowed_file(filename):
                return False, f"File type not allowed. Only PDF files are accepted.", None
            
            # Check file size (if possible)
            if hasattr(file, 'content_length') and file.content_length > self.MAX_FILE_SIZE:
                return False, f"File too large. Maximum size is {self.MAX_FILE_SIZE / (1024*1024):.1f}MB", None
            
            # Sanitize filename
            safe_filename = self.sanitize_filename(filename, therapist_id)
            
            # Ensure therapist directory exists
            therapist_dir = self._ensure_therapist_dir(therapist_id)
            
            # Full path for the file
            file_path = os.path.join(therapist_dir, safe_filename)
            
            # Check if file already exists
            if os.path.exists(file_path):
                # Add timestamp to make unique
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name_parts = safe_filename.rsplit('.', 1)
                safe_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                file_path = os.path.join(therapist_dir, safe_filename)
            
            # Save the file
            file.save(file_path)
            
            # Verify file was saved and is valid PDF
            if not os.path.exists(file_path):
                return False, "Failed to save file", None
            
            # Check if it's actually a PDF (basic check)
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    os.remove(file_path)
                    return False, "Invalid PDF file", None
            
            logger.info(f"Successfully uploaded PDF for therapist {therapist_id}: {safe_filename}")
            return True, f"File uploaded successfully as {safe_filename}", safe_filename
            
        except Exception as e:
            logger.error(f"Error uploading PDF for therapist {therapist_id}: {str(e)}")
            return False, f"Upload failed: {str(e)}", None
    
    def delete_form(self, therapist_id: int, filename: str) -> bool:
        """Delete a PDF form.
        
        Args:
            therapist_id: ID of the therapist
            filename: Name of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Sanitize the filename to prevent directory traversal
            if '..' in filename or '/' in filename or '\\' in filename:
                logger.warning(f"Suspicious filename in delete request: {filename}")
                return False
            
            therapist_dir = self._get_therapist_dir(therapist_id)
            file_path = os.path.join(therapist_dir, filename)
            
            # Check if file exists and is within therapist directory
            if not os.path.exists(file_path):
                logger.warning(f"File not found for deletion: {file_path}")
                return False
            
            # Verify the file is actually within the therapist's directory
            if not os.path.abspath(file_path).startswith(os.path.abspath(therapist_dir)):
                logger.error(f"Attempted to delete file outside therapist directory: {file_path}")
                return False
            
            # Delete the file
            os.remove(file_path)
            logger.info(f"Successfully deleted PDF for therapist {therapist_id}: {filename}")
            
            # Remove therapist directory if empty
            try:
                if not os.listdir(therapist_dir):
                    os.rmdir(therapist_dir)
                    logger.info(f"Removed empty directory for therapist {therapist_id}")
            except:
                pass  # Directory not empty or other issue, ignore
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting PDF for therapist {therapist_id}: {str(e)}")
            return False
    
    def delete_all_forms(self, therapist_id: int) -> Tuple[bool, int]:
        """Delete all PDF forms for a therapist.
        
        Args:
            therapist_id: ID of the therapist
            
        Returns:
            Tuple of (success, number_of_files_deleted)
        """
        try:
            therapist_dir = self._get_therapist_dir(therapist_id)
            
            if not os.path.exists(therapist_dir):
                return True, 0
            
            deleted_count = 0
            
            # Delete all PDF files
            for filename in os.listdir(therapist_dir):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(therapist_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
            
            # Try to remove the directory if empty
            try:
                os.rmdir(therapist_dir)
                logger.info(f"Removed directory for therapist {therapist_id}")
            except:
                pass  # Directory not empty (has non-PDF files) or other issue
            
            logger.info(f"Deleted {deleted_count} PDFs for therapist {therapist_id}")
            return True, deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting all PDFs for therapist {therapist_id}: {str(e)}")
            return False, 0


# Import datetime at the top of the file if not already imported
from datetime import datetime
