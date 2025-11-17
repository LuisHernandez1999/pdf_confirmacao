

from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime

class ImagemOut(BaseModel):
    id: int
    url: str

class ConfirmacaoOut(BaseModel):
    id: int
    tag_doc: str
    nome_vistoriador: str
    data_servico: Optional[date]
    tipo_servico: str
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]

    class Config:
        from_attributes = True

class RelatorioResponse(BaseModel):
    id: int
    confirmacao_tag: str
    obs_antes: Optional[str]
    obs_depois: Optional[str]
    observacao: Optional[str]
    data_geracao: datetime
    confirmacao: ConfirmacaoOut
    imagens: List[ImagemOut]
    imagens_utilizadas: dict

    class Config:
        from_attributes = True