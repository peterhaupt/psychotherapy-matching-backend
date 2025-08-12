"""Pytest fixtures for mocking dependencies in unit tests."""
import sys
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
    
    # Configure mock models
    MockEmail = MagicMock()
    MockPhoneCall = MagicMock()
    mock_models_email.Email = MockEmail
    mock_models_phone_call.PhoneCall = MockPhoneCall
    
    # Configure database components
    MockSessionLocal = MagicMock()
    mock_shared_utils_database.SessionLocal = MockSessionLocal
    
    # Configure Flask components
    mock_parser = MagicMock()
    mock_reqparse = MagicMock()
    mock_reqparse.RequestParser = MagicMock(return_value=mock_parser)
    mock_flask_restful.Resource = MagicMock()
    mock_flask_restful.reqparse = mock_reqparse
    
    # Configure config
    mock_config_obj = MagicMock()
    mock_config_obj.get_service_url = MagicMock(return_value="http://patient-service")
    mock_shared_config.get_config = MagicMock(return_value=mock_config_obj)
    
    # Configure RetryAPIClient
    mock_shared_api_retry_client.RetryAPIClient = MockRetryAPIClient
    
    # Configure logger
    mock_logger = MagicMock()
    mock_logging.getLogger = MagicMock(return_value=mock_logger)
    
    # Return configured mocks for use in tests that need them
    return {
        'MockEmail': MockEmail,
        'MockPhoneCall': MockPhoneCall,
        'MockSessionLocal': MockSessionLocal,
        'mock_parser': mock_parser,
        'MockRetryAPIClient': MockRetryAPIClient,
        'mock_config': mock_config_obj,
        'mock_logger': mock_logger
    }


@pytest.fixture
def get_mocks(mock_all_dependencies):
    """Provide access to the configured mocks for tests that need them."""
    return mock_all_dependencies