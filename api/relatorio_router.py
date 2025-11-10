from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from domain.service.service_gerar_relatorio import gerar_relatorio

router = APIRouter(prefix="/relatorio", tags=["Relatório"])

@router.post("/{confirmacao_id}")
def criar_relatorio(confirmacao_id: int, imagens_escolhidas: list[int], db: Session = Depends(get_db)):
    return gerar_relatorio(db, confirmacao_id, imagens_escolhidas)
