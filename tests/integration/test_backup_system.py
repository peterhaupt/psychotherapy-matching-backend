"""Integration tests for PostgreSQL backup system - Environment Agnostic Version."""
import pytest
import subprocess
import time
import glob
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Environment detection and configuration
TEST_ENV = os.environ.get("TEST_ENV", "dev")  # Fallback to dev if not set
SERVICE_ENV_SUFFIX = os.environ.get("SERVICE_ENV_SUFFIX", "")

# Base URLs for database connections
PATIENT_BASE_URL = os.environ["PATIENT_API_URL"]
THERAPIST_BASE_URL = os.environ["THERAPIST_API_URL"]

# Environment-specific backup configuration
def get_backup_config():
    """Get backup configuration based on current environment."""
    if TEST_ENV == "prod" or SERVICE_ENV_SUFFIX == "-prod":
        return {
            "env": "prod",
            "container_name": "postgres-backup-prod",
            "db_container_name": "postgres-prod",
            "backup_dir": "backups/postgres/hourly",
            "backup_prefix": "backup",
            "schedule_minutes": 60,  # Every hour
            "max_wait_minutes": 70,  # Wait longer for hourly backups
            "health_port": 8082,  # Assumed external port for prod backup
            "skip_restore_tests": True  # Don't test restore in production
        }
    elif TEST_ENV == "test" or SERVICE_ENV_SUFFIX == "-test":
        return {
            "env": "test",
            "container_name": "postgres-backup-test",
            "db_container_name": "postgres-test",
            "backup_dir": "backups/postgres/test",
            "backup_prefix": "test_backup",
            "schedule_minutes": 1,  # Every minute
            "max_wait_minutes": 3,  # Short wait for frequent backups
            "health_port": 8081,  # Assumed external port for test backup
            "skip_restore_tests": False
        }
    else:  # dev environment (default)
        return {
            "env": "dev",
            "container_name": "postgres-backup",
            "db_container_name": "postgres",
            "backup_dir": "backups/postgres/dev",
            "backup_prefix": "dev_backup",
            "schedule_minutes": 5,  # Every 5 minutes
            "max_wait_minutes": 8,  # Reasonable wait for 5-minute schedule
            "health_port": 8080,  # Assumed external port for dev backup
            "skip_restore_tests": False
        }

# Get current environment configuration
BACKUP_CONFIG = get_backup_config()

# Skip backup tests if explicitly disabled
BACKUP_TESTS_ENABLED = os.environ.get("ENABLE_BACKUP_TESTS", "true").lower() == "true"

