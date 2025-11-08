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
    
    # Infomaniak's OpenStack auth endpoint (constant)
    AUTH_URL = 'https://api.pub1.infomaniak.cloud/identity/v3'
    
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
            self.environment = env_mapping.get(flask_env, 'dev')  # FIXED: Now inside else block
        
        # Container name is just the environment
        self.container = self.environment
        
        # Get credentials from environment (only what we actually need)
        self.application_id = os.environ.get('SWIFT_APPLICATION_ID')
        self.application_secret = os.environ.get('SWIFT_APPLICATION_SECRET')
        
        # HMAC key for signature verification
        self.hmac_key = os.environ.get('HMAC_SECRET_KEY')
        
        # Validate required credentials
        if not all([self.application_id, self.application_secret]):
            raise ValueError(
                "Missing Swift credentials. Required environment variables: "
                "SWIFT_APPLICATION_ID, SWIFT_APPLICATION_SECRET"
            )
        
        if not self.hmac_key:
            raise ValueError("Missing HMAC_SECRET_KEY for signature verification")
        
        # Initialize connection
        self._init_connection()
        
        logger.info(f"ObjectStorageClient initialized for container: {self.container}")
    
    def _init_connection(self):
        """Initialize Swift connection using application credentials."""
        try:
            # Create auth using application credentials
            auth = v3.ApplicationCredential(
                auth_url=self.AUTH_URL,
                application_credential_id=self.application_id,
                application_credential_secret=self.application_secret
            )
            
            # Create session
            sess = session.Session(auth=auth)

            # Create Swift connection
            # Storage URL format: https://s3.pub2.infomaniak.cloud/object/v1/AUTH_{project_id}
            storage_url = os.environ.get('SWIFT_STORAGE_URL')
            if not storage_url:
                raise ValueError(
                    "SWIFT_STORAGE_URL environment variable is required. "
                    "Format: https://s3.pub2.infomaniak.cloud/object/v1/AUTH_{project_id}"
                )
            self.conn = Connection(session=sess, preauthurl=storage_url)
            
            # Test connection and log the discovered URL
            try:
                headers, containers = self.conn.get_account()
                
                # Try to log the URL being used (if available)
                if hasattr(self.conn, 'url'):
                    logger.info(f"Swift connection established using URL: {self.conn.url}")
                else:
                    logger.info(f"Swift connection established (URL auto-discovered)")
                    
                logger.info(f"Account has {len(containers)} containers available")
                
                # Verify our expected container exists
                container_names = [c['name'] for c in containers]
                if self.container not in container_names:
                    logger.warning(
                        f"Container '{self.container}' not found! "
                        f"Available containers: {', '.join(container_names)}"
                    )
                    # Don't fail here - let operations fail with proper errors
                else:
                    logger.info(f"Container '{self.container}' verified to exist")
                    
            except Exception as e:
                logger.error(f"Failed to verify Swift connection: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to initialize Swift connection: {str(e)}")
            raise ValueError(f"Swift connection failed: {str(e)}")
    
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
                logger.debug(f"Found {len(files)} files in {self.container}/{folder}/")
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {self.container}/{folder}: {str(e)}")
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
                    # Handle various timestamp formats
                    timestamp_str = data['timestamp']
                    # Remove timezone info for parsing
                    timestamp_str = timestamp_str.replace('+00:00', '').replace('Z', '').split('+')[0]
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age = datetime.utcnow() - timestamp
                    if age > timedelta(minutes=30):
                        logger.warning(
                            f"File {object_path} is {age.total_seconds()/60:.1f} minutes old"
                        )
                except Exception as e:
                    logger.debug(f"Could not parse timestamp: {e}")
                    # Don't fail on timestamp parsing
            
            # Check environment matches (if specified in data)
            if 'environment' in data and data['environment'] != self.environment:
                logger.warning(
                    f"Environment mismatch: file is for '{data['environment']}', "
                    f"but client is configured for '{self.environment}'"
                )
                # Don't fail - just warn
            
            logger.info(f"Successfully downloaded and verified {self.container}/{object_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.container}/{folder}/{filename}: {str(e)}")
            raise ValueError(f"Invalid JSON in file: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to download {self.container}/{folder}/{filename}: {str(e)}")
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
            logger.info(f"Deleted {self.container}/{object_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete {self.container}/{folder}/{filename}: {str(e)}")
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
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                logger.warning(f"Missing required signature fields: {', '.join(missing_fields)}")
                return False
            
            # Only support hmac-sha256-v1
            if data['signature_version'] != 'hmac-sha256-v1':
                logger.warning(f"Unsupported signature version: {data['signature_version']}")
                return False
            
            # PHP signs the entire payload (minus signature fields)
            # Make a copy and remove signature fields
            payload_to_verify = data.copy()
            provided_signature = payload_to_verify.pop('signature', None)
            payload_to_verify.pop('signature_version', None)
            
            if not provided_signature:
                logger.warning("No signature found in data")
                return False
            
            # PHP signs the JSON-encoded payload with these flags:
            # JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
            payload_string = json.dumps(
                payload_to_verify,
                separators=(',', ':'),  # No spaces
                ensure_ascii=False,     # Don't escape unicode (UNESCAPED_UNICODE)
                # Note: Python doesn't escape slashes by default (like UNESCAPED_SLASHES)
            )
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.hmac_key.encode('utf-8'),
                payload_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant-time)
            is_valid = hmac.compare_digest(expected_signature, provided_signature)
            
            if not is_valid:
                logger.warning(
                    f"Invalid signature for {data.get('type')} "
                    f"from environment '{data.get('environment')}'"
                )
                logger.debug(f"Expected: {expected_signature[:20]}...")
                logger.debug(f"Got: {data['signature'][:20]}...")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying HMAC: {str(e)}", exc_info=True)
            return False
    
    def test_connection(self) -> bool:
        """Test the Swift connection and container access.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            # Try to get container info
            headers = self.conn.head_container(self.container)
            object_count = headers.get('x-container-object-count', 0)
            logger.info(
                f"Container '{self.container}' is accessible "
                f"({object_count} objects)"
            )
            
            # Try to list files (should work even if empty)
            headers, objects = self.conn.get_container(self.container, limit=1)
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed for container '{self.container}': {str(e)}")
            return False
    
    def upload_file(self, folder: str, filename: str, data: Dict[str, Any]) -> bool:
        """Upload a JSON file to Object Storage (for testing).
        
        Args:
            folder: Folder name (e.g., 'verifications', 'contacts')
            filename: Name for the file
            data: Data to upload as JSON
            
        Returns:
            True if uploaded successfully, False otherwise
        """
        try:
            object_path = f"{folder}/{filename}"
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            
            self.conn.put_object(
                self.container,
                object_path,
                contents=json_content.encode('utf-8'),
                content_type='application/json'
            )
            
            logger.info(f"Uploaded {self.container}/{object_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload {self.container}/{folder}/{filename}: {str(e)}")
            return False


# Convenience function for testing
def test_swift_connection():
    """Test Swift connection with current configuration."""
    try:
        print("Testing Swift connection...")
        print(f"Using environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        client = ObjectStorageClient()
        if client.test_connection():
            print(f"✅ Connected to Swift container: {client.container}")
            
            # Try listing each expected folder
            for folder in ['verifications', 'contacts', 'registrations']:
                files = client.list_files(folder)
                print(f"  {folder}/: {len(files)} files")
            
            return True
        else:
            print("❌ Connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    # Run test if executed directly
    test_swift_connection()
