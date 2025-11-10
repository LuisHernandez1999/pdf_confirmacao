from sqlalchemy import Column, Integer, String, JSON
from core.database import Base

class RelatorioConfirmacao(Base):
    __tablename__ = "relatorio_confirmacao"
    id = Column(Integer, primary_key=True, index=True)
    tag_doc = Column(String(14), index=True)  
    nome_vistoriador = Column(String(20), index=True)
    campos_antes = Column(JSON) 
    campos_depois = Column(JSON) 
