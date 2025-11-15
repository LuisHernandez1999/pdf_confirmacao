from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class RelatorioConfirmacao(Base):
    __tablename__ = "relatorio_confirmacao"

    id = Column(Integer, primary_key=True, index=True)
    confirmacao_tag = Column(
        String(14),
        ForeignKey("confirmacao_servico.tag_doc", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    obs_antes = Column(Text, nullable=True)
    obs_depois = Column(Text, nullable=True)
    observacao = Column(Text, nullable=True)
    data_geracao = Column(DateTime(timezone=True), server_default=func.now())

    # RELATIONSHIP com a confirmação usando string (evita ImportError)
    confirmacao = relationship(
        "ConfirmacaoServico",  # string, não import direto
        primaryjoin="foreign(RelatorioConfirmacao.confirmacao_tag) == remote(ConfirmacaoServico.tag_doc)",
        viewonly=True,
        lazy="joined"
    )

    # RELATIONSHIP com todas as imagens da confirmação usando string
    imagens = relationship(
        "ImagemConfirmacao",  # string, não import direto
        secondary="pesagem__imagemconfirmacao",
        primaryjoin="foreign(RelatorioConfirmacao.confirmacao_tag) == remote(ImagemConfirmacao.confirmacao_id)",
        viewonly=True,
        lazy="joined"
    )

    def gerar_obs_por_imagem(self):
        """
        Popula obs_antes e obs_depois a partir das imagens relacionadas.
        """
        if not self.imagens:
            return
        self.obs_antes = getattr(self.imagens[0], "observacao", None)
        self.obs_depois = getattr(self.imagens[-1], "observacao", None)
