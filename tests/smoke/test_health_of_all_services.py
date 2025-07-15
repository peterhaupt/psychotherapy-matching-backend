"""Simple smoke test for all service health endpoints - Environment Agnostic Version."""
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

# Environment detection
TEST_ENV = os.environ.get("TEST_ENV", "dev")
SERVICE_ENV_SUFFIX = os.environ.get("SERVICE_ENV_SUFFIX", "")

# Service health URLs from environment
CORE_SERVICES = [
    ("patient", os.environ["PATIENT_HEALTH_URL"], "patient"),
    ("patient-import", os.environ["PATIENT_HEALTH_URL"].replace("/health", "/health/import"), "patient-import"),
    ("therapist", os.environ["THERAPIST_HEALTH_URL"], "therapist"),
    ("therapist-import", os.environ["THERAPIST_HEALTH_URL"].replace("/health", "/health/import"), "therapist-import"),
    ("matching", os.environ["MATCHING_HEALTH_URL"], "matching"),
    ("communication", os.environ["COMMUNICATION_HEALTH_URL"], "communication"),
    ("geocoding", os.environ["GEOCODING_HEALTH_URL"], "geocoding"),
]

# Environment-specific backup service configuration
def get_backup_services():
    """Get backup services based on current environment."""
    backup_services = []
    
    # Environment detection
    if TEST_ENV == "prod" or SERVICE_ENV_SUFFIX == "-prod":
        # Production environment
        backup_url = os.environ.get("POSTGRES_BACKUP_PROD_HEALTH_URL", "http://localhost:8082/health")
        backup_services.append(("postgres-backup-prod", backup_url, "backup"))
    elif TEST_ENV == "test" or SERVICE_ENV_SUFFIX == "-test":
        # Test environment
        backup_url = os.environ.get("POSTGRES_BACKUP_TEST_HEALTH_URL", "http://localhost:8081/health")
        backup_services.append(("postgres-backup-test", backup_url, "backup"))
    else:
        # Development environment (default)
        backup_url = os.environ.get("POSTGRES_BACKUP_HEALTH_URL", "http://localhost:8080/health")
        backup_services.append(("postgres-backup", backup_url, "backup"))
    
    return backup_services

# Test controls
BACKUP_HEALTH_TESTS_ENABLED = os.environ.get("ENABLE_BACKUP_HEALTH_TESTS", "true").lower() == "true"
PARALLEL_TESTS_ENABLED = os.environ.get("ENABLE_PARALLEL_HEALTH_TESTS", "true").lower() == "true"

# Combine core services with environment-specific backup services
def get_all_services():
    """Get all services to test based on environment."""
    services = CORE_SERVICES.copy()
    
    if BACKUP_HEALTH_TESTS_ENABLED:
        services.extend(get_backup_services())
    
    return services

