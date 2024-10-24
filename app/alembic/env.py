from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from core.config import get_app_settings, get_settings_no_cache
from models.user import Base
from models.contact import Contact

# Получение настроек приложения
app_settings = get_app_settings()

# Формирование строки подключения к базе данных
pg_connection_string = (
    f"postgresql://{app_settings.pg_username}:{app_settings.pg_password}@"
    f"{app_settings.pg_host}:{app_settings.pg_port}/{app_settings.pg_database}"
)

# Alembic Config object
config = context.config

# Установка строки подключения в конфигурации Alembic
config.set_main_option("sqlalchemy.url", pg_connection_string)

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Установка метаданных
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
