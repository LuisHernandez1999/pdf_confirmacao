from sqlalchemy import Table, MetaData
from sqlalchemy.orm import registry
from core.database import engine

metadata = MetaData()

confirmacao_servico_table = Table(
    "confirmacao_servico",  # nome exato do Django
    metadata,
    autoload_with=engine,    # pega a tabela diretamente do banco
)

mapper_registry = registry()

class ConfirmacaoServico:
    pass

mapper_registry.map_imperatively(ConfirmacaoServico, confirmacao_servico_table)