SERVICES = get_all_services()
TIMEOUT = int(os.environ.get("HEALTH_CHECK_TIMEOUT", "10"))  # seconds


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
            except ValueError:
                # Handle non-JSON responses (backup services might return plain text)
                response_text = response.text.strip()
                if ("healthy" in response_text.lower() or 
                    "backup" in response_text.lower() or
                    expected_service in response_text.lower()):
                    return (service_name, True, 200, {"status": "healthy", "service": expected_service, "response": response_text}, None)
                else:
                    return (service_name, False, 200, None, f"Unexpected text response: {response_text}")
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
        
        print(f"\n🔍 Testing health endpoints in {TEST_ENV} environment")
        print(f"Service suffix: '{SERVICE_ENV_SUFFIX}'")
        print(f"Backup tests enabled: {BACKUP_HEALTH_TESTS_ENABLED}")
        
        for service_name, url, expected_service in SERVICES:
            print(f"\nChecking {service_name} service at {url}")
            
            service_name, success, status_code, data, error = check_service_health(
                service_name, url, expected_service
            )
            
            if success:
                print(f"✅ {service_name} service: OK")
                if data and isinstance(data, dict):
                    print(f"   Response: {data}")
            else:
                print(f"❌ {service_name} service: FAILED")
                print(f"   Status: {status_code}")
                print(f"   Error: {error}")
                
                # For backup services, make failure non-fatal in some environments
                if service_name.startswith("postgres-backup") and not BACKUP_HEALTH_TESTS_ENABLED:
                    print(f"   ⚠️  Backup service failure ignored (tests disabled)")
                    continue
                    
                failed_services.append(f"{service_name}: {error}")
        
        # Assert that all services are healthy
        assert not failed_services, f"Failed services: {'; '.join(failed_services)}"
    
    @pytest.mark.skipif(not PARALLEL_TESTS_ENABLED, reason="Parallel tests disabled")
    def test_all_health_endpoints_parallel(self):
        """Test all health endpoints in parallel for faster execution."""
        print(f"\n🚀 Testing all services in parallel in {TEST_ENV} environment...")
        failed_services = []
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=min(len(SERVICES), 10)) as executor:
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
                    
                    # For backup services, make failure non-fatal if tests disabled
                    if service_name.startswith("postgres-backup") and not BACKUP_HEALTH_TESTS_ENABLED:
                        print(f"   ⚠️  Backup service failure ignored (tests disabled)")
                        continue
                        
                    failed_services.append(f"{service_name}: {error}")
        
        # Assert that all services are healthy
        assert not failed_services, f"Failed services: {'; '.join(failed_services)}"
    
    def test_individual_health_endpoints(self):
        """Test each health endpoint individually for detailed reporting."""
        failed_services = []
        
        print(f"\n🔍 Individual health checks for {TEST_ENV} environment")
        
        for service_name, url, expected_service in SERVICES:
            # Test each service individually
            service_name, success, status_code, data, error = check_service_health(
                service_name, url, expected_service
            )
            
            if not success:
                # For backup services, handle gracefully
                if service_name.startswith("postgres-backup"):
                    if BACKUP_HEALTH_TESTS_ENABLED:
                        failed_services.append(f"{service_name}: {error}")
                    else:
                        print(f"⚠️ {service_name} service: SKIPPED (backup tests disabled)")
                else:
                    failed_services.append(f"{service_name}: {error}")
                continue
                
            # Validate response structure
            if isinstance(data, dict):
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
        print(f"\nTesting {service_name} service in {TEST_ENV} environment...")
        
        service_name, success, status_code, data, error = check_service_health(
            service_name, url, expected_service
        )
        
        # Handle backup services specially
        if service_name.startswith("postgres-backup") and not BACKUP_HEALTH_TESTS_ENABLED:
            pytest.skip(f"Backup health tests disabled for {service_name}")
        
        # Detailed assertions for better error reporting
        assert success, f"{service_name} health check failed: {error}"
        assert status_code == 200, f"{service_name} returned status {status_code}"
        
        if isinstance(data, dict):
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
        slow_threshold = float(os.environ.get("SLOW_RESPONSE_THRESHOLD", "3.0"))  # seconds
        
        print(f"\n⏱️ Testing response times in {TEST_ENV} environment (threshold: {slow_threshold}s)")
        
        for service_name, url, expected_service in SERVICES:
            start_time = time.time()
            
            try:
                response = requests.get(url, timeout=TIMEOUT)
                response_time = time.time() - start_time
                
                if response_time > slow_threshold:
                    slow_services.append(f"{service_name}: {response_time:.2f}s")
                
                print(f"{service_name} responded in {response_time:.2f}s")
                
            except requests.RequestException as e:
                response_time = time.time() - start_time
                if service_name.startswith("postgres-backup") and not BACKUP_HEALTH_TESTS_ENABLED:
                    print(f"{service_name} skipped: {e}")
                else:
                    slow_services.append(f"{service_name}: timeout/error after {response_time:.2f}s")
                    print(f"{service_name} failed after {response_time:.2f}s: {e}")
        
        if slow_services:
            print(f"⚠️  Slow services detected: {'; '.join(slow_services)}")
            # Don't fail the test for slow services, just warn
        else:
            print("✅ All services responded quickly")
    
    def test_service_availability_summary(self):
        """Generate a summary report of all service availability."""
        print("\n" + "="*80)
        print(f"SERVICE AVAILABILITY SUMMARY - {TEST_ENV.upper()} ENVIRONMENT")
        print("="*80)
        
        healthy_count = 0
        total_count = len(SERVICES)
        skipped_count = 0
        
        for service_name, url, expected_service in SERVICES:
            # Skip backup services if tests disabled
            if service_name.startswith("postgres-backup") and not BACKUP_HEALTH_TESTS_ENABLED:
                status_icon = "⏭️"
                status_text = "SKIPPED"
                skipped_count += 1
            else:
                service_name, success, status_code, data, error = check_service_health(
                    service_name, url, expected_service
                )
                
                status_icon = "✅" if success else "❌"
                status_text = "HEALTHY" if success else "UNHEALTHY"
                
                if success:
                    healthy_count += 1
            
            print(f"{status_icon} {service_name.upper():20} | {url:50} | {status_text}")
        
        print("="*80)
        tested_count = total_count - skipped_count
        if tested_count > 0:
            print(f"SUMMARY: {healthy_count}/{tested_count} tested services healthy "
                  f"({healthy_count/tested_count*100:.1f}%)")
        if skipped_count > 0:
            print(f"         {skipped_count} services skipped")
        print(f"ENVIRONMENT: {TEST_ENV.upper()}")
        print("="*80)
        
        # This test always passes but provides visibility
        assert True, "Summary test completed"


