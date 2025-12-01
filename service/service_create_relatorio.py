import logging
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao

logger = logging.getLogger("relatorio_service")


def gerar_relatorios_completos(db: Session) -> dict:
    """
    Retorna TODAS as confirmações existentes no banco,
    cada uma com TODAS as imagens vinculadas, sem filtros
    e sem parâmetros de query.
    """

    # 1 — Buscar todas as confirmações
    confirmacoes = db.query(ConfirmacaoServico).all()

    if not confirmacoes:
        return {"result": [], "msg": "Nenhuma confirmação cadastrada."}

    # 2 — Buscar todas as imagens existentes
    imagens = db.query(ImagemConfirmacao).all()

    # Agrupar imagens por confirmacao_id
    imagens_por_confirmacao = {}
    for img in imagens:
        imagens_por_confirmacao.setdefault(img.confirmacao_id, []).append(img)

    # 3 — Montar lista final
    resultado = []

    for conf in confirmacoes:
        imagens_conf = imagens_por_confirmacao.get(conf.id, [])

        resultado.append({
            "confirmacao_tag": conf.tag_doc,
            "nome_vistoriador": conf.nome_vistoriador,
            "data_servico": str(conf.data_servico),
            "tipo_servico": conf.tipo_servico,

            "imagens": [
                {
                    "imagem": img.imagem,
                    "latitude": float(img.latitude) if img.latitude else None,
                    "longitude": float(img.longitude) if img.longitude else None
                }
                for img in imagens_conf
            ]
        })

    logger.info("Relatórios completos gerados — sem filtro, sem parâmetros.")

    return jsonable_encoder({"result": resultado})
