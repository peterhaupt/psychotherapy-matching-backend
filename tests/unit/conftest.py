"""Pytest fixtures for mocking dependencies in unit tests."""
import pytest
from unittest.mock import MagicMock, Mock


class MockRetryAPIClient:
    """Mock implementation of RetryAPIClient for testing."""
    
    @classmethod
    def call_with_retry(cls, method, url, json=None, timeout=10):
        pass


@pytest.fixture(autouse=True)
def mock_all_dependencies(monkeypatch):
    """Automatically mock all external dependencies for every test."""
    
    # Mock all the base modules
    mock_models = MagicMock()
    mock_models_email = MagicMock()
    mock_models_phone_call = MagicMock()
    mock_shared = MagicMock()
    mock_shared_utils = MagicMock()
    mock_shared_utils_database = MagicMock()
    mock_shared_config = MagicMock()
    mock_shared_api = MagicMock()
    mock_shared_api_base_resource = MagicMock()
    mock_shared_api_retry_client = MagicMock()
    mock_flask = MagicMock()
    mock_flask_restful = MagicMock()
    mock_sqlalchemy = MagicMock()
    mock_sqlalchemy_exc = MagicMock()
    mock_sqlalchemy_orm = MagicMock()
    mock_requests = MagicMock()
    mock_logging = MagicMock()
    
    # Set up module structure
    monkeypatch.setitem(sys.modules, 'models', mock_models)
    monkeypatch.setitem(sys.modules, 'models.email', mock_models_email)
    monkeypatch.setitem(sys.modules, 'models.phone_call', mock_models_phone_call)
    monkeypatch.setitem(sys.modules, 'shared', mock_shared)
    monkeypatch.setitem(sys.modules, 'shared.utils', mock_shared_utils)
    monkeypatch.setitem(sys.modules, 'shared.utils.database', mock_shared_utils_database)
    monkeypatch.setitem(sys.modules, 'shared.config', mock_shared_config)
    monkeypatch.setitem(sys.modules, 'shared.api', mock_shared_api)
    monkeypatch.setitem(sys.modules, 'shared.api.base_resource', mock_shared_api_base_resource)
    monkeypatch.setitem(sys.modules, 'shared.api.retry_client', mock_shared_api_retry_client)
    monkeypatch.setitem(sys.modules, 'flask', mock_flask)
    monkeypatch.setitem(sys.modules, 'flask_restful', mock_flask_restful)
    monkeypatch.setitem(sys.modules, 'sqlalchemy', mock_sqlalchemy)
    monkeypatch.setitem(sys.modules, 'sqlalchemy.exc', mock_sqlalchemy_exc)
    monkeypatch.setitem(sys.modules, 'sqlalchemy.orm', mock_sqlalchemy_orm)
    monkeypatch.setitem(sys.modules, 'requests', mock_requests)
    monkeypatch.setitem(sys.modules, 'logging', mock_logging)
    
    # Return configured mocks for use in tests
    return {
        'models': mock_models,
        'models_email': mock_models_email,
        'models_phone_call': mock_models_phone_call,
        'shared_utils_database': mock_shared_utils_database,
        'shared_config': mock_shared_config,
        'shared_api_retry_client': mock_shared_api_retry_client,
        'flask_restful': mock_flask_restful,
        'logging': mock_logging
    }


@pytest.fixture
def mock_email_model(mock_all_dependencies):
    """Fixture for mocked Email model."""
    MockEmail = MagicMock()
    mock_all_dependencies['models_email'].Email = MockEmail
    return MockEmail


@pytest.fixture
def mock_phone_call_model(mock_all_dependencies):
    """Fixture for mocked PhoneCall model."""
    MockPhoneCall = MagicMock()
    mock_all_dependencies['models_phone_call'].PhoneCall = MockPhoneCall
    return MockPhoneCall


@pytest.fixture
def mock_session_local(mock_all_dependencies):
    """Fixture for mocked SessionLocal."""
    MockSessionLocal = MagicMock()
    mock_all_dependencies['shared_utils_database'].SessionLocal = MockSessionLocal
    return MockSessionLocal


@pytest.fixture
def mock_retry_api_client(mock_all_dependencies):
    """Fixture for mocked RetryAPIClient."""
    mock_all_dependencies['shared_api_retry_client'].RetryAPIClient = MockRetryAPIClient
    return MockRetryAPIClient


@pytest.fixture
def mock_request_parser(mock_all_dependencies):
    """Fixture for mocked Flask-RESTful request parser."""
    mock_parser = MagicMock()
    mock_reqparse = MagicMock()
    mock_reqparse.RequestParser = MagicMock(return_value=mock_parser)
    mock_all_dependencies['flask_restful'].reqparse = mock_reqparse
    mock_all_dependencies['flask_restful'].Resource = MagicMock()
    return mock_parser


@pytest.fixture
def mock_config(mock_all_dependencies):
    """Fixture for mocked configuration."""
    mock_config_obj = MagicMock()
    mock_config_obj.get_service_url = MagicMock(return_value="http://patient-service")
    mock_all_dependencies['shared_config'].get_config = MagicMock(return_value=mock_config_obj)
    return mock_config_obj


@pytest.fixture
def mock_logger(mock_all_dependencies):
    """Fixture for mocked logger."""
    logger = MagicMock()
    mock_all_dependencies['logging'].getLogger = MagicMock(return_value=logger)
    return logger


@pytest.fixture
def mock_date(monkeypatch):
    """Fixture for mocking datetime.date."""
    from unittest.mock import Mock
    mock_date_obj = Mock()
    mock_date_obj.today.return_value.isoformat.return_value = '2025-01-15'
    return mock_date_obj


import sys