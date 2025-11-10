from sqlalchemy import Table, MetaData
from sqlalchemy.orm import mapper, relationship
from core.database import engine
from domain.models.base import Base

metadata = MetaData()
imagem_confirmacao_table = Table(
    "imagem_confirmacao",
    metadata,
    autoload_with=engine,
)

class ImagemConfirmacao:
    pass

mapper(ImagemConfirmacao, imagem_confirmacao_table, properties={
    "confirmacao": relationship("ConfirmacaoServico", back_populates="imagens")
})
