import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Diretório base do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

# Configurações do projeto
from core.config import settings

# Importa o Base e os modelos que devem ser monitorados pelo Alembic
from domain.models.base import Base
from domain.models.relatorio_confirmacao import RelatorioConfirmacao  # Garantir que o Alembic veja essa tabela

# Config Alembic
config = context.config
fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata: Alembic vai olhar apenas essas tabelas
target_metadata = Base.metadata

# --------------------------
# Modo offline
# --------------------------
def run_migrations_offline():
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# --------------------------
# Executa o modo correto
# --------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
