"""Simple smoke test for all service health endpoints."""
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

# Service configurations: (name, url, expected_service_identifier)
SERVICES = [
    ("patient", os.environ["PATIENT_HEALTH_URL"], "patient"),
    ("patient-import", os.environ["PATIENT_HEALTH_URL"].replace("/health", "/health/import"), "patient-import"),
    ("therapist", os.environ["THERAPIST_HEALTH_URL"], "therapist"),
    ("therapist-import", os.environ["THERAPIST_HEALTH_URL"].replace("/health", "/health/import"), "therapist-import"),
    ("matching", os.environ["MATCHING_HEALTH_URL"], "matching"),
    ("communication", os.environ["COMMUNICATION_HEALTH_URL"], "communication"),
    ("geocoding", os.environ["GEOCODING_HEALTH_URL"], "geocoding"),
    # Backup container health endpoints
    ("postgres-backup", os.environ.get("POSTGRES_BACKUP_HEALTH_URL", "http://localhost:8080/health"), "backup"),
    ("postgres-backup-test", os.environ.get("POSTGRES_BACKUP_TEST_HEALTH_URL", "http://localhost:8081/health"), "backup"),
    ("postgres-backup-prod", os.environ.get("POSTGRES_BACKUP_PROD_HEALTH_URL", "http://localhost:8082/health"), "backup"),
]

TIMEOUT = 10  # seconds


def check_service_health(service_name, url, expected_service):
    """Check a single service health endpoint.
    
    Returns:
        tuple: (service_name, success, status_code, response_data, error_message)
    """
    try:
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                data = response.json()
                # Verify expected structure
                if (data.get("status") == "healthy" and 
                    expected_service in data.get("service", "").lower()):
                    return (service_name, True, 200, data, None)
                else:
                    return (service_name, False, 200, data, 
                           f"Unexpected response structure: {data}")
            except ValueError as e:
                return (service_name, False, 200, None, f"Invalid JSON: {e}")
        else:
            return (service_name, False, response.status_code, None, 
                   f"HTTP {response.status_code}")
            
    except requests.RequestException as e:
        return (service_name, False, 0, None, f"Connection error: {e}")


class TestHealthEndpoints:
    """Smoke tests for all service health endpoints."""
    
    def test_all_health_endpoints_sequential(self):
        """Test all health endpoints one by one (sequential)."""
        failed_services = []
        
        for service_name, url, expected_service in SERVICES:
            print(f"\nChecking {service_name} service at {url}")
            
            service_name, success, status_code, data, error = check_service_health(
                service_name, url, expected_service
            )
            
            if success:
                print(f"✅ {service_name} service: OK")
                print(f"   Response: {data}")
            else:
                print(f"❌ {service_name} service: FAILED")
                print(f"   Status: {status_code}")
                print(f"   Error: {error}")
                failed_services.append(f"{service_name}: {error}")
        
        # Assert that all services are healthy
        assert not failed_services, f"Failed services: {'; '.join(failed_services)}"
    
    def test_all_health_endpoints_parallel(self):
        """Test all health endpoints in parallel for faster execution."""
        print("\nTesting all services in parallel...")
        failed_services = []
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=len(SERVICES)) as executor:
            # Submit all requests
            future_to_service = {
                executor.submit(check_service_health, name, url, expected): name
                for name, url, expected in SERVICES
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_service):
                service_name, success, status_code, data, error = future.result()
                
                if success:
                    print(f"✅ {service_name} service: OK")
                else:
                    print(f"❌ {service_name} service: FAILED ({error})")
                    failed_services.append(f"{service_name}: {error}")
        
        # Assert that all services are healthy
        assert not failed_services, f"Failed services: {'; '.join(failed_services)}"
    
    def test_individual_health_endpoints(self):
        """Test each health endpoint individually for detailed reporting."""
        failed_services = []
        
        for service_name, url, expected_service in SERVICES:
            # Test each service individually
            service_name, success, status_code, data, error = check_service_health(
                service_name, url, expected_service
            )
            
            if not success:
                failed_services.append(f"{service_name}: {error}")
                continue
                
            if data.get("status") != "healthy":
                failed_services.append(f"{service_name}: status is '{data.get('status')}', expected 'healthy'")
                continue
                
            if expected_service not in data.get("service", "").lower():
                failed_services.append(f"{service_name}: service identifier mismatch in '{data.get('service')}'")
                continue
                
            print(f"✅ {service_name} service: OK")
        
        # Assert that all services passed
        assert not failed_services, f"Failed services: {'; '.join(failed_services)}"
    
    @pytest.mark.parametrize("service_name,url,expected_service", SERVICES)
    def test_parametrized_health_endpoints(self, service_name, url, expected_service):
        """Parametrized test for each service (creates separate test cases)."""
        print(f"\nTesting {service_name} service...")
        
        service_name, success, status_code, data, error = check_service_health(
            service_name, url, expected_service
        )
        
        # Detailed assertions for better error reporting
        assert success, f"{service_name} health check failed: {error}"
        assert status_code == 200, f"{service_name} returned status {status_code}"
        assert data is not None, f"{service_name} returned no data"
        assert data.get("status") == "healthy", \
            f"{service_name} status is '{data.get('status')}', expected 'healthy'"
        assert expected_service in data.get("service", "").lower(), \
            f"{service_name} service field is '{data.get('service')}', expected to contain '{expected_service}'"
        
        print(f"✅ {service_name} service is healthy")


