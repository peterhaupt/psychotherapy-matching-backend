"""API client with automatic retry logic."""
import requests
from time import sleep
from typing import Optional, Dict, Any


class RetryAPIClient:
    """API client with automatic retry logic."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    @classmethod
    def call_with_retry(cls, method: str, url: str, 
                       json: Optional[Dict] = None,
                       timeout: int = 10) -> requests.Response:
        """
        Make an API call with automatic retry on failure.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Full URL to call
            json: JSON payload (optional)
            timeout: Request timeout in seconds
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException after all retries exhausted
        """
        last_exception = None
        
        for attempt in range(cls.MAX_RETRIES):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=json,
                    timeout=timeout
                )
                
                # Success or client error (4xx) - don't retry
                if response.status_code < 500:
                    return response
                    
                # Server error - will retry
                last_exception = requests.HTTPError(
                    f"Server error: {response.status_code}"
                )
                
            except requests.RequestException as e:
                last_exception = e
            
            # Wait before retry (except on last attempt)
            if attempt < cls.MAX_RETRIES - 1:
                sleep(cls.RETRY_DELAY * (attempt + 1))  # Exponential backoff
        
        # All retries exhausted
        raise last_exception
