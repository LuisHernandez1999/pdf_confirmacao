from datetime import date
from sqlalchemy.orm import Session
from src.domain.models.imagem_confirmacao import ConfirmacaoServico
from src.domain.models.imagem_confirmacao import ImagemConfirmacao
import logging


logger = logging.getLogger(__name__)

##### endpoint pra possivel galeria de imagens 
def imagens_galeria_mapper(
    db: Session,
    cursor: int,                    
    tipo_servico: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
    limit: int = 50,
):
    query = (
        db.query(
            ImagemConfirmacao.id.label("imagem_id"),
            ConfirmacaoServico.data_servico,
            ConfirmacaoServico.tipo_servico,
            ConfirmacaoServico.vistoriador,
        )
        .join(
            ConfirmacaoServico,
            ConfirmacaoServico.id == ImagemConfirmacao.confirmacao_id
        )
        .filter(ImagemConfirmacao.imagem_id.isnot(None))
    )

    if data_inicial:
        query = query.filter(ConfirmacaoServico.data_servico >= data_inicial)

    if data_final:
        query = query.filter(ConfirmacaoServico.data_servico <= data_final)

    if tipo_servico:
        query = query.filter(ConfirmacaoServico.tipo_servico == tipo_servico)
    

    
    query = query.filter(ImagemConfirmacao.id > cursor)
    query = query.order_by(ImagemConfirmacao.id.asc())
    dados = query
    resultados = query.limit(limit).all()

    lista_imagens = []
    next_cursor = cursor

    for c in resultados:
        lista_imagens.append({
            "imagem_id": c.imagem_id,
            "data_servico": c.data_servico,
            "tipo_servico": c.tipo_servico,
            "responsavel": c.vistoriador,
        })
        next_cursor = c.imagem_id

    return {
        "data": dados,                  
        "lsta_imgs": lista_imagens,   # payload
        "next_cursor": next_cursor,       
        "has_more": len(lista_imagens) == limit

    }
