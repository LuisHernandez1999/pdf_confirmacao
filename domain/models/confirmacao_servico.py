from sqlalchemy import Table, MetaData
from sqlalchemy.orm import mapper, relationship
from core.database import engine
from domain.models.base import Base

metadata = MetaData()
confirmacao_servico_table = Table(
    "confirmacao_servico",
    metadata,
    autoload_with=engine,
)

class ConfirmacaoServico:
    pass

mapper(ConfirmacaoServico, confirmacao_servico_table, properties={
    "imagens": relationship("ImagemConfirmacao", back_populates="confirmacao")
})
