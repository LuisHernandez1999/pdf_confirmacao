
from typing import List, Optional
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.mapper.list_table_cf_mapper import listar_confirmacoes_para_tabela
from src.mapper.galeria_mapper import imagens_galeria_mapper

def listar_confi_tabela(
    db: Session,
    tag_conf: Optional[str] = None,
    data_servico:Optional[date]=None,
    data_inicial: Optional[date] = None,
    data_final: Optional[date] = None,
    tipo_servico: Optional[str] = None,
    com_imagens: Optional[bool] = None,
    cursor: Optional[int] = None,          
    limit: int = 10 
) -> List[dict]:
    try:
        return listar_confirmacoes_para_tabela(
            db=db,
            tag_conf=tag_conf,
            data_servico=data_servico,
            data_inicial=data_inicial,
            data_final=data_final,
            tipo_servico=tipo_servico,
            com_imagens=com_imagens,
            cursor=cursor,
            limit=limit
        )
    except Exception:
        raise HTTPException(status_code=500, detail="erro ao carregar confirmacoes")
    



def galeria_imgs_service(
    db:Session,
    cursor:int,
    limit:int[50],
    tipo_servico: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
    data_servico: date | None=None
)->List[dict]:
    try:
        return imagens_galeria_mapper(
            db= db,
            limit=limit,
            cursor=cursor,
            data_servico =data_servico,
            tipo_servico= tipo_servico,
            data_final=data_final,
            data_inicial=data_inicial,
            data_servico=data_servico,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="erro ao carregar imagens")