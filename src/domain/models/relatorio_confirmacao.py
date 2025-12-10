from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship, foreign, remote
from sqlalchemy.sql import func

from src.core.database import Base
from src.domain.models.confirmacao_servico import ConfirmacaoServico

class RelatorioConfirmacao(Base):
    __tablename__ = "relatorio_confirmacao"

    id = Column(Integer, primary_key=True, index=True)
    confirmacao_tag = Column(String(14), nullable=False, index=True)

    # listas de URLs escolhidas pelo usuário (JSON)
    imagem_antes = Column(JSON, nullable=True)
    imagem_depois = Column(JSON, nullable=True)

    # latitude/longitude das imagens escolhidas (JSON)
    latitude_antes = Column(JSON, nullable=True)
    longitude_antes = Column(JSON, nullable=True)
    latitude_depois = Column(JSON, nullable=True)
    longitude_depois = Column(JSON, nullable=True)

    data_geracao = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento com confirmação
    confirmacao = relationship(
        ConfirmacaoServico,
        primaryjoin=foreign(confirmacao_tag) == remote(ConfirmacaoServico.tag_doc),
        uselist=False,
        viewonly=True,
        lazy="joined"
    )
