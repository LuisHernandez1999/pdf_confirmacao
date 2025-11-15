# api/relatorio.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core.database import get_db
from domain.service.service_gerar_relatorio import gerar_relatorio

router = APIRouter(prefix="/relatorio", tags=["Relatório"])

class RelatorioCreateRequest(BaseModel):
    confirmacao_tag: str
    imagem_antes_id: int
    imagem_depois_id: int
    observacao: Optional[str] = None

@router.post("/")
def criar_relatorio(payload: RelatorioCreateRequest, db: Session = Depends(get_db)):
    try:
        relatorio = gerar_relatorio(
            db=db,
            confirmacao_tag=payload.confirmacao_tag,
            imagem_antes_id=payload.imagem_antes_id,
            imagem_depois_id=payload.imagem_depois_id,
            observacao=payload.observacao
        )
        return {"success": True, "relatorio_id": relatorio.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
