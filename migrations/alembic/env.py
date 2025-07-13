"""Alembic environment configuration - Manual migrations with environment detection."""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Try to load environment variables
try:
    from dotenv import load_dotenv
    
    # Determine environment from ENV variable (defaults to 'dev')
    env = os.environ.get('ENV', 'dev')
    
    # Load the appropriate .env file
    env_file_map = {
        'dev': '.env.dev',
        'test': '.env.test', 
        'prod': '.env.prod'
    }
    
    env_file = env_file_map.get(env, '.env.dev')
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), env_file)
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment variables from: {env_path}")
    else:
        print(f"Warning: Environment file not found at {env_path}")
        print(f"Using system environment variables.")
        
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Construct database URL directly from environment variables
# Always use localhost with external port for migrations from host machine
db_user = os.environ.get('DB_USER', 'your_db_user')
db_password = os.environ.get('DB_PASSWORD', 'your_secure_password')
db_name = os.environ.get('DB_NAME', 'therapy_platform')
db_external_port = os.environ.get('DB_EXTERNAL_PORT', '5432')

database_url = f"postgresql://{db_user}:{db_password}@localhost:{db_external_port}/{db_name}"

# Set the URL in the config
config.set_main_option('sqlalchemy.url', database_url)

# Log connection details (without exposing password)
print(f"Using database connection: postgresql://{db_user}:****@localhost:{db_external_port}/{db_name}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata to None for manual migrations only
# No auto-generation support
target_metadata = None

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