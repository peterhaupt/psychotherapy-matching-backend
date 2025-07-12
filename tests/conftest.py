"""Pytest configuration for environment-specific testing.

This conftest.py file allows switching between different environment files
when running tests using the --env option.

Usage:
    pytest --env=dev tests/integration/test_database_schemas.py -v
    pytest --env=test tests/integration/test_database_schemas.py -v  
    pytest --env=prod tests/integration/test_database_schemas.py -v
    pytest tests/integration/test_database_schemas.py -v  # defaults to dev
"""
import os
import pytest
from dotenv import load_dotenv


def pytest_addoption(parser):
    """Add custom command line option for environment selection."""
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        choices=["dev", "test", "prod"],
        help="Environment to use for testing (dev, test, prod). Defaults to 'dev'."
    )


def pytest_configure(config):
    """Load environment file based on --env option."""
    env = config.getoption("--env")
    env_file = f'.env.{env}'
    
    # Get the project root directory (one level up from tests/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file_path = os.path.join(project_root, env_file)
    
    if os.path.exists(env_file_path):
        load_dotenv(env_file_path)
        print(f"\n✅ Loaded environment file: {env_file}")
    else:
        print(f"\n❌ Warning: {env_file} not found at {env_file_path}")
        
        # Try to load default .env as fallback
        default_env_path = os.path.join(project_root, '.env')
        if os.path.exists(default_env_path):
            load_dotenv(default_env_path)
            print(f"📄 Fallback: Loaded default .env file")
        else:
            print(f"⚠️  No environment files found. Using system environment variables only.")
    
    # Override Docker hostnames to localhost for local testing
    # This allows tests to connect to Docker containers from host machine
    os.environ['DB_HOST'] = 'localhost'
    os.environ['PGBOUNCER_HOST'] = 'localhost'
    print(f"🔧 Overridden DB_HOST and PGBOUNCER_HOST to 'localhost' for local testing")


def pytest_report_header(config):
    """Add environment info to pytest header."""
    env = config.getoption("--env")
    return f"Environment: {env}"


# Optional: Add a fixture that tests can use to access the current environment
@pytest.fixture(scope="session")
def test_environment(request):
    """Fixture that provides the current test environment name."""
    return request.config.getoption("--env")


# Optional: Add a fixture for database configuration validation
@pytest.fixture(scope="session", autouse=True)
def validate_test_environment(request):
    """Automatically validate that required environment variables are set."""
    env = request.config.getoption("--env")
    
    # Only validate for integration tests that need database
    if "integration" in str(request.node.fspath):
        required_vars = ["DB_USER", "DB_PASSWORD", "DB_NAME", "DB_HOST"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            pytest.fail(
                f"Missing required environment variables for {env} environment: "
                f"{', '.join(missing_vars)}. "
                f"Please check your .env.{env} file."
            )
        
        print(f"✅ Database config validated for {env} environment")
