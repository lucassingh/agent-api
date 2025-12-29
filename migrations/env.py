import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# this is the Alembic Config object
config = context.config

# ✅ CORRECCIÓN: Obtener DATABASE_URL de múltiples fuentes
def get_database_url():
    """
    Obtiene la URL de la base de datos en este orden:
    1. Variable de entorno DATABASE_URL (Render, producción)
    2. Configuración de settings (desarrollo con .env)
    3. alembic.ini (último recurso)
    """
    # 1. Variable de entorno (Render usa esta)
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        # ✅ IMPORTANTE: Render usa postgres:// pero SQLAlchemy necesita postgresql://
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql://", 1)
        return env_url
    
    # 2. Intenta importar settings (para desarrollo local)
    try:
        from app.core.config import settings
        if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL:
            return settings.DATABASE_URL
    except ImportError:
        pass
    
    # 3. Último recurso: alembic.ini
    return config.get_main_option("sqlalchemy.url")

# Configurar la URL
database_url = get_database_url()
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importar modelos DESPUÉS de configurar la URL
from app.core.database import Base
from app.models.user import User
from app.models.incident import Incident

# add your model's MetaData object here
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
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