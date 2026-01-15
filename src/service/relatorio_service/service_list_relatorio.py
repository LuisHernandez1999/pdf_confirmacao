import logging
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict
from src.utils.relatorio_utils.relatorio_utils import normalizar_data
from src.domain.models.confirmacao_servico import ConfirmacaoServico
from src.mapper.relatorio_mappers.galeria_mapper import imagens_galeria_mapper
from src.utils.relatorio_utils.relatorio_pdf_utils import (
    setup_logger,
    expandir_confirmacoes_em_cards_imagem,
    aplicar_filtros_query,
    criar_pdf_visual
)
from src.mapper.relatorio_mappers.relatorio_mapper import (
    mapear_confirmacoes_validas,
)
# from src.utils.imagem_utils import otimizar_url_imagem

logger = logging.getLogger("relatorio_service")
setup_logger()


def gerar_relatorios_completos(
    db: Session,
    data_inicial: date | None = None,
    data_final: date | None = None,
    tipo_servico: str | None = None,
    cursor: int | None = None,
    limit: int = 50,
) -> dict:

    logger.info("📸 Gerando galeria JSON")

    if data_inicial and data_final and data_inicial > data_final:
        data_inicial, data_final = data_final, data_inicial

    if tipo_servico:
        tipo_servico = tipo_servico.strip()
        if tipo_servico.lower() in ("todos", "todas", "0", ""):
            tipo_servico = None

    resultado = imagens_galeria_mapper(
        db=db,
        cursor=cursor,
        tipo_servico=tipo_servico,
        data_inicial=data_inicial,
        data_final=data_final,
        limit=limit,
    )

    imagens = resultado["data"]

    # for img in imagens:
    #     img["imagem"] = otimizar_url_imagem(img["imagem"])

    if not imagens:
        raise HTTPException(status_code=404, detail="Nenhum registro encontrado")

    confirmacoes = defaultdict(lambda: {
        "tipo_servico": None,
        "data_servico": None,
        "imagens": []
    })

    for img in imagens:
        key = (img["tipo_servico"], img["data_servico"])
        bloco = confirmacoes[key]

        if bloco["tipo_servico"] is None:
            bloco["tipo_servico"] = img["tipo_servico"]
            bloco["data_servico"] = img["data_servico"]

        bloco["imagens"].append({
            "imagem_id": img["imagem_id"]
        })

    return {
        "data_inicial": data_inicial,
        "data_final": data_final,
        "tipo_servico": tipo_servico,
        "total_confirmacoes": len(confirmacoes),
        "confirmacoes": list(confirmacoes.values()),
        "next_cursor": resultado["next_cursor"],
        "has_more": resultado["has_more"],
        "limit": limit,
    }


def gerar_pdf_relatorio_completo(
    db: Session,
    data_inicial: date | None = None,
    data_final: date | None = None,
    tipo_servico: str | None = None,
    imagens_excluir: list[int] | None = None,
) -> bytes:

    data_inicial = normalizar_data(data_inicial)
    data_final = normalizar_data(data_final)

    logger.info("🧾 Gerando PDF do relatório")

    query = (
        db.query(ConfirmacaoServico)
        .options(joinedload(ConfirmacaoServico.imagens))
    )

    if not (data_inicial or data_final or tipo_servico):
        query = query.order_by(
            ConfirmacaoServico.data_servico.desc()
        ).limit(50)
    else:
        query = aplicar_filtros_query(
            query, data_inicial, data_final, tipo_servico
        )

    confirmacoes = query.all()
    if not confirmacoes:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma confirmação encontrada"
        )

    confirmacoes_validas = mapear_confirmacoes_validas(confirmacoes)

    excluir_set = set(imagens_excluir or [])
    total_excluidas = 0

    if excluir_set:
        for c in confirmacoes_validas:
            imgs = c["imagens"]
            qtd_antes = len(imgs)

            c["imagens"] = [
                img for img in imgs if img["id"] not in excluir_set
            ]

            total_excluidas += qtd_antes - len(c["imagens"])

        confirmacoes_validas = [
            c for c in confirmacoes_validas if c["imagens"]
        ]

    logger.info(f"🧹 Imagens removidas: {total_excluidas}")

    total_cards = len(
        expandir_confirmacoes_em_cards_imagem(confirmacoes_validas)
    )

    pdf_buffer = criar_pdf_visual(
        confirmacoes=confirmacoes_validas,
        data_inicial=data_inicial,
        data_final=data_final,
        total_confirmacoes=len(confirmacoes_validas),
        total_imagens=total_cards
    )

    logger.info("✅ PDF gerado com sucesso")
    return pdf_buffer.getvalue()
