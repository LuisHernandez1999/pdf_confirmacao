from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import foreign, remote 
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao

class RelatorioConfirmacao(Base):
    __tablename__ = "relatorio_confirmacao"
    id = Column(Integer, primary_key=True, index=True)
    confirmacao_tag = Column(                
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
        imagens_ordenadas = sorted(self.imagens, key=lambda x: x.id) 
        self.obs_antes = getattr(imagens_ordenadas[0], "observacao", None)
        self.obs_depois = getattr(imagens_ordenadas[-1], "observacao", None)
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
    order_by=ImagemConfirmacao.id.asc(),  
)