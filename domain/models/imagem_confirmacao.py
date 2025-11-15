from sqlalchemy import Table, MetaData
from sqlalchemy.orm import registry, relationship
from core.database import engine
from domain.models.confirmacao_servico import ConfirmacaoServico

metadata = MetaData()
mapper_registry = registry()

imagem_confirmacao_table = Table(
    "pesagem__imagemconfirmacao",
    metadata,
    autoload_with=engine
)

class ImagemConfirmacao:
    pass

mapper_registry.map_imperatively(
    ImagemConfirmacao,
    imagem_confirmacao_table,
    properties={
        "confirmacao": relationship(
            ConfirmacaoServico,
            back_populates="imagens",
            lazy="joined"
        )
    }
)

# Relacionamento inverso
ConfirmacaoServico.imagens = relationship(
    ImagemConfirmacao,
    viewonly=True,
    lazy="joined",
    primaryjoin="ImagemConfirmacao.confirmacao_id==ConfirmacaoServico.id"
)
