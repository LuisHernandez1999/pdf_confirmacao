import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Caminho raiz do projeto
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from core.config import settings
from core.database import Base
from domain.models.relatorio_confirmacao import RelatorioConfirmacao

# Configuração padrão do Alembic
config = context.config
fileConfig(config.config_file_name)

# Apenas as tabelas que queremos que o Alembic gerencie
target_metadata = Base.metadata

# Evita que Alembic tente criar tabelas já existentes
def include_object(object, name, type_, reflected, compare_to):
    # Só incluir o RelatorioConfirmacao
    if type_ == "table" and name != "relatorio_confirmacao":
        return False
    return True

def run_migrations_offline():
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
