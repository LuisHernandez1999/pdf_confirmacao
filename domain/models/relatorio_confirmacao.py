from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import foreign, remote  # ← aqui é o lugar certo
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao

class RelatorioConfirmacao(Base):
    __tablename__ = "relatorio_confirmacao"

    id = Column(Integer, primary_key=True, index=True)
    confirmacao_tag = Column(                # ← continua SEM ForeignKey!
        String(14),
        nullable=False,
        index=True,
    )
    obs_antes = Column(Text, nullable=True)
    obs_depois = Column(Text, nullable=True)
    observacao = Column(Text, nullable=True)
    data_geracao = Column(DateTime(timezone=True), server_default=func.now())

    def gerar_obs_por_imagem(self):
        if not self.imagens:
            return
        # Ajuste a ordenação se tiver coluna de data/sequencia
        imagens_ordenadas = sorted(self.imagens, key=lambda x: x.id)  # ou x.data_criacao
        self.obs_antes = getattr(imagens_ordenadas[0], "observacao", None)
        self.obs_depois = getattr(imagens_ordenadas[-1], "observacao", None)


# ==================== RELACIONAMENTOS FORA DA CLASSE ====================
RelatorioConfirmacao.confirmacao = relationship(
    ConfirmacaoServico,
    primaryjoin=foreign(RelatorioConfirmacao.confirmacao_tag) == remote(ConfirmacaoServico.tag_doc),
    uselist=False,
    viewonly=True,
    lazy="joined",
)

RelatorioConfirmacao.imagens = relationship(
    ImagemConfirmacao,
    secondary=ConfirmacaoServico.__table__,
    primaryjoin=foreign(RelatorioConfirmacao.confirmacao_tag) == remote(ConfirmacaoServico.tag_doc),
    secondaryjoin=foreign(ImagemConfirmacao.confirmacao_id) == remote(ConfirmacaoServico.id),
    viewonly=True,
    lazy="joined",
    order_by=ImagemConfirmacao.id.asc(),  # ← mude se tiver data_criacao ou sequencia
)