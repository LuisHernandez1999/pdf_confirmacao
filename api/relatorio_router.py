# routers/relatorio_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Literal
import logging

from core.database import get_db
from domain.service.service_gerar_relatorio import (
    gerar_relatorio_completo,
    gerar_pdf_relatorio_completo
)

router = APIRouter(
    prefix="/relatorio",
    tags=["Relatório"]
)

logger = logging.getLogger("api.relatorio")


# ================================================
# 1. RELATÓRIO INDIVIDUAL (ANTIGO - mantido por compatibilidade)
# ================================================
# Você pode deixar ou remover depois, se não usar mais
# ================================================
# @router.post("/")
# ... (se quiser manter o antigo, deixe comentado ou apague)


# ================================================
# 2. RELATÓRIO COMPLETO COM TODAS AS CONFIRMAÇÕES + CARROSSEL
# ================================================
@router.get("/completo")
def relatorio_completo(db: Session = Depends(get_db)):
    """
    Gera o relatório completo com TODAS as confirmações do banco,
    retorna HTML diretamente para visualização no navegador.
    """
    try:
        resultado = gerar_relatorio_completo(db=db)
        html_content: str = resultado["html"]
        
        logger.info(f"Relatório completo gerado - {resultado['total_confirmacoes']} confirmações")
        
        # Retorna HTML diretamente
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Erro ao gerar relatório completo")
        raise HTTPException(status_code=500, detail="Erro interno ao gerar relatório completo")


@router.get("/completo/download")
def relatorio_completo_download(db: Session = Depends(get_db)):
    """
    Baixa o relatório completo como arquivo HTML
    """
    try:
        resultado = gerar_relatorio_completo(db=db)
        html_content: str = resultado["html"]
        
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": 'attachment; filename="relatorio_completo.html"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            }
        )
    except Exception as e:
        logger.exception("Erro ao baixar relatório")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/completo/download-pdf")
def relatorio_completo_pdf(db: Session = Depends(get_db)):
    """
    Gera e baixa o relatório completo como PDF usando svglib + reportlab
    """
    try:
        pdf_bytes = gerar_pdf_relatorio_completo(db=db)
        
        logger.info(f"PDF gerado com sucesso - {len(pdf_bytes)} bytes")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="relatorio_completo.pdf"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            }
        )
    except Exception as e:
        logger.exception("Erro ao gerar PDF do relatório")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")
