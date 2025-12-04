
from typing import List, Optional
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session
from mapper.list_table_cf_mapper import listar_confirmacoes_para_tabela

def listar_confi_tabela(
    db: Session,
    tag_conf: Optional[str] = None,
    data_servico:Optional[date]=None,
    data_inicial: Optional[date] = None,
    data_final: Optional[date] = None,
    tipo_servico: Optional[str] = None,
    com_imagens: Optional[bool] = None,
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
        )
    except Exception:
        raise HTTPException(status_code=500, detail="erro ao carregar confirmacoes")