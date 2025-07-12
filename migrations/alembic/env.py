"""Alembic environment configuration."""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the project root directory to Python's path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the shared config system
from shared.config import get_config  # noqa: E402

# Import the Base class and models
from shared.utils.database import Base  # noqa: E402
# Need to import all models that will be part of migrations
from patient_service.models.patient import Patient  # noqa: F401, E402
from therapist_service.models.therapist import Therapist  # noqa: F401, E402
# PlacementRequest removed - using bundle system instead
from matching_service.models.platzsuche import Platzsuche  # noqa: F401, E402
from matching_service.models.therapeutenanfrage import Therapeutenanfrage  # noqa: F401, E402
from matching_service.models.therapeut_anfrage_patient import TherapeutAnfragePatient  # noqa: F401, E402
from communication_service.models.email import Email  # noqa: F401, E402
from communication_service.models.phone_call import PhoneCall  # noqa: F401, E402
from geocoding_service.models.geocache import GeoCache, DistanceCache  # noqa: F401, E402

# Try to load environment variables
try:
    from dotenv import load_dotenv
    # Load .env file from project root (two levels up from alembic/)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment variables from: {env_path}")
    else:
        print(f"Warning: .env file not found at {env_path}")
        print(f"Using system environment variables.")
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get the shared configuration and build database URL for external connections
shared_config = get_config()

# Use external_url=True to get localhost connection for migrations running from host
database_url = shared_config.get_database_uri(external_url=True)

# Set the URL in the config
config.set_main_option('sqlalchemy.url', database_url)

# Parse connection details for logging (without exposing password)
if '://' in database_url and '@' in database_url:
    # postgresql://user:password@host:port/database
    protocol_part, rest = database_url.split('://', 1)
    auth_part, host_part = rest.split('@', 1)
    user = auth_part.split(':', 1)[0]
    host_and_db = host_part
    print(f"Using database connection: {protocol_part}://{user}:****@{host_and_db}")
else:
    print(f"Using database connection: {database_url}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the MetaData object for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()