from datetime import date
from sqlalchemy.orm import Session
from src.domain.models.imagem_confirmacao import ConfirmacaoServico, ImagemConfirmacao
import logging
logger = logging.getLogger(__name__)
def imagens_galeria_mapper(
    db: Session,
    cursor: int | None = None,
    tipo_servico: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
    limit: int = 50,
):
    query = (
        db.query(
            ImagemConfirmacao.id.label("imagem_id"),
            ImagemConfirmacao.confirmacao_id,
            ImagemConfirmacao.imagem,           
            ImagemConfirmacao.latitude,
            ImagemConfirmacao.longitude,
            ConfirmacaoServico.data_servico,
            ConfirmacaoServico.tipo_servico,
            ConfirmacaoServico.nome_vistoriador,
        )
        .join(
            ConfirmacaoServico,
            ConfirmacaoServico.id == ImagemConfirmacao.confirmacao_id
        )
        .filter(ImagemConfirmacao.imagem.isnot(None))
    )

    # 🔹 Filtros opcionais (aplicados ANTES do cursor)
    if tipo_servico:
        query = query.filter(ConfirmacaoServico.tipo_servico == tipo_servico)

    if data_inicial:
        query = query.filter(ConfirmacaoServico.data_servico >= data_inicial)

    if data_final:
        query = query.filter(ConfirmacaoServico.data_servico <= data_final)

    # 🔹 Cursor DESC (buscar mais antigas)
    if cursor:
        query = query.filter(ImagemConfirmacao.id < cursor)

    # 🔹 Ordenação correta para galeria
    query = query.order_by(ImagemConfirmacao.id.desc())

    # 🔹 Busca +1 para saber se existe próxima página
    resultados = query.limit(limit + 1).all()

    has_more = len(resultados) > limit
    resultados = resultados[:limit]

    lista_imagens = []
    next_cursor = None

    for item in resultados:
        lista_imagens.append({
            "imagem_id": item.imagem_id,
            "imagem": item.imagem,
            "confirmacao_id": item.confirmacao_id,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "data_servico": item.data_servico,
            "tipo_servico": item.tipo_servico,
            "responsavel": item.nome_vistoriador,
        })
        next_cursor = item.imagem_id  

    return {
        "data": lista_imagens,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "limit": limit,
    }
