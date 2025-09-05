"""Centralized configuration module for all services.

This module provides a single source of truth for all configuration values
across the microservices architecture. It reads from environment variables
with NO defaults - all required values must be explicitly set.

Phase 3.1: Removed all default values and added validation.
Updated: Added Object Storage (Swift) configuration, removed GCS
"""
import os
import logging
from typing import Optional, List, Dict, Set

def _get_env_bool(var_name: str) -> Optional[bool]:
    """Convert environment variable to boolean, return None if not set."""
    value = os.environ.get(var_name)
    if value is None:
        return None
    return value.lower() in ('true', '1', 'yes', 'on')


def _get_env_int(var_name: str) -> Optional[int]:
    """Convert environment variable to integer, return None if not set."""
    value = os.environ.get(var_name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {var_name} must be a valid integer, got: {value}")


def _get_env_float(var_name: str) -> Optional[float]:
    """Convert environment variable to float, return None if not set."""
    value = os.environ.get(var_name)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Environment variable {var_name} must be a valid float, got: {value}")


def _get_env_list(var_name: str, separator: str = ",") -> Optional[List[str]]:
    """Convert environment variable to list, return None if not set."""
    value = os.environ.get(var_name)
    if value is None:
        return None
    return [item.strip() for item in value.split(separator) if item.strip()]


class Config:
    """Base configuration class with NO default values.
    
    All configuration must be provided via environment variables.
    Use validate() method to check required variables are set.
    """
    
    # Critical Infrastructure - Required for all services
    DB_USER: Optional[str] = os.environ.get("DB_USER")
    DB_PASSWORD: Optional[str] = os.environ.get("DB_PASSWORD")
    DB_NAME: Optional[str] = os.environ.get("DB_NAME")
    DB_HOST: Optional[str] = os.environ.get("DB_HOST")
    DB_PORT: Optional[int] = _get_env_int("DB_PORT")
    
    # External port mappings (for host-side connections)
    DB_EXTERNAL_PORT: Optional[int] = _get_env_int("DB_EXTERNAL_PORT")
    PGBOUNCER_EXTERNAL_PORT: Optional[int] = _get_env_int("PGBOUNCER_EXTERNAL_PORT")
    
    # PgBouncer Configuration
    PGBOUNCER_HOST: Optional[str] = os.environ.get("PGBOUNCER_HOST")
    PGBOUNCER_PORT: Optional[int] = _get_env_int("PGBOUNCER_PORT")
    PGBOUNCER_ADMIN_USER: Optional[str] = os.environ.get("PGBOUNCER_ADMIN_USER")
    PGBOUNCER_ADMIN_PASSWORD: Optional[str] = os.environ.get("PGBOUNCER_ADMIN_PASSWORD")
    
    # Environment Settings
    FLASK_ENV: Optional[str] = os.environ.get("FLASK_ENV")
    FLASK_DEBUG: Optional[bool] = _get_env_bool("FLASK_DEBUG")
    LOG_LEVEL: Optional[str] = os.environ.get("LOG_LEVEL")
    SERVICE_ENV_SUFFIX: Optional[str] = os.environ.get("SERVICE_ENV_SUFFIX")
    SERVICE_HOST: Optional[str] = os.environ.get("SERVICE_HOST")
    
    # Service Ports
    PATIENT_SERVICE_PORT: Optional[int] = _get_env_int("PATIENT_SERVICE_PORT")
    THERAPIST_SERVICE_PORT: Optional[int] = _get_env_int("THERAPIST_SERVICE_PORT")
    MATCHING_SERVICE_PORT: Optional[int] = _get_env_int("MATCHING_SERVICE_PORT")
    COMMUNICATION_SERVICE_PORT: Optional[int] = _get_env_int("COMMUNICATION_SERVICE_PORT")
    GEOCODING_SERVICE_PORT: Optional[int] = _get_env_int("GEOCODING_SERVICE_PORT")
    SCRAPING_SERVICE_PORT: Optional[int] = _get_env_int("SCRAPING_SERVICE_PORT")

    # Internal Docker ports (fixed across environments)
    PATIENT_SERVICE_INTERNAL_PORT: Optional[int] = _get_env_int("PATIENT_SERVICE_INTERNAL_PORT")
    THERAPIST_SERVICE_INTERNAL_PORT: Optional[int] = _get_env_int("THERAPIST_SERVICE_INTERNAL_PORT")
    MATCHING_SERVICE_INTERNAL_PORT: Optional[int] = _get_env_int("MATCHING_SERVICE_INTERNAL_PORT")
    COMMUNICATION_SERVICE_INTERNAL_PORT: Optional[int] = _get_env_int("COMMUNICATION_SERVICE_INTERNAL_PORT")
    GEOCODING_SERVICE_INTERNAL_PORT: Optional[int] = _get_env_int("GEOCODING_SERVICE_INTERNAL_PORT")
    
    # CORS Configuration
    CORS_ALLOWED_ORIGINS: Optional[List[str]] = _get_env_list("CORS_ALLOWED_ORIGINS")
    CORS_SUPPORTS_CREDENTIALS: Optional[bool] = _get_env_bool("CORS_SUPPORTS_CREDENTIALS")
    
    # Email Configuration (Communication Service)
    SMTP_HOST: Optional[str] = os.environ.get("SMTP_HOST")
    SMTP_PORT: Optional[int] = _get_env_int("SMTP_PORT")
    SMTP_USERNAME: Optional[str] = os.environ.get("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.environ.get("SMTP_PASSWORD")
    SMTP_USE_TLS: Optional[bool] = _get_env_bool("SMTP_USE_TLS")
    EMAIL_SENDER: Optional[str] = os.environ.get("EMAIL_SENDER")
    EMAIL_SENDER_NAME: Optional[str] = os.environ.get("EMAIL_SENDER_NAME")
    EMAIL_ADD_LEGAL_FOOTER: Optional[bool] = _get_env_bool("EMAIL_ADD_LEGAL_FOOTER")
    
    # Company Information
    COMPANY_NAME: Optional[str] = os.environ.get("COMPANY_NAME")
    COMPANY_STREET: Optional[str] = os.environ.get("COMPANY_STREET")
    COMPANY_PLZ: Optional[str] = os.environ.get("COMPANY_PLZ")
    COMPANY_CITY: Optional[str] = os.environ.get("COMPANY_CITY")
    COMPANY_COUNTRY: Optional[str] = os.environ.get("COMPANY_COUNTRY")
    COMPANY_CEO: Optional[str] = os.environ.get("COMPANY_CEO")
    COMPANY_HRB: Optional[str] = os.environ.get("COMPANY_HRB")
    LEGAL_FOOTER_PRIVACY_TEXT: Optional[str] = os.environ.get("LEGAL_FOOTER_PRIVACY_TEXT")
    
    # System Notifications
    SYSTEM_NOTIFICATION_EMAIL: Optional[str] = os.environ.get("SYSTEM_NOTIFICATION_EMAIL")
    
    # Patient Service Configuration
    PATIENT_IMPORT_LOCAL_PATH: Optional[str] = os.environ.get("PATIENT_IMPORT_LOCAL_PATH")
    PATIENT_IMPORT_CHECK_INTERVAL_SECONDS: Optional[int] = _get_env_int("PATIENT_IMPORT_CHECK_INTERVAL_SECONDS")
    
    # Object Storage Configuration (Swift/OpenStack for Infomaniak)
    SWIFT_APPLICATION_ID: Optional[str] = os.environ.get("SWIFT_APPLICATION_ID")
    SWIFT_APPLICATION_SECRET: Optional[str] = os.environ.get("SWIFT_APPLICATION_SECRET")
    HMAC_SECRET_KEY: Optional[str] = os.environ.get("HMAC_SECRET_KEY")
    
    # Therapist Service Configuration
    THERAPIST_IMPORT_FOLDER_PATH: Optional[str] = os.environ.get("THERAPIST_IMPORT_FOLDER_PATH")
    THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS: Optional[int] = _get_env_int("THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS")
    THERAPIST_IMPORT_ENABLED: Optional[bool] = _get_env_bool("THERAPIST_IMPORT_ENABLED")
    
    # Matching Service Configuration
    MAX_ANFRAGE_SIZE: Optional[int] = _get_env_int("MAX_ANFRAGE_SIZE")
    MIN_ANFRAGE_SIZE: Optional[int] = _get_env_int("MIN_ANFRAGE_SIZE")
    PLZ_MATCH_DIGITS: Optional[int] = _get_env_int("PLZ_MATCH_DIGITS")
    DEFAULT_MAX_DISTANCE_KM: Optional[int] = _get_env_int("DEFAULT_MAX_DISTANCE_KM")
    FOLLOW_UP_THRESHOLD_DAYS: Optional[int] = _get_env_int("FOLLOW_UP_THRESHOLD_DAYS")
    DEFAULT_PHONE_CALL_TIME: Optional[str] = os.environ.get("DEFAULT_PHONE_CALL_TIME")
    MATCHING_FALLBACK_TIME_MORNING: Optional[str] = os.environ.get("MATCHING_FALLBACK_TIME_MORNING")
    MATCHING_FALLBACK_TIME_AFTERNOON: Optional[str] = os.environ.get("MATCHING_FALLBACK_TIME_AFTERNOON")
    MATCHING_CALL_DURATION_SHORT: Optional[int] = _get_env_int("MATCHING_CALL_DURATION_SHORT")
    MATCHING_CALL_DURATION_STANDARD: Optional[int] = _get_env_int("MATCHING_CALL_DURATION_STANDARD")
    MATCHING_TOMORROW_OFFSET_DAYS: Optional[int] = _get_env_int("MATCHING_TOMORROW_OFFSET_DAYS")
    
    # Communication Service Configuration
    COMMUNICATION_EMAIL_BATCH_LIMIT: Optional[int] = _get_env_int("COMMUNICATION_EMAIL_BATCH_LIMIT")
    COMMUNICATION_TIMEOUT_SHORT: Optional[int] = _get_env_int("COMMUNICATION_TIMEOUT_SHORT")
    COMMUNICATION_TIMEOUT_LONG: Optional[int] = _get_env_int("COMMUNICATION_TIMEOUT_LONG")
    EMAIL_QUEUE_CHECK_INTERVAL_SECONDS: Optional[int] = _get_env_int("EMAIL_QUEUE_CHECK_INTERVAL_SECONDS")
    EMAIL_QUEUE_BATCH_SIZE: Optional[int] = _get_env_int("EMAIL_QUEUE_BATCH_SIZE")
    
    # Geocoding Service Configuration
    OSM_API_URL: Optional[str] = os.environ.get("OSM_API_URL")
    OSM_USER_AGENT: Optional[str] = os.environ.get("OSM_USER_AGENT")
    OSM_TIMEOUT: Optional[int] = _get_env_int("OSM_TIMEOUT")
    OSM_MAX_RETRIES: Optional[int] = _get_env_int("OSM_MAX_RETRIES")
    OSM_RATE_LIMIT: Optional[float] = _get_env_float("OSM_RATE_LIMIT")
    OSRM_API_URL: Optional[str] = os.environ.get("OSRM_API_URL")
    OSRM_PROFILE_CAR: Optional[str] = os.environ.get("OSRM_PROFILE_CAR")
    OSRM_PROFILE_TRANSIT: Optional[str] = os.environ.get("OSRM_PROFILE_TRANSIT")
    CACHE_TTL_SECONDS: Optional[int] = _get_env_int("CACHE_TTL_SECONDS")
    CACHE_MAX_SIZE: Optional[int] = _get_env_int("CACHE_MAX_SIZE")
    GEOCODING_REQUEST_TIMEOUT: Optional[int] = _get_env_int("GEOCODING_REQUEST_TIMEOUT")
    GEOCODING_RETRY_DELAY_BASE: Optional[int] = _get_env_int("GEOCODING_RETRY_DELAY_BASE")
    GEOCODING_RATE_LIMIT_SLEEP: Optional[int] = _get_env_int("GEOCODING_RATE_LIMIT_SLEEP")
    GEOCODING_COORDINATE_PRECISION: Optional[int] = _get_env_int("GEOCODING_COORDINATE_PRECISION")
    
    # Security Configuration
    SECRET_KEY: Optional[str] = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY: Optional[str] = os.environ.get("JWT_SECRET_KEY")
    SESSION_LIFETIME_MINUTES: Optional[int] = _get_env_int("SESSION_LIFETIME_MINUTES")
    SESSION_COOKIE_SECURE: Optional[bool] = _get_env_bool("SESSION_COOKIE_SECURE")
    SESSION_COOKIE_HTTPONLY: Optional[bool] = _get_env_bool("SESSION_COOKIE_HTTPONLY")
    
    # Feature Flags
    ENABLE_SCRAPING: Optional[bool] = _get_env_bool("ENABLE_SCRAPING")
    ENABLE_EMAIL_SENDING: Optional[bool] = _get_env_bool("ENABLE_EMAIL_SENDING")
    ENABLE_PHONE_SCHEDULING: Optional[bool] = _get_env_bool("ENABLE_PHONE_SCHEDULING")
    
    # Rate Limiting
    API_RATE_LIMIT_PER_MINUTE: Optional[int] = _get_env_int("API_RATE_LIMIT_PER_MINUTE")
    API_RATE_LIMIT_PER_HOUR: Optional[int] = _get_env_int("API_RATE_LIMIT_PER_HOUR")
    
    # Development Tools
    ENABLE_DEBUG_TOOLBAR: Optional[bool] = _get_env_bool("ENABLE_DEBUG_TOOLBAR")
    ENABLE_PROFILING: Optional[bool] = _get_env_bool("ENABLE_PROFILING")
    SQL_ECHO: Optional[bool] = _get_env_bool("SQL_ECHO")
    
    # Monitoring and Logging
    SENTRY_DSN: Optional[str] = os.environ.get("SENTRY_DSN")
    ENABLE_PERFORMANCE_MONITORING: Optional[bool] = _get_env_bool("ENABLE_PERFORMANCE_MONITORING")
    
    # Frontend Configuration (for reference by backend services if needed)
    REACT_APP_USE_MOCK_DATA: Optional[bool] = _get_env_bool("REACT_APP_USE_MOCK_DATA")
    REACT_APP_PATIENT_API: Optional[str] = os.environ.get("REACT_APP_PATIENT_API")
    REACT_APP_THERAPIST_API: Optional[str] = os.environ.get("REACT_APP_THERAPIST_API")
    REACT_APP_MATCHING_API: Optional[str] = os.environ.get("REACT_APP_MATCHING_API")
    REACT_APP_COMMUNICATION_API: Optional[str] = os.environ.get("REACT_APP_COMMUNICATION_API")
    REACT_APP_GEOCODING_API: Optional[str] = os.environ.get("REACT_APP_GEOCODING_API")
    
    # Define required variables by service
    REQUIRED_CORE_VARS: Set[str] = {
        "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_HOST", "DB_PORT",
        "FLASK_ENV", "LOG_LEVEL"
    }
    
    REQUIRED_BY_SERVICE: Dict[str, Set[str]] = {
        "patient": {
            "PATIENT_SERVICE_PORT",
            "PATIENT_IMPORT_LOCAL_PATH",
            "PATIENT_IMPORT_CHECK_INTERVAL_SECONDS",
            # Object Storage credentials required
            "SWIFT_APPLICATION_ID",
            "SWIFT_APPLICATION_SECRET",
            "HMAC_SECRET_KEY"
        },
        "therapist": {
            "THERAPIST_SERVICE_PORT",
            "THERAPIST_IMPORT_FOLDER_PATH", "THERAPIST_IMPORT_CHECK_INTERVAL_SECONDS"
        },
        "matching": {
            "MATCHING_SERVICE_PORT",
            "MAX_ANFRAGE_SIZE", "MIN_ANFRAGE_SIZE", "PLZ_MATCH_DIGITS",
            "FOLLOW_UP_THRESHOLD_DAYS", "DEFAULT_PHONE_CALL_TIME"
        },
        "communication": {
            "COMMUNICATION_SERVICE_PORT",
            "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD",
            "EMAIL_SENDER", "EMAIL_SENDER_NAME", "SYSTEM_NOTIFICATION_EMAIL",
            # Object Storage credentials required for processing emails
            "SWIFT_APPLICATION_ID",
            "SWIFT_APPLICATION_SECRET",
            "HMAC_SECRET_KEY"
        },
        "geocoding": {
            "GEOCODING_SERVICE_PORT",
            "OSM_API_URL", "OSM_USER_AGENT", "OSRM_API_URL"
        }
    }
    
    @classmethod
    def validate(cls, service_name: Optional[str] = None) -> None:
        """Validate that all required environment variables are set.
        
        Args:
            service_name: Optional service name for service-specific validation
            
        Raises:
            ValueError: If required environment variables are missing
        """
        missing_vars = []
        
        # Check core required variables
        for var_name in cls.REQUIRED_CORE_VARS:
            if getattr(cls, var_name) is None:
                missing_vars.append(var_name)
        
        # Check service-specific required variables
        if service_name and service_name in cls.REQUIRED_BY_SERVICE:
            for var_name in cls.REQUIRED_BY_SERVICE[service_name]:
                if getattr(cls, var_name) is None:
                    missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables{' for ' + service_name if service_name else ''}: "
                f"{', '.join(sorted(missing_vars))}"
            )
    
    @classmethod
    def get_database_uri(cls, use_pgbouncer: bool = True, external_url: bool = False) -> str:
        """Get the database connection URI.
        
        Args:
            use_pgbouncer: Whether to connect through PgBouncer (default: True)
            external_url: Whether to use external ports for connections outside Docker (default: False)
            
        Returns:
            PostgreSQL connection string
            
        Raises:
            ValueError: If required database variables are not set
        """
        if use_pgbouncer:
            # Determine which host and port to use
            if external_url:
                host = "localhost"  # External connections use localhost
                port = cls.PGBOUNCER_EXTERNAL_PORT
                required_vars = [cls.DB_USER, cls.DB_PASSWORD, cls.DB_NAME, port]
                if not all(required_vars):
                    raise ValueError("Database configuration incomplete for external PgBouncer connection")
            else:
                host = cls.PGBOUNCER_HOST
                port = cls.PGBOUNCER_PORT
                required_vars = [cls.DB_USER, cls.DB_PASSWORD, cls.PGBOUNCER_HOST, cls.PGBOUNCER_PORT, cls.DB_NAME]
                if not all(required_vars):
                    raise ValueError("Database configuration incomplete for PgBouncer connection")
            
            return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{host}:{port}/{cls.DB_NAME}"
        else:
            # Determine which host and port to use
            if external_url:
                host = "localhost"  # External connections use localhost
                port = cls.DB_EXTERNAL_PORT
                required_vars = [cls.DB_USER, cls.DB_PASSWORD, cls.DB_NAME, port]
                if not all(required_vars):
                    raise ValueError("Database configuration incomplete for external direct connection")
            else:
                host = cls.DB_HOST
                port = cls.DB_PORT
                required_vars = [cls.DB_USER, cls.DB_PASSWORD, cls.DB_HOST, cls.DB_PORT, cls.DB_NAME]
                if not all(required_vars):
                    raise ValueError("Database configuration incomplete for direct connection")
            
            return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{host}:{port}/{cls.DB_NAME}"
    
    @classmethod
    def get_service_url(cls, service: str, internal: bool = True) -> str:
        """Get the URL for a specific service.
        
        Args:
            service: Service name (patient, therapist, matching, communication, geocoding)
            internal: Whether to return internal (Docker) or external URL
            
        Returns:
            Service URL
            
        Raises:
            ValueError: If service is unknown or port not configured
        """
        # Map service names to hostnames and both internal/external ports
        service_map = {
            "patient": ("patient_service", cls.PATIENT_SERVICE_INTERNAL_PORT, cls.PATIENT_SERVICE_PORT),
            "therapist": ("therapist_service", cls.THERAPIST_SERVICE_INTERNAL_PORT, cls.THERAPIST_SERVICE_PORT),
            "matching": ("matching_service", cls.MATCHING_SERVICE_INTERNAL_PORT, cls.MATCHING_SERVICE_PORT),
            "communication": ("communication_service", cls.COMMUNICATION_SERVICE_INTERNAL_PORT, cls.COMMUNICATION_SERVICE_PORT),
            "geocoding": ("geocoding_service", cls.GEOCODING_SERVICE_INTERNAL_PORT, cls.GEOCODING_SERVICE_PORT),
        }
        
        if service not in service_map:
            raise ValueError(f"Unknown service: {service}")
        
        hostname, internal_port, external_port = service_map[service]
        
        if internal:
            port = internal_port
            if port is None:
                raise ValueError(f"Internal port not configured for service: {service}")
            # Add service suffix if configured
            if cls.SERVICE_ENV_SUFFIX:
                hostname = f"{hostname}{cls.SERVICE_ENV_SUFFIX}"
            return f"http://{hostname}:{port}"
        else:
            port = external_port
            if port is None:
                raise ValueError(f"External port not configured for service: {service}")
            return f"http://localhost:{port}"
    
    @classmethod
    def get_smtp_settings(cls) -> dict:
        """Get SMTP settings as a dictionary.
        
        Returns:
            Dictionary with SMTP configuration
            
        Raises:
            ValueError: If required SMTP settings are missing
        """
        required_smtp = ["SMTP_HOST", "SMTP_PORT", "EMAIL_SENDER"]
        missing = [var for var in required_smtp if getattr(cls, var) is None]
        if missing:
            raise ValueError(f"Missing required SMTP settings: {', '.join(missing)}")
        
        return {
            "host": cls.SMTP_HOST,
            "port": cls.SMTP_PORT,
            "username": cls.SMTP_USERNAME or "",
            "password": cls.SMTP_PASSWORD or "",
            "use_tls": cls.SMTP_USE_TLS or False,
            "sender": cls.EMAIL_SENDER,
            "sender_name": cls.EMAIL_SENDER_NAME or cls.EMAIL_SENDER
        }
    
    @classmethod
    def get_cors_settings(cls) -> dict:
        """Get CORS settings as a dictionary.
        
        Returns:
            Dictionary with CORS configuration
        """
        return {
            "origins": cls.CORS_ALLOWED_ORIGINS or ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": cls.CORS_SUPPORTS_CREDENTIALS or False
        }
    
    @classmethod
    def get_anfrage_config(cls) -> Dict[str, int]:
        """Get Anfrage (Inquiry) configuration as a dictionary.
        
        Returns:
            Dictionary with Anfrage-related configuration
            
        Raises:
            ValueError: If required Anfrage settings are missing
        """
        required_anfrage = ["MAX_ANFRAGE_SIZE", "MIN_ANFRAGE_SIZE", "PLZ_MATCH_DIGITS"]
        missing = [var for var in required_anfrage if getattr(cls, var) is None]
        if missing:
            raise ValueError(f"Missing required Anfrage settings: {', '.join(missing)}")
        
        return {
            "max_size": cls.MAX_ANFRAGE_SIZE,
            "min_size": cls.MIN_ANFRAGE_SIZE,
            "plz_match_digits": cls.PLZ_MATCH_DIGITS,
            "default_max_distance_km": cls.DEFAULT_MAX_DISTANCE_KM or 25
        }
    
    @classmethod
    def get_follow_up_config(cls) -> Dict[str, any]:
        """Get follow-up configuration as a dictionary.
        
        Returns:
            Dictionary with follow-up related configuration
        """
        return {
            "threshold_days": cls.FOLLOW_UP_THRESHOLD_DAYS or 7,
            "default_call_time": cls.DEFAULT_PHONE_CALL_TIME or "12:00"
        }


class DevelopmentConfig(Config):
    """Development-specific configuration with safe defaults for dev tools."""
    
    @classmethod
    def get_cors_settings(cls) -> dict:
        """Override CORS for development with permissive defaults."""
        base_settings = super().get_cors_settings()
        if not cls.CORS_ALLOWED_ORIGINS:
            base_settings["origins"] = ["http://localhost:3000", "http://localhost:8080"]
        return base_settings


class ProductionConfig(Config):
    """Production-specific configuration with strict validation."""
    
    REQUIRED_PRODUCTION_VARS: Set[str] = {
        "SECRET_KEY", "JWT_SECRET_KEY", "SYSTEM_NOTIFICATION_EMAIL"
    }
    
    @classmethod
    def validate(cls, service_name: Optional[str] = None) -> None:
        """Enhanced validation for production environment."""
        # Call parent validation first
        super().validate(service_name)
        
        # Check production-specific requirements
        missing_vars = []
        for var_name in cls.REQUIRED_PRODUCTION_VARS:
            if getattr(cls, var_name) is None:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required production environment variables: {', '.join(missing_vars)}")
        
        # Validate security settings
        if cls.SECRET_KEY and len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        
        if cls.JWT_SECRET_KEY and len(cls.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")


class TestConfig(Config):
    """Test-specific configuration."""
    pass


# Select configuration based on FLASK_ENV
env = os.environ.get("FLASK_ENV")

if env == "production":
    config = ProductionConfig()
elif env == "test":
    config = TestConfig()
else:
    config = DevelopmentConfig()


# Convenience function for services to import
def get_config() -> Config:
    """Get the current configuration object.
    
    Returns:
        Configuration object based on current environment
    """
    return config


def setup_logging(service_name: str = "unknown-service") -> None:
    """Set up centralized logging configuration for all services.
    
    This function:
    - Sets up basic logging configuration with the configured format
    - Sets the root logger to the configured LOG_LEVEL
    - Allows service-specific loggers to use their own levels
    
    Args:
        service_name: Name of the service for identification in logs
    """
    # Get the current configuration
    current_config = get_config()
    
    # Use INFO as fallback if LOG_LEVEL not set
    log_level_name = current_config.LOG_LEVEL or "INFO"
    root_level = getattr(logging, log_level_name, logging.INFO)
    
    # In debug mode, use DEBUG for root logger; otherwise use configured level
    if current_config.FLASK_DEBUG:
        root_level = logging.DEBUG
    
    # Set up basic logging configuration
    logging.basicConfig(
        level=root_level,
        format=f'%(asctime)s - {service_name} - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Log the configuration for debugging
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {service_name}")
    logger.info(f"Root log level: {logging.getLevelName(root_level)}")
    logger.debug("This is a debug message - you should see this in debug mode")