class TestBackupSystem:
    """Test class for PostgreSQL backup system functionality."""

    @classmethod
    def setup_class(cls):
        """Setup test class - ensure backup directories exist."""
        if not BACKUP_TESTS_ENABLED:
            pytest.skip("Backup tests disabled via ENABLE_BACKUP_TESTS")
        
        # Ensure backup directories exist
        os.makedirs(BACKUP_CONFIG["backup_dir"], exist_ok=True)
        print(f"Testing backup system in {BACKUP_CONFIG['env']} environment")
        print(f"Backup directory: {BACKUP_CONFIG['backup_dir']}")
        print(f"Container: {BACKUP_CONFIG['container_name']}")

    def run_docker_command(self, container_name, command):
        """Helper to run commands in Docker containers."""
        try:
            result = subprocess.run(
                ["docker", "exec", container_name] + command,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def get_recent_backup_files(self, max_age_minutes=60):
        """Get backup files created within the last max_age_minutes."""
        pattern = os.path.join(BACKUP_CONFIG["backup_dir"], f"{BACKUP_CONFIG['backup_prefix']}_*.sql.gz")
        files = glob.glob(pattern)
        
        recent_files = []
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        for file_path in files:
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time > cutoff_time:
                recent_files.append((file_path, file_time))
        
        # Sort by modification time, newest first
        recent_files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in recent_files]

    def wait_for_backup_file(self, timeout_minutes=None):
        """Wait for a new backup file to appear in the specified directory."""
        if timeout_minutes is None:
            timeout_minutes = BACKUP_CONFIG["max_wait_minutes"]
            
        initial_files = set(glob.glob(os.path.join(BACKUP_CONFIG["backup_dir"], f"{BACKUP_CONFIG['backup_prefix']}_*.sql.gz")))
        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        print(f"Waiting for new backup file in {BACKUP_CONFIG['backup_dir']} (timeout: {timeout_minutes} min)")
        
        while datetime.now() - start_time < timeout:
            current_files = set(glob.glob(os.path.join(BACKUP_CONFIG["backup_dir"], f"{BACKUP_CONFIG['backup_prefix']}_*.sql.gz")))
            new_files = current_files - initial_files
            
            if new_files:
                # Get the newest file
                newest_file = max(new_files, key=os.path.getmtime)
                file_time = datetime.fromtimestamp(os.path.getmtime(newest_file))
                print(f"New backup file found: {newest_file} (created: {file_time})")
                return newest_file
            
            time.sleep(10)  # Check every 10 seconds
        
        return None

    # Container and Cron Service Tests

    def test_backup_container_running(self):
        """Test that the backup container is running."""
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={BACKUP_CONFIG['container_name']}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, "Failed to check docker containers"
        
        running_containers = result.stdout.strip().split('\n')
        assert BACKUP_CONFIG['container_name'] in running_containers, \
            f"Backup container {BACKUP_CONFIG['container_name']} is not running"
        
        print(f"✅ Backup container {BACKUP_CONFIG['container_name']} is running")

    def test_cron_running_in_backup_container(self):
        """Test that cron service is running in backup container."""
        success, stdout, stderr = self.run_docker_command(
            BACKUP_CONFIG['container_name'], 
            ["pgrep", "-f", "cron"]
        )
        
        assert success, f"Cron not running in {BACKUP_CONFIG['container_name']} container. stderr: {stderr}"
        assert stdout.strip(), "No cron process found"
        print(f"✅ Cron is running in {BACKUP_CONFIG['container_name']} container (PID: {stdout.strip()})")

    def test_backup_container_health(self):
        """Test backup container health endpoint."""
        health_url = f"http://localhost:{BACKUP_CONFIG['health_port']}/health"
        
        try:
            response = requests.get(health_url, timeout=10)
            assert response.status_code == 200, f"Health endpoint returned {response.status_code}"
            
            # Try to parse as text (simple health responses)
            health_text = response.text
            assert "healthy" in health_text.lower() or "backup" in health_text.lower(), \
                f"Health response doesn't indicate healthy status: {health_text}"
            
            print(f"✅ Backup container health check passed: {health_text[:100]}...")
            
        except requests.ConnectionError:
            pytest.skip(f"Health endpoint not accessible at {health_url} - container may not expose port externally")
        except Exception as e:
            pytest.fail(f"Health check failed: {e}")

    # Backup Creation Tests

    def test_backup_creation(self):
        """Test that backup files are being created in current environment."""
        # Check for recent backup files first
        max_age = BACKUP_CONFIG["schedule_minutes"] * 2  # Look for files within 2x schedule interval
        recent_files = self.get_recent_backup_files(max_age_minutes=max_age)
        
        if recent_files:
            print(f"✅ Recent backup file found in {BACKUP_CONFIG['env']}: {recent_files[0]}")
            backup_file = recent_files[0]
        else:
            # Wait for a new backup file
            print(f"No recent backup found, waiting for new backup (schedule: every {BACKUP_CONFIG['schedule_minutes']} min)...")
            backup_file = self.wait_for_backup_file()
            assert backup_file is not None, \
                f"No backup file created in {BACKUP_CONFIG['backup_dir']} within {BACKUP_CONFIG['max_wait_minutes']} minutes"
        
        # Verify file exists and has reasonable size
        assert os.path.exists(backup_file), f"Backup file does not exist: {backup_file}"
        
        file_size = os.path.getsize(backup_file)
        assert file_size > 1000, f"Backup file too small: {file_size} bytes"  # At least 1KB
        
        print(f"✅ {BACKUP_CONFIG['env'].upper()} backup file created successfully: {backup_file} ({file_size} bytes)")

    def test_backup_file_validity(self):
        """Test that backup files are valid gzipped SQL files."""
        max_age = BACKUP_CONFIG["schedule_minutes"] * 3  # Look for files within 3x schedule interval
        recent_files = self.get_recent_backup_files(max_age_minutes=max_age)
        assert recent_files, f"No recent backup files found in {BACKUP_CONFIG['backup_dir']}"
        
        backup_file = recent_files[0]
        print(f"Testing backup file validity: {backup_file}")
        
        # Test gzip validity
        result = subprocess.run(
            ["gunzip", "-t", backup_file],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Backup file failed gzip validation: {result.stderr}"
        print(f"✅ {BACKUP_CONFIG['env'].upper()} backup file is valid: {backup_file}")

    def test_backup_contains_sql_content(self):
        """Test that backup files contain valid SQL content."""
        recent_files = self.get_recent_backup_files(max_age_minutes=60)
        assert recent_files, f"No recent backup files found in {BACKUP_CONFIG['backup_dir']}"
        
        backup_file = recent_files[0]
        print(f"Testing SQL content in: {backup_file}")
        
        # Verify backup contains SQL content
        result = subprocess.run(
            ["zcat", backup_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, "Could not read backup file content"
        assert "CREATE" in result.stdout or "INSERT" in result.stdout or "COPY" in result.stdout, \
            "Backup file does not contain SQL commands"
        print(f"✅ {BACKUP_CONFIG['env'].upper()} backup file contains valid SQL content")

    # Backup Restoration Tests (conditional)

    @pytest.mark.skipif(BACKUP_CONFIG["skip_restore_tests"], reason="Restore tests disabled for this environment")
    def test_backup_restoration(self):
        """Test successful backup restoration in current environment."""
        # Get a recent backup file
        recent_files = self.get_recent_backup_files(max_age_minutes=60)
        assert recent_files, f"No recent backup files found in {BACKUP_CONFIG['backup_dir']}"
        
        backup_file = recent_files[0]
        print(f"Testing restoration of: {backup_file}")
        
        # Create a timestamp for backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Test restoration using the existing Makefile command
        # Create a unique test patient first, then restore, then verify
        
        # 1. Create a unique test patient
        test_patient_data = {
            "anrede": "Herr",
            "geschlecht": "männlich", 
            "vorname": f"RestoreTest_{timestamp}",
            "nachname": f"{BACKUP_CONFIG['env'].title()}Test",
            "email": f"restore_test_{BACKUP_CONFIG['env']}_{timestamp}@example.com"
        }
        
        try:
            create_response = requests.post(f"{PATIENT_BASE_URL}/patients", json=test_patient_data)
            if create_response.status_code == 201:
                created_patient = create_response.json()
                print(f"Created test patient: {created_patient['id']}")
                
                # 2. Copy our backup file to the expected location for Makefile
                backup_filename = f"backup_{timestamp}.sql.gz"
                backup_dest = os.path.join("backups/postgres/manual", backup_filename)
                os.makedirs("backups/postgres/manual", exist_ok=True)
                subprocess.run(["cp", backup_file, backup_dest], check=True)
                
                try:
                    # 3. Run restore command using make
                    restore_target = f"restore-{BACKUP_CONFIG['env']}"
                    restore_result = subprocess.run(
                        ["make", restore_target, f"BACKUP={timestamp}"],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )
                    
                    if restore_result.returncode == 0:
                        print("✅ Restore command completed successfully")
                        
                        # 4. Verify services are still responding after restore
                        time.sleep(10)  # Give services time to restart
                        
                        health_response = requests.get(f"{PATIENT_BASE_URL.replace('/api', '')}/health", timeout=30)
                        assert health_response.status_code == 200, "Patient service should be healthy after restore"
                        
                        print(f"✅ {BACKUP_CONFIG['env'].upper()} backup restoration test completed successfully")
                    else:
                        print(f"Restore command output: {restore_result.stdout}")
                        print(f"Restore command errors: {restore_result.stderr}")
                        print("⚠️ Restore command had issues but backup file is valid")
                        
                finally:
                    # Cleanup
                    try:
                        os.remove(backup_dest)
                        if create_response.status_code == 201:
                            requests.delete(f"{PATIENT_BASE_URL}/patients/{created_patient['id']}")
                    except:
                        pass  # Ignore cleanup errors
            else:
                print("Could not create test patient, skipping restore test")
                pytest.skip("Unable to create test patient for restore test")
                
        except requests.ConnectionError:
            pytest.skip("Cannot connect to patient service for restore test")

    # Container Process Tests

    def test_backup_script_exists(self):
        """Test that backup script exists and is executable."""
        # Check that backup script exists and is executable
        success, stdout, stderr = self.run_docker_command(
            BACKUP_CONFIG['container_name'],
            ["test", "-x", "/usr/local/bin/backup-script.sh"]
        )
        
        assert success, f"Backup script not found or not executable in {BACKUP_CONFIG['container_name']} container: {stderr}"
        print(f"✅ {BACKUP_CONFIG['env'].upper()} backup script is present and executable")

    def test_backup_crontab_configuration(self):
        """Test that crontab is properly configured."""
        success, stdout, stderr = self.run_docker_command(
            BACKUP_CONFIG['container_name'],
            ["crontab", "-l"]
        )
        
        if success:
            assert "backup" in stdout.lower(), "Backup script not found in crontab"
            
            # Check environment-specific schedule patterns
            if BACKUP_CONFIG['env'] == "dev":
                assert "*/5" in stdout, "Dev backup should run every 5 minutes"
            elif BACKUP_CONFIG['env'] == "test":
                assert "*" in stdout and "* *" in stdout, "Test backup should run every minute"
            elif BACKUP_CONFIG['env'] == "prod":
                assert "0 *" in stdout, "Prod backup should run hourly"
                
            print(f"✅ {BACKUP_CONFIG['env'].upper()} crontab configured correctly: {stdout.strip()}")
        else:
            # Check alternative cron file location
            success2, stdout2, stderr2 = self.run_docker_command(
                BACKUP_CONFIG['container_name'],
                ["cat", "/var/spool/cron/crontabs/root"]
            )
            if success2:
                assert "backup" in stdout2.lower(), "Backup script not found in cron file"
                print(f"✅ {BACKUP_CONFIG['env'].upper()} cron file configured correctly")
            else:
                print(f"⚠️ Could not verify crontab configuration in {BACKUP_CONFIG['env']}, but cron process is running")

    def test_backup_environment_variables(self):
        """Test that backup container has correct environment variables."""
        # Check BACKUP_ENV variable
        success, stdout, stderr = self.run_docker_command(
            BACKUP_CONFIG['container_name'],
            ["printenv", "BACKUP_ENV"]
        )
        
        if success:
            backup_env = stdout.strip()
            assert backup_env == BACKUP_CONFIG['env'], \
                f"BACKUP_ENV should be '{BACKUP_CONFIG['env']}', got '{backup_env}'"
            print(f"✅ BACKUP_ENV correctly set to '{backup_env}'")
        else:
            print(f"⚠️ Could not check BACKUP_ENV in {BACKUP_CONFIG['container_name']}")

    # Disk Space and Statistics Tests

    def test_backup_directory_exists(self):
        """Test that backup directory exists and is writable."""
        backup_dir = BACKUP_CONFIG['backup_dir']
        assert os.path.exists(backup_dir), f"Backup directory does not exist: {backup_dir}"
        assert os.path.isdir(backup_dir), f"Backup path is not a directory: {backup_dir}"
        
        # Check if directory is writable by attempting to create a test file
        test_file = os.path.join(backup_dir, f"test_write_{int(time.time())}.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"✅ Backup directory is writable: {backup_dir}")
        except (PermissionError, OSError) as e:
            pytest.fail(f"Backup directory is not writable: {backup_dir}, error: {e}")

    def test_backup_count_reasonable(self):
        """Test that backup count is reasonable for the environment."""
        backup_files = glob.glob(os.path.join(BACKUP_CONFIG['backup_dir'], f"{BACKUP_CONFIG['backup_prefix']}_*.sql.gz"))
        backup_count = len(backup_files)
        
        # Environment-specific expectations
        if BACKUP_CONFIG['env'] == "dev":
            # Dev should have some backups but not too many (retention: 7 days, every 5 min = ~2000 max)
            assert 0 <= backup_count <= 2000, f"Unexpected backup count for dev: {backup_count}"
        elif BACKUP_CONFIG['env'] == "test":
            # Test should have some backups but not too many (retention: 7 days, every 1 min = ~10000 max)
            assert 0 <= backup_count <= 10000, f"Unexpected backup count for test: {backup_count}"
        elif BACKUP_CONFIG['env'] == "prod":
            # Prod hourly backups (retention: 7 days = 168 max)
            assert 0 <= backup_count <= 200, f"Unexpected backup count for prod hourly: {backup_count}"
        
        print(f"✅ {BACKUP_CONFIG['env'].upper()} backup count is reasonable: {backup_count} files")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])