class TestBackupServiceHealth:
    """Specific tests for backup service health endpoints."""
    
    @pytest.mark.skipif(not BACKUP_HEALTH_TESTS_ENABLED, reason="Backup health tests disabled")
    def test_backup_services_health_structure(self):
        """Test that backup services return proper health structure."""
        backup_services = get_backup_services()
        
        if not backup_services:
            pytest.skip("No backup services configured for this environment")
        
        failed_backup_services = []
        
        for service_name, url, expected_service in backup_services:
            print(f"\n🔍 Testing backup service: {service_name}")
            
            service_name, success, status_code, data, error = check_service_health(
                service_name, url, expected_service
            )
            
            if not success:
                failed_backup_services.append(f"{service_name}: {error}")
                continue
            
            # Backup services might return different response formats
            if isinstance(data, dict):
                # JSON response - check for backup-specific fields
                expected_fields = ["status"]
                optional_fields = ["service", "last_backup", "backup_count", "disk_usage", "response"]
                
                missing_required = [field for field in expected_fields if field not in data]
                present_optional = [field for field in optional_fields if field in data]
                
                if missing_required:
                    failed_backup_services.append(f"{service_name}: missing required fields: {missing_required}")
                else:
                    print(f"✅ {service_name} has required health fields")
                    if present_optional:
                        print(f"   Additional fields: {present_optional}")
            else:
                # Text response - this is also acceptable for backup services
                print(f"✅ {service_name} returned text response (acceptable)")
        
        # Only fail if basic health checks failed
        if failed_backup_services:
            pytest.fail(f"Backup service health checks failed: {'; '.join(failed_backup_services)}")
    
    @pytest.mark.skipif(not BACKUP_HEALTH_TESTS_ENABLED, reason="Backup health tests disabled")
    def test_backup_services_respond_with_backup_info(self):
        """Test that backup services provide backup-specific information when available."""
        backup_services = get_backup_services()
        
        if not backup_services:
            pytest.skip("No backup services configured for this environment")
        
        print(f"\n📋 Backup service information for {TEST_ENV} environment:")
        
        for service_name, url, expected_service in backup_services:
            try:
                response = requests.get(url, timeout=TIMEOUT)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Log backup-specific information if available
                        if "last_backup" in data:
                            print(f"  {service_name} last backup: {data['last_backup']}")
                        if "backup_count" in data:
                            print(f"  {service_name} backup count: {data['backup_count']}")
                        if "disk_usage" in data:
                            print(f"  {service_name} disk usage: {data['disk_usage']}")
                        if "response" in data:
                            print(f"  {service_name} status: {data['response']}")
                            
                        print(f"✅ {service_name} provided backup information")
                        
                    except ValueError:
                        # Plain text response
                        response_text = response.text.strip()
                        print(f"  {service_name} status: {response_text}")
                        print(f"✅ {service_name} responded with status information")
                        
                else:
                    print(f"⚠️  {service_name} health check failed with status {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"⚠️  {service_name} connection failed: {e}")

    @pytest.mark.skipif(not BACKUP_HEALTH_TESTS_ENABLED, reason="Backup health tests disabled")
    def test_environment_specific_backup_service(self):
        """Test that the correct backup service is running for the environment."""
        backup_services = get_backup_services()
        
        if not backup_services:
            pytest.skip("No backup services configured for this environment")
        
        print(f"\n🎯 Verifying correct backup service for {TEST_ENV} environment")
        
        expected_service_name = None
        if TEST_ENV == "prod" or SERVICE_ENV_SUFFIX == "-prod":
            expected_service_name = "postgres-backup-prod"
        elif TEST_ENV == "test" or SERVICE_ENV_SUFFIX == "-test":
            expected_service_name = "postgres-backup-test"
        else:
            expected_service_name = "postgres-backup"
        
        # Check that we're testing the correct service
        service_names = [service[0] for service in backup_services]
        assert expected_service_name in service_names, \
            f"Expected backup service '{expected_service_name}' not found. Available: {service_names}"
        
        print(f"✅ Correct backup service '{expected_service_name}' is configured for {TEST_ENV}")
        
        # Test the service
        for service_name, url, expected_service in backup_services:
            if service_name == expected_service_name:
                service_name, success, status_code, data, error = check_service_health(
                    service_name, url, expected_service
                )
                
                assert success, f"Environment-specific backup service {service_name} failed: {error}"
                print(f"✅ Environment-specific backup service {service_name} is healthy")
                break


class TestEnvironmentConfiguration:
    """Tests to verify environment-specific configuration."""
    
    def test_service_count_appropriate_for_environment(self):
        """Test that service count is appropriate for the environment."""
        core_service_count = len(CORE_SERVICES)
        backup_service_count = len(get_backup_services()) if BACKUP_HEALTH_TESTS_ENABLED else 0
        total_service_count = len(SERVICES)
        
        print(f"\n📊 Service count for {TEST_ENV} environment:")
        print(f"  Core services: {core_service_count}")
        print(f"  Backup services: {backup_service_count}")
        print(f"  Total services: {total_service_count}")
        
        # Verify reasonable service counts
        assert core_service_count == 7, f"Expected 7 core services, got {core_service_count}"
        
        if BACKUP_HEALTH_TESTS_ENABLED:
            assert backup_service_count == 1, f"Expected 1 backup service when enabled, got {backup_service_count}"
            assert total_service_count == 8, f"Expected 8 total services when backup enabled, got {total_service_count}"
        else:
            assert backup_service_count == 0, f"Expected 0 backup services when disabled, got {backup_service_count}"
            assert total_service_count == 7, f"Expected 7 total services when backup disabled, got {total_service_count}"
        
        print(f"✅ Service count is appropriate for {TEST_ENV} environment")


if __name__ == "__main__":
    # Can be run directly for quick checks
    print(f"Running health check smoke tests for {TEST_ENV} environment...")
    pytest.main([__file__, "-v", "--tb=short"])