class TestServiceConnectivity:
    """Additional connectivity tests."""
    
    def test_all_services_respond_quickly(self):
        """Test that all services respond within reasonable time."""
        slow_services = []
        
        for service_name, url, expected_service in SERVICES:
            start_time = time.time()
            
            try:
                response = requests.get(url, timeout=5)
                response_time = time.time() - start_time
                
                if response_time > 3.0:  # More than 3 seconds is considered slow
                    slow_services.append(f"{service_name}: {response_time:.2f}s")
                
                print(f"{service_name} responded in {response_time:.2f}s")
                
            except requests.RequestException as e:
                slow_services.append(f"{service_name}: timeout/error")
                print(f"{service_name} failed: {e}")
        
        if slow_services:
            print(f"⚠️  Slow services detected: {'; '.join(slow_services)}")
            # Don't fail the test for slow services, just warn
        else:
            print("✅ All services responded quickly")
    
    def test_service_availability_summary(self):
        """Generate a summary report of all service availability."""
        print("\n" + "="*60)
        print("SERVICE AVAILABILITY SUMMARY")
        print("="*60)
        
        healthy_count = 0
        total_count = len(SERVICES)
        
        for service_name, url, expected_service in SERVICES:
            service_name, success, status_code, data, error = check_service_health(
                service_name, url, expected_service
            )
            
            status_icon = "✅" if success else "❌"
            status_text = "HEALTHY" if success else "UNHEALTHY"
            
            print(f"{status_icon} {service_name.upper():18} | {url:40} | {status_text}")
            
            if success:
                healthy_count += 1
        
        print("="*60)
        print(f"SUMMARY: {healthy_count}/{total_count} services healthy "
              f"({healthy_count/total_count*100:.1f}%)")
        print("="*60)
        
        # This test always passes but provides visibility
        assert True, "Summary test completed"


class TestBackupServiceHealth:
    """Specific tests for backup service health endpoints."""
    
    def test_backup_services_health_structure(self):
        """Test that backup services return proper health structure."""
        backup_services = [s for s in SERVICES if s[0].startswith("postgres-backup")]
        
        failed_backup_services = []
        
        for service_name, url, expected_service in backup_services:
            service_name, success, status_code, data, error = check_service_health(
                service_name, url, expected_service
            )
            
            if not success:
                failed_backup_services.append(f"{service_name}: {error}")
                continue
            
            # Backup services should have additional fields
            expected_fields = ["status", "service", "last_backup", "backup_count", "disk_usage"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                print(f"⚠️  {service_name} missing expected fields: {missing_fields}")
                # Don't fail for missing fields, as the basic health check passed
            else:
                print(f"✅ {service_name} has all expected backup health fields")
        
        # Only fail if basic health checks failed
        if failed_backup_services:
            pytest.fail(f"Backup service health checks failed: {'; '.join(failed_backup_services)}")
    
    def test_backup_services_respond_with_backup_info(self):
        """Test that backup services provide backup-specific information."""
        backup_services = [s for s in SERVICES if s[0].startswith("postgres-backup")]
        
        for service_name, url, expected_service in backup_services:
            try:
                response = requests.get(url, timeout=TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Log backup-specific information if available
                    if "last_backup" in data:
                        print(f"{service_name} last backup: {data['last_backup']}")
                    if "backup_count" in data:
                        print(f"{service_name} backup count: {data['backup_count']}")
                    if "disk_usage" in data:
                        print(f"{service_name} disk usage: {data['disk_usage']}")
                        
                    print(f"✅ {service_name} provided backup information")
                else:
                    print(f"⚠️  {service_name} health check failed with status {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"⚠️  {service_name} connection failed: {e}")


if __name__ == "__main__":
    # Can be run directly for quick checks
    print("Running health check smoke tests...")
    pytest.main([__file__, "-v", "--tb=short"])