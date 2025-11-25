from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal
import logging

from core.database import get_db
from domain.service.service_gerar_relatorio import gerar_relatorio, gerar_svg_relatorio

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
    accept: Optional[str] = Header(default=None, alias="Accept"),
    format: Optional[Literal["json", "svg"]] = Query(None, alias="format"),
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

        # Gera o SVG (sempre string)
        svg_string: str = gerar_svg_relatorio(dados_relatorio)

        # Cliente quer SVG?
        if format == "svg" or (accept and "image/svg+xml" in accept.lower()):
            logger.info(f"Retornando SVG - {payload.confirmacao_tag}")
            return Response(
                content=svg_string,
                media_type="image/svg+xml",
                headers={
                    "Content-Disposition": f'attachment; filename="relatorio_{payload.confirmacao_tag}.svg"',
                    "Cache-Control": "no-cache",
                }
            )

        # Padrão: retorna JSON (com SVG embutido ou não — você escolhe)
        dados_relatorio["svg"] = svg_string  # inclui o SVG no JSON (muito útil pro frontend!)
        return JSONResponse(content=dados_relatorio)

    except Exception as e:
        logger.exception("Erro fatal ao gerar relatório")
        raise HTTPException(status_code=500, detail="Erro ao gerar o relatório")