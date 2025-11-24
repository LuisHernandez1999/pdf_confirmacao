from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from core.database import get_db
from domain.service.service_gerar_relatorio import gerar_relatorio, gerar_pdf_relatorio

router = APIRouter(prefix="/relatorio", tags=["Relatório"])
logger = logging.getLogger("api.relatorio")

class RelatorioCreateRequest(BaseModel):
    confirmacao_tag: str
    imagem_antes_id: int
    imagem_depois_id: int
    obs_antes: Optional[str] = None
    obs_depois: Optional[str] = None
    observacao: Optional[str] = None


@router.post("/")
def criar_relatorio(
    payload: RelatorioCreateRequest,
    db: Session = Depends(get_db),
    accept: Optional[str] = Header(default=None, alias="Accept"),  # AQUI É O SEGREDO
    format: Optional[str] = Query(None, alias="format")
):
    try:
        dados_relatorio = gerar_relatorio(
            db=db,
            confirmacao_tag=payload.confirmacao_tag,
            imagem_antes_id=payload.imagem_antes_id,
            imagem_depois_id=payload.imagem_depois_id,
            obs_antes=payload.obs_antes,
            obs_depois=payload.obs_depois,
            observacao=payload.observacao
        )

        # Agora sim ele detecta o header Accept corretamente
        wants_pdf = (
            (accept and "application/pdf" in accept.lower()) or
            format == "pdf"
        )

        if wants_pdf:
            logger.info(f"GERANDO PDF - Relatório ID: {dados_relatorio['id']}")
            pdf_buffer = gerar_pdf_relatorio(dados_relatorio)
            pdf_buffer.seek(0)  # importante!

            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="relatorio_{payload.confirmacao_tag}.pdf"',
                    "Cache-Control": "no-cache"
                }
            )

        return JSONResponse(content=dados_relatorio)

    except Exception as e:
        logger.exception("Erro fatal ao gerar relatório")
        raise HTTPException(status_code=500, detail=str(e))