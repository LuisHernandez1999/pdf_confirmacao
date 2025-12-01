# routers/relatorio_router.py
from fastapi import APIRouter, HTTPException, Depends, Body,Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session
from typing import List
from typing import Optional, Literal
import logging
from pydantic import BaseModel
from service.service_create_relatorio import gerar_relatorios_completos
from core.database import get_db
from service.service_list_relatorio import (
    gerar_relatorios_completos,
    gerar_pdf_relatorio_completo
)

router = APIRouter(
    prefix="/relatorio",
    tags=["Relatório"]
)

logger = logging.getLogger("api.relatorio")



class RelatorioRequest(BaseModel):
    imagens_antes_ids: List[int]
    imagens_depois_ids: List[int]



@router.get("/completo/download")
def relatorio_completo_download(db: Session = Depends(get_db)):
    """
    Baixa o relatório completo como arquivo HTML
    """
    try:
        resultado = gerar_relatorios_completos(db=db)
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



@router.get("/criar_relatorio")
def criar_relatorio(db: Session = Depends(get_db)):
    try:
        resultado = gerar_relatorios_completos(db=db)

        logger.info("Relatórios completos gerados com sucesso.")

        return JSONResponse(content=resultado)

    except Exception as e:
        logger.exception("Erro ao gerar relatórios")
        raise HTTPException(status_code=500, detail=str(e))