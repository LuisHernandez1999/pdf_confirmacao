# api/relatorio.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core.database import get_db
from domain.service.service_gerar_relatorio import gerar_relatorio
from domain.schemas.relatorio_schemas import RelatorioResponse 

router = APIRouter(prefix="/relatorio", tags=["Relatório"])

class RelatorioCreateRequest(BaseModel):
    confirmacao_tag: str
    imagem_antes_id: int
    imagem_depois_id: int
    obs_antes: Optional[str] = None
    obs_depois: Optional[str] = None
    observacao: Optional[str] = None

@router.post("/", response_model=RelatorioResponse) 
def criar_relatorio(payload: RelatorioCreateRequest, db: Session = Depends(get_db)):
    try:
        relatorio = gerar_relatorio(
            db=db,
            confirmacao_tag=payload.confirmacao_tag,
            imagem_antes_id=payload.imagem_antes_id,
            imagem_depois_id=payload.imagem_depois_id,
            obs_antes=payload.obs_antes,
            obs_depois=payload.obs_depois,
            observacao=payload.observacao
        )
        return relatorio  
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))