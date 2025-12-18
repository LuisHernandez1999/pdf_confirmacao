from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import  Optional
from datetime import date
import logging
from src.core.database import get_db
from src.service.service_list_relatorio import (
    gerar_relatorios_completos,
    gerar_pdf_relatorio_completo
)
from src.service.service_table_conf import listar_confi_tabela,galeria_imgs_service
router = APIRouter(
    prefix="/relatorio",
    tags=["Relatório"]
)

logger = logging.getLogger("api.relatorio")


# ==============================================================
# 1) ENDPOINT QUE O FRONTEND USA PARA LISTAR CONFIRMAÇÕES
# ==============================================================

@router.get("/completo")
def listar_relatorio_completo(
    db: Session = Depends(get_db),
    data_inicial: Optional[date] = Query(None),
    data_final: Optional[date] = Query(None),
    tipo_servico: Optional[str] = Query(None)
):
    try:
        dados = gerar_relatorios_completos(
            db=db,
            data_inicial=data_inicial,
            data_final=data_final,
            tipo_servico=tipo_servico
        )

        return dados

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado no endpoint /relatorio/completo")
        raise HTTPException(status_code=500, detail="Erro interno")


# ==============================================================
# 2) HISTÓRICO (TABELA COM CURSOR)
# ==============================================================

@router.get("/historico")
def get_historico(
    db: Session = Depends(get_db),
    tag_conf: str | None = Query(None),
    data_inicial: date | None = Query(None),
    data_final: date | None = Query(None),
    tipo_servico: str | None = Query(None),
    com_imagens: bool | None = Query(None),
    cursor: Optional[int] = Query(None),
    limit: int = Query(10)
):
    dados, next_cursor = listar_confi_tabela(
        db=db,
        tag_conf=tag_conf,
        data_inicial=data_inicial,
        data_final=data_final,
        tipo_servico=tipo_servico,
        com_imagens=com_imagens,
        cursor=cursor,
        limit=limit,
    )

    return {
        "data": dados,
        "next_cursor": next_cursor,
        "limit": limit
    }


# ==============================================================
# 3) PDF (ACEITA FILTROS + EXCLUSÃO DE IMAGENS)
# ==============================================================

@router.post("/pdf")
async def relatorio_completo_pdf(
    db: Session = Depends(get_db),
    body: dict = None
):
    try:
        data_inicial = body.get("data_inicial")
        data_final = body.get("data_final")
        tipo_servico = body.get("tipo_servico")
        imagens_excluir = body.get("imagens_excluir", [])

        pdf_bytes = gerar_pdf_relatorio_completo(
            db=db,
            data_inicial=data_inicial,
            data_final=data_final,
            tipo_servico= tipo_servico,
            imagens_excluir=imagens_excluir
        )

        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=relatorio.pdf"
            }
        )

    except Exception as e:
        logger.exception("Erro ao gerar PDF")
        raise HTTPException(status_code=500, detail="Erro ao gerar PDF")


@router.get("/galeria")
async def galeria_imagens_conf(
    db: Session = Depends(get_db),
    data_inicial: Optional[date] = Query(None),
    data_final: Optional[date] = Query(None),
    tipo_servico: Optional[str] = Query(None),
    cursor: Optional[int] = Query(
        None,
        description="Último imagem_id recebido (cursor pagination)"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Quantidade de imagens por página"
    ),
):
    return gerar_relatorios_completos(
        db=db,
        cursor=cursor,
        limit=limit,
        tipo_servico=tipo_servico,
        data_inicial=data_inicial,
        data_final=data_final,
    )
