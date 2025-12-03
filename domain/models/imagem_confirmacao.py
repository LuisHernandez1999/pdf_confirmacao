# domain/models/imagem_confirmacao.py

from sqlalchemy import Table, MetaData
from sqlalchemy.orm import relationship, foreign, remote  # ← adiciona foreign e remote aqui
from core.database import Base, engine

# IMPORTA A CLASSE DO PAI (não causa circular porque o outro arquivo não importa esse)
from domain.models.confirmacao_servico import ConfirmacaoServico

metadata = MetaData()
mapper_registry = Base.registry

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
            primaryjoin=foreign(imagem_confirmacao_table.c.confirmacao_id) == remote(ConfirmacaoServico.id),
            backref="imagens",   
            lazy="joined"
        )
    }
)