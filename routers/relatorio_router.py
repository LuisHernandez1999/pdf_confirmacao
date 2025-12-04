# routers/relatorio_router.py
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging
from service.service_table_conf import listar_confi_tabela

from core.database import get_db
from service.service_list_relatorio import (  
    gerar_pdf_relatorio_completo,
)

router = APIRouter( 
    prefix="/relatorio",
    tags=["Relatório"]
)

logger = logging.getLogger("api.relatorio")
@router.get("/historico")
def get_historico(
    db: Session = Depends(get_db),
    tag_conf: str | None = Query(None),
    data_inicial: date | None = Query(None),
    data_final: date | None = Query(None),
    tipo_servico: str | None = Query(None),
    com_imagens: bool | None = Query(None),
):
    dados = listar_confi_tabela(
        db=db,
        tag_conf=tag_conf,
        data_inicial=data_inicial,
        data_final=data_final,
        tipo_servico=tipo_servico,
        com_imagens=com_imagens,
    )
    return {"data": dados}


@router.get("/completo/download-pdf")
async def relatorio_completo_pdf(
    db: Session = Depends(get_db),
    data_inicial: Optional[date] = Query(None, description="Data inicial do filtro (YYYY-MM-DD)"),
    data_final: Optional[date] = Query(None, description="Data final do filtro (YYYY-MM-DD)"),
    excluir_imagens: Optional[str] = Query(
        None,
        description="IDs das imagens que você quer REMOVER do PDF, separados por vírgula. Ex: 42,57,103",
        example="15,28,94"
    ),
):
    """
    Gera e baixa o relatório completo em PDF.
    Agora você pode excluir imagens específicas passando os IDs delas!
    """
    imagens_excluir_ids: List[int] | None = None

    if excluir_imagens:
        try:
            # Remove espaços e converte para int
            imagens_excluir_ids = [int(x.strip()) for x in excluir_imagens.split(",") if x.strip()]
            if not imagens_excluir_ids:
                raise ValueError()
            logger.info(f"Usuário solicitou exclusão de {len(imagens_excluir_ids)} imagem(ns): {imagens_excluir_ids}")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Parâmetro 'excluir_imagens' inválido. Use IDs separados por vírgula (ex: 10,25,37)"
            )

    try:
        pdf_bytes = gerar_pdf_relatorio_completo(
            db=db,
            data_inicial=data_inicial,
            data_final=data_final,
            imagens_excluir=imagens_excluir_ids,   # passa a lista pro service
        )

        filename = "relatorio_completo.pdf"
        if data_inicial or data_final:
            periodo = []
            if data_inicial:
                periodo.append(data_inicial.strftime("%Y%m%d"))
            if data_final:
                periodo.append(data_final.strftime("%Y%m%d"))
            filename = f"relatorio_completo_{'-'.join(periodo)}.pdf"

        logger.info(f"PDF gerado com sucesso - {len(pdf_bytes)} bytes - Nome: {filename}")

        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erro inesperado ao gerar PDF do relatório completo")
        raise HTTPException(status_code=500, detail="Erro interno ao gerar o PDF")
