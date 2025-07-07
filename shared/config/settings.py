"""Centralized configuration module for all services.

This module provides a single source of truth for all configuration values
across the microservices architecture. It reads from environment variables
with sensible defaults for development.
"""
import os
import logging
from typing import Optional, List, Dict

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root (two levels up from shared/config/)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, rely on environment variables only
    pass


class Config:
    """Base configuration class with common settings."""
    
    # Database Configuration
    DB_USER: str = os.environ.get("DB_USER", "your_db_user")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "your_secure_password")
    DB_NAME: str = os.environ.get("DB_NAME", "therapy_platform")
    DB_HOST: str = os.environ.get("DB_HOST", "postgres")
    DB_PORT: int = int(os.environ.get("DB_PORT", "5432"))
    
    # PgBouncer Configuration
    PGBOUNCER_HOST: str = os.environ.get("PGBOUNCER_HOST", "pgbouncer")
    PGBOUNCER_PORT: int = int(os.environ.get("PGBOUNCER_PORT", "6432"))
    PGBOUNCER_ADMIN_USER: str = os.environ.get("PGBOUNCER_ADMIN_USER", os.environ.get("DB_USER", "your_db_user"))
    PGBOUNCER_ADMIN_PASSWORD: str = os.environ.get("PGBOUNCER_ADMIN_PASSWORD", os.environ.get("DB_PASSWORD", "your_secure_password"))
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_ZOOKEEPER_CONNECT: str = os.environ.get("KAFKA_ZOOKEEPER_CONNECT", "zookeeper:2181")
    KAFKA_LOG_LEVEL: str = os.environ.get("KAFKA_LOG_LEVEL", "WARNING")  # NEW: Separate Kafka log level
    
    # Service Ports
    PATIENT_SERVICE_PORT: int = int(os.environ.get("PATIENT_SERVICE_PORT", "8001"))
    THERAPIST_SERVICE_PORT: int = int(os.environ.get("THERAPIST_SERVICE_PORT", "8002"))
    MATCHING_SERVICE_PORT: int = int(os.environ.get("MATCHING_SERVICE_PORT", "8003"))
    COMMUNICATION_SERVICE_PORT: int = int(os.environ.get("COMMUNICATION_SERVICE_PORT", "8004"))
    GEOCODING_SERVICE_PORT: int = int(os.environ.get("GEOCODING_SERVICE_PORT", "8005"))
    SCRAPING_SERVICE_PORT: int = int(os.environ.get("SCRAPING_SERVICE_PORT", "8006"))
    
    # Application Settings
    FLASK_ENV: str = os.environ.get("FLASK_ENV", "development")
    FLASK_DEBUG: bool = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    # CORS Configuration
    CORS_ALLOWED_ORIGINS: List[str] = os.environ.get(
        "CORS_ALLOWED_ORIGINS", 
        "http://localhost:3000"
    ).split(",")
    CORS_ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOWED_HEADERS: List[str] = ["Content-Type", "Authorization"]
    CORS_SUPPORTS_CREDENTIALS: bool = os.environ.get("CORS_SUPPORTS_CREDENTIALS", "true").lower() == "true"
    
    # Email Configuration (for Communication Service)
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "1025"))
    SMTP_USERNAME: str = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.environ.get("SMTP_USE_TLS", "false").lower() == "true"
    EMAIL_SENDER: str = os.environ.get("EMAIL_SENDER", "noreply@curavani.de")
    EMAIL_SENDER_NAME: str = os.environ.get("EMAIL_SENDER_NAME", "Curavani Therapievermittlung")
    EMAIL_ADD_LEGAL_FOOTER: bool = os.environ.get("EMAIL_ADD_LEGAL_FOOTER", "true").lower() == "true"
    
    # Company Configuration
    COMPANY_NAME: str = "Curavani Therapievermittlung GmbH"
    COMPANY_DOMAIN: str = "curavani.de"
    
    # System Notifications
    SYSTEM_NOTIFICATION_EMAIL: str = os.environ.get("SYSTEM_NOTIFICATION_EMAIL", "info@curavani.com")
    
    # Geocoding Configuration
    OSM_API_URL: str = os.environ.get("OSM_API_URL", "https://nominatim.openstreetmap.org")
    OSM_USER_AGENT: str = os.environ.get("OSM_USER_AGENT", "TherapyPlatform/1.0")
    OSM_TIMEOUT: int = int(os.environ.get("OSM_TIMEOUT", "10"))
    OSM_MAX_RETRIES: int = int(os.environ.get("OSM_MAX_RETRIES", "3"))
    OSM_RATE_LIMIT: float = float(os.environ.get("OSM_RATE_LIMIT", "1.0"))
    OSRM_API_URL: str = os.environ.get("OSRM_API_URL", "https://router.project-osrm.org")
    OSRM_PROFILE_CAR: str = os.environ.get("OSRM_PROFILE_CAR", "car")
    OSRM_PROFILE_TRANSIT: str = os.environ.get("OSRM_PROFILE_TRANSIT", "foot")
    CACHE_TTL_SECONDS: int = int(os.environ.get("CACHE_TTL_SECONDS", "2592000"))  # 30 days
    CACHE_MAX_SIZE: int = int(os.environ.get("CACHE_MAX_SIZE", "1000"))
    
    # Security Configuration
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    
    # Feature Flags
    ENABLE_SCRAPING: bool = os.environ.get("ENABLE_SCRAPING", "true").lower() == "true"
    ENABLE_EMAIL_SENDING: bool = os.environ.get("ENABLE_EMAIL_SENDING", "true").lower() == "true"
    ENABLE_PHONE_SCHEDULING: bool = os.environ.get("ENABLE_PHONE_SCHEDULING", "true").lower() == "true"
    
    # Scraping Service Configuration
    SCRAPING_BUCKET_NAME: str = os.environ.get("SCRAPING_BUCKET_NAME", "therapy-scraping-data")
    SCRAPING_BUCKET_REGION: str = os.environ.get("SCRAPING_BUCKET_REGION", "eu-central-1")
    SCRAPING_SERVICE_ACCOUNT_PATH: str = os.environ.get("SCRAPING_SERVICE_ACCOUNT_PATH", "")
    
    # Monitoring and Logging
    SENTRY_DSN: str = os.environ.get("SENTRY_DSN", "")
    ENABLE_PERFORMANCE_MONITORING: bool = os.environ.get("ENABLE_PERFORMANCE_MONITORING", "false").lower() == "true"
    
    # Rate Limiting
    API_RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("API_RATE_LIMIT_PER_MINUTE", "60"))
    API_RATE_LIMIT_PER_HOUR: int = int(os.environ.get("API_RATE_LIMIT_PER_HOUR", "1000"))
    
    # Session Configuration
    SESSION_LIFETIME_MINUTES: int = int(os.environ.get("SESSION_LIFETIME_MINUTES", "1440"))
    SESSION_COOKIE_SECURE: bool = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = os.environ.get("SESSION_COOKIE_HTTPONLY", "true").lower() == "true"
    
    # Development Tools
    ENABLE_DEBUG_TOOLBAR: bool = os.environ.get("ENABLE_DEBUG_TOOLBAR", "true").lower() == "true"
    ENABLE_PROFILING: bool = os.environ.get("ENABLE_PROFILING", "false").lower() == "true"
    SQL_ECHO: bool = os.environ.get("SQL_ECHO", "false").lower() == "true"
    
    # Frontend Configuration (for reference by backend services if needed)
    REACT_APP_USE_MOCK_DATA: bool = os.environ.get("REACT_APP_USE_MOCK_DATA", "false").lower() == "true"
    REACT_APP_PATIENT_API: str = os.environ.get("REACT_APP_PATIENT_API", "http://localhost:8001/api")
    REACT_APP_THERAPIST_API: str = os.environ.get("REACT_APP_THERAPIST_API", "http://localhost:8002/api")
    REACT_APP_MATCHING_API: str = os.environ.get("REACT_APP_MATCHING_API", "http://localhost:8003/api")
    REACT_APP_COMMUNICATION_API: str = os.environ.get("REACT_APP_COMMUNICATION_API", "http://localhost:8004/api")
    REACT_APP_GEOCODING_API: str = os.environ.get("REACT_APP_GEOCODING_API", "http://localhost:8005/api")
    
    # Anfrage (Inquiry) Configuration - PHASE 4 ADDITIONS
    MAX_ANFRAGE_SIZE: int = int(os.environ.get("MAX_ANFRAGE_SIZE", "6"))
    MIN_ANFRAGE_SIZE: int = int(os.environ.get("MIN_ANFRAGE_SIZE", "1"))
    PLZ_MATCH_DIGITS: int = int(os.environ.get("PLZ_MATCH_DIGITS", "2"))
    DEFAULT_MAX_DISTANCE_KM: int = int(os.environ.get("DEFAULT_MAX_DISTANCE_KM", "25"))
    
    @classmethod
    def get_database_uri(cls, use_pgbouncer: bool = True) -> str:
        """Get the database connection URI.
        
        Args:
            use_pgbouncer: Whether to connect through PgBouncer (default: True)
            
        Returns:
            PostgreSQL connection string
        """
        if use_pgbouncer:
            return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.PGBOUNCER_HOST}:{cls.PGBOUNCER_PORT}/{cls.DB_NAME}"
        else:
            return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def get_service_url(cls, service: str, internal: bool = True) -> str:
        """Get the URL for a specific service.
        
        Args:
            service: Service name (patient, therapist, matching, communication, geocoding)
            internal: Whether to return internal (Docker) or external URL
            
        Returns:
            Service URL
        """
        service_map = {
            "patient": ("patient_service", cls.PATIENT_SERVICE_PORT),
            "therapist": ("therapist_service", cls.THERAPIST_SERVICE_PORT),
            "matching": ("matching_service", cls.MATCHING_SERVICE_PORT),
            "communication": ("communication_service", cls.COMMUNICATION_SERVICE_PORT),
            "geocoding": ("geocoding_service", cls.GEOCODING_SERVICE_PORT),
        }
        
        if service not in service_map:
            raise ValueError(f"Unknown service: {service}")
        
        hostname, port = service_map[service]
        
        if internal:
            return f"http://{hostname}:{port}"
        else:
            return f"http://localhost:{port}"
    
    @classmethod
    def get_smtp_settings(cls) -> dict:
        """Get SMTP settings as a dictionary.
        
        Returns:
            Dictionary with SMTP configuration
        """
        return {
            "host": cls.SMTP_HOST,
            "port": cls.SMTP_PORT,
            "username": cls.SMTP_USERNAME,
            "password": cls.SMTP_PASSWORD,
            "use_tls": cls.SMTP_USE_TLS,
            "sender": cls.EMAIL_SENDER,
            "sender_name": cls.EMAIL_SENDER_NAME
        }
    
    @classmethod
    def get_cors_settings(cls) -> dict:
        """Get CORS settings as a dictionary.
        
        Returns:
            Dictionary with CORS configuration
        """
        return {
            "origins": cls.CORS_ALLOWED_ORIGINS,
            "methods": cls.CORS_ALLOWED_METHODS,
            "allow_headers": cls.CORS_ALLOWED_HEADERS,
            "supports_credentials": cls.CORS_SUPPORTS_CREDENTIALS
        }
    
    @classmethod
    def get_anfrage_config(cls) -> Dict[str, int]:
        """Get Anfrage (Inquiry) configuration as a dictionary.
        
        Returns:
            Dictionary with Anfrage-related configuration
        """
        return {
            "max_size": cls.MAX_ANFRAGE_SIZE,
            "min_size": cls.MIN_ANFRAGE_SIZE,
            "plz_match_digits": cls.PLZ_MATCH_DIGITS,
            "default_max_distance_km": cls.DEFAULT_MAX_DISTANCE_KM
        }


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    FLASK_DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production-specific configuration."""
    FLASK_DEBUG = False
    LOG_LEVEL = "WARNING"
    
    # Disable all development tools in production
    ENABLE_DEBUG_TOOLBAR = False
    ENABLE_PROFILING = False
    SQL_ECHO = False
    
    # Require secure cookies in production
    SESSION_COOKIE_SECURE = True
    
    # In production, these should come from environment variables
    # with no defaults for security
    @classmethod
    def validate(cls):
        """Validate that all required production configs are set."""
        required = [
            "DB_USER", "DB_PASSWORD", "DB_NAME",
            "SMTP_USERNAME", "SMTP_PASSWORD",
            "SECRET_KEY", "JWT_SECRET_KEY"
        ]
        
        missing = [var for var in required if not os.environ.get(var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Validate that default secrets are not used in production
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed from default in production")
        
        if cls.JWT_SECRET_KEY == "dev-jwt-secret-change-in-production":
            raise ValueError("JWT_SECRET_KEY must be changed from default in production")


class TestConfig(Config):
    """Test-specific configuration."""
    DB_NAME = "therapy_platform_test"
    LOG_LEVEL = "ERROR"


# Select configuration based on FLASK_ENV
env = os.environ.get("FLASK_ENV", "development")

if env == "production":
    config = ProductionConfig()
    # Validate production configuration
    config.validate()
elif env == "testing":
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
    - Silences noisy Kafka loggers by setting them to WARNING or higher
    - Allows service-specific loggers to use their own levels
    
    Args:
        service_name: Name of the service for identification in logs
    """
    # Get the current configuration
    current_config = get_config()
    
    # Determine the root log level
    # In debug mode, use DEBUG for root logger; otherwise use configured level
    root_level = logging.DEBUG if current_config.FLASK_DEBUG else getattr(logging, current_config.LOG_LEVEL)
    
    # Set up basic logging configuration
    logging.basicConfig(
        level=root_level,
        format=f'%(asctime)s - {service_name} - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get the kafka log level (default to WARNING if not set)
    kafka_level = getattr(logging, current_config.KAFKA_LOG_LEVEL, logging.WARNING)
    
    # List of Kafka-related logger names to silence
    kafka_loggers = [
        'kafka',
        'kafka.client',
        'kafka.consumer',
        'kafka.consumer.fetcher',
        'kafka.consumer.group',
        'kafka.conn',
        'kafka.connection',
        'kafka.coordinator',
        'kafka.coordinator.consumer',
        'kafka.coordinator.base',
        'kafka.metrics',
        'kafka.protocol',
        'kafka.protocol.parser',
        'kafka.producer',
        'kafka.producer.kafka',
        'kafka.producer.record_accumulator',
        'kafka.producer.sender',
    ]
    
    # Set all Kafka loggers to WARNING level or higher
    for logger_name in kafka_loggers:
        kafka_logger = logging.getLogger(logger_name)
        kafka_logger.setLevel(kafka_level)
    
    # Also set the kafka-python logger specifically
    logging.getLogger('kafka.python').setLevel(kafka_level)
    
    # Log the configuration for debugging
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {service_name}")
    logger.info(f"Root log level: {logging.getLevelName(root_level)}")
    logger.info(f"Kafka log level: {logging.getLevelName(kafka_level)}")
    logger.debug("This is a debug message - you should see this in debug mode")