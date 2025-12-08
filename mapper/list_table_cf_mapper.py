import logging
from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from domain.models.confirmacao_servico import ConfirmacaoServico

logger = logging.getLogger(__name__)


def listar_confirmacoes_para_tabela(
    db: Session,
    tag_conf: Optional[str] = None,
    data_inicial: Optional[date] = None,
    data_servico: Optional[date] = None,
    data_final: Optional[date] = None,
    tipo_servico: Optional[str] = None,
    com_imagens: Optional[bool] = None,
    cursor: Optional[int] = None,          
    limit: int = 50                        
) -> Tuple[List[dict], Optional[int]]:
    try:
        logger.info("Listando confirmações")

        query = db.query(ConfirmacaoServico).options(
            joinedload(ConfirmacaoServico.imagens)
        )

        # -------------------------------
        # Filtros existentes
        # -------------------------------
        if data_servico:
            query = query.filter(ConfirmacaoServico.data_servico == data_servico)

        if tag_conf:
            query = query.filter(ConfirmacaoServico.tag_doc.ilike(f"%{tag_conf}%"))

        if data_inicial:
            query = query.filter(ConfirmacaoServico.data_servico >= data_inicial)

        if data_final:
            query = query.filter(ConfirmacaoServico.data_servico <= data_final)

        if tipo_servico:
            query = query.filter(ConfirmacaoServico.tipo_servico == tipo_servico)

        if com_imagens is not None:
            if com_imagens:
                query = query.filter(ConfirmacaoServico.imagens.any())
            else:
                query = query.filter(~ConfirmacaoServico.imagens.any())

        # -------------------------------
        # Cursor (id < cursor para paginação)
        # -------------------------------
        if cursor:
            query = query.filter(ConfirmacaoServico.id < cursor)

        query = query.order_by(
            ConfirmacaoServico.id.desc()
        ).limit(limit + 1)          # 👈 pega 1 extra para saber se existe próxima página

        registros = query.all()

        resultado = []
        next_cursor = None

        # ------------------------------------------
        # Verifica se existe próxima página
        # ------------------------------------------
        if len(registros) > limit:
            next_cursor = registros[-2].id  # id do penúltimo item
            registros = registros[:limit]   # remove extra

        # ------------------------------------------
        # Monta resultado
        # ------------------------------------------
        for c in registros:
            lat = lng = None
            if c.imagens:
                img = c.imagens[0]
                lat = float(img.latitude) if img.latitude else None
                lng = float(img.longitude) if img.longitude else None

            resultado.append({
                "id": c.id,
                "tag_doc": c.tag_doc,
                "vistoriador": c.nome_vistoriador or "Não informado",
                "data_servico": c.data_servico.strftime("%Y-%m-%d"),
                "tipo_servico": c.tipo_servico or "Não especificado",
                "imagens": len(c.imagens),
                "latitude": lat,
                "longitude": lng,
            })

        logger.info(f"Retornadas {len(resultado)} confirmações")

        # Retorna lista + cursor da próxima página
        return resultado, next_cursor

    except Exception as e:
        logger.error(f"Erro no mapper: {e}", exc_info=True)
        raise
