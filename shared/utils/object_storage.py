"""Object Storage client for Infomaniak Swift/OpenStack.

Simple client for downloading files from Object Storage containers,
verifying HMAC signatures, and deleting processed files.
"""
import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from swiftclient import Connection
from keystoneauth1 import session
from keystoneauth1.identity import v3

logger = logging.getLogger(__name__)


class ObjectStorageClient:
    """Simple Swift client for processing files from Infomaniak Object Storage."""
    
    def __init__(self, environment: Optional[str] = None):
        """Initialize Swift client with Infomaniak credentials.
        
        Args:
            environment: Override environment (dev/test/prod). 
                        If None, uses FLASK_ENV to determine container.
        """
        if environment:
            # Use explicitly provided environment
            self.environment = environment
        else:
            # Map FLASK_ENV to container name
            flask_env = os.environ.get('FLASK_ENV', 'development')
            env_mapping = {
                'development': 'dev',
                'test': 'test',
                'production': 'prod'
            }
        self.environment = env_mapping.get(flask_env, 'dev')
        
        # Container name is just the environment
        self.container = self.environment
        
        # Get credentials from environment
        self.auth_url = os.environ.get('SWIFT_AUTH_URL', 'https://api.pub1.infomaniak.cloud/identity/v3')
        self.application_id = os.environ.get('SWIFT_APPLICATION_ID')
        self.application_secret = os.environ.get('SWIFT_APPLICATION_SECRET')
        self.region = os.environ.get('SWIFT_REGION', 'dc4-a')
        
        # HMAC key for signature verification
        self.hmac_key = os.environ.get('HMAC_SECRET_KEY')
        
        # Validate required credentials
        if not all([self.application_id, self.application_secret]):
            raise ValueError(
                "Missing Swift credentials. Required: "
                "SWIFT_APPLICATION_ID, SWIFT_APPLICATION_SECRET"
            )
        
        if not self.hmac_key:
            raise ValueError("Missing HMAC_SECRET_KEY for signature verification")
        
        # Initialize connection
        self._init_connection()
        
        logger.info(f"ObjectStorageClient initialized for environment: {self.environment}")
    
    def _init_connection(self):
        """Initialize Swift connection using application credentials."""
        # Create auth using application credentials
        auth = v3.ApplicationCredential(
            auth_url=self.auth_url,
            application_credential_id=self.application_id,
            application_credential_secret=self.application_secret
        )
        
        # Create session
        sess = session.Session(auth=auth)
        
        # Create Swift connection
        self.conn = Connection(session=sess)
        
        # Test connection
        try:
            self.conn.get_account()
            logger.info("Swift connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Swift: {str(e)}")
            raise
    
    def list_files(self, folder: str) -> List[str]:
        """List JSON files in a specific folder.
        
        Args:
            folder: Folder name (e.g., 'verifications', 'contacts', 'registrations')
            
        Returns:
            List of file names in the folder
        """
        try:
            # List objects with prefix
            prefix = f"{folder}/"
            headers, objects = self.conn.get_container(
                self.container, 
                prefix=prefix,
                delimiter='/'
            )
            
            # Filter for JSON files only
            files = []
            for obj in objects:
                name = obj['name']
                if name.endswith('.json'):
                    # Return just the filename, not the full path
                    filename = name.replace(prefix, '')
                    files.append(filename)
            
            if files:
                logger.debug(f"Found {len(files)} files in {folder}/")
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {folder}: {str(e)}")
            return []
    
    def download_file(self, folder: str, filename: str) -> Dict[str, Any]:
        """Download and verify a JSON file from Object Storage.
        
        Args:
            folder: Folder name (e.g., 'verifications', 'contacts')
            filename: Name of the file to download
            
        Returns:
            Parsed JSON data with verified signature
            
        Raises:
            ValueError: If HMAC verification fails or JSON is invalid
            Exception: If download fails
        """
        try:
            # Build full object path
            object_path = f"{folder}/{filename}"
            
            # Download file
            headers, content = self.conn.get_object(self.container, object_path)
            
            # Parse JSON
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            data = json.loads(content)
            
            # Verify HMAC signature
            if not self.verify_hmac(data):
                raise ValueError(f"HMAC verification failed for {object_path}")
            
            # Check file age (warn if older than 30 minutes)
            if 'timestamp' in data:
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('+00:00', '').replace('Z', ''))
                    age = datetime.utcnow() - timestamp
                    if age > timedelta(minutes=30):
                        logger.warning(f"File {object_path} is {age.total_seconds()/60:.1f} minutes old")
                except:
                    pass  # Don't fail on timestamp parsing
            
            # Check environment matches
            if 'environment' in data and data['environment'] != self.environment:
                raise ValueError(
                    f"Environment mismatch: file is for {data['environment']}, "
                    f"but client is configured for {self.environment}"
                )
            
            logger.info(f"Successfully downloaded and verified {object_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {folder}/{filename}: {str(e)}")
            raise ValueError(f"Invalid JSON in file: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to download {folder}/{filename}: {str(e)}")
            raise
    
    def delete_file(self, folder: str, filename: str) -> bool:
        """Delete a file from Object Storage.
        
        Args:
            folder: Folder name
            filename: Name of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            object_path = f"{folder}/{filename}"
            self.conn.delete_object(self.container, object_path)
            logger.info(f"Deleted {object_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete {folder}/{filename}: {str(e)}")
            return False
    
    def verify_hmac(self, data: Dict[str, Any]) -> bool:
        """Verify HMAC signature on data.
        
        Expected structure:
        {
            "signature": "...",
            "signature_version": "hmac-sha256-v1",
            "timestamp": "2025-09-03T11:53:44+02:00",
            "type": "email_verification",
            "environment": "dev",
            "data": { ... actual payload ... }
        }
        
        Args:
            data: JSON data with signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['signature', 'signature_version', 'timestamp', 'type', 'data']
            if not all(field in data for field in required_fields):
                logger.warning("Missing required signature fields")
                return False
            
            # Only support hmac-sha256-v1
            if data['signature_version'] != 'hmac-sha256-v1':
                logger.warning(f"Unsupported signature version: {data['signature_version']}")
                return False
            
            # Reconstruct the signed content
            # PHP signs: timestamp|type|environment|json_encode(data)
            signed_content = '|'.join([
                data['timestamp'],
                data['type'],
                data.get('environment', ''),
                json.dumps(data['data'], separators=(',', ':'), ensure_ascii=False)
            ])
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.hmac_key.encode('utf-8'),
                signed_content.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, data['signature'])
            
            if not is_valid:
                logger.warning(f"Invalid signature for {data.get('type')} from {data.get('environment')}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying HMAC: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test the Swift connection and container access.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            # Try to get container info
            headers = self.conn.head_container(self.container)
            logger.info(f"Container '{self.container}' is accessible")
            
            # Try to list files (should work even if empty)
            self.conn.get_container(self.container, limit=1)
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False


# Convenience function for testing
def test_swift_connection():
    """Test Swift connection with current configuration."""
    try:
        client = ObjectStorageClient()
        if client.test_connection():
            print(f"✓ Connected to Swift container: {client.container}")
            
            # Try listing each expected folder
            for folder in ['verifications', 'contacts', 'registrations']:
                files = client.list_files(folder)
                print(f"✓ {folder}/: {len(files)} files")
            
            return True
        else:
            print("✗ Connection test failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False