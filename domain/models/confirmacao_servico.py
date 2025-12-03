from sqlalchemy import Table, MetaData
from core.database import Base, engine

metadata = MetaData()
mapper_registry = Base.registry  

confirmacao_servico_table = Table(
    "confirmacao_servico",
    metadata,
    autoload_with=engine,
)

class ConfirmacaoServico:
    pass

mapper_registry.map_imperatively(ConfirmacaoServico, confirmacao_servico_table)
