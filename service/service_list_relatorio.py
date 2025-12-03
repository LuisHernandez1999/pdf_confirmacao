# service/relatorio_service.py
import logging
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from domain.models.confirmacao_servico import ConfirmacaoServico
from utils.relatorio_pdf_utils import (
    setup_logger,
    expandir_confirmacoes_em_cards_imagem,
    aplicar_filtros_query,
    criar_pdf_visual
)
from mapper.relatorio_mapper import (
    mapear_confirmacoes_validas,
    calcular_total_imagens,
    gerar_observacao_relatorio,
    mapear_dados_relatorio,
    criar_relatorio_confirmacao,
    filtrar_imagens_excluidas
)

logger = logging.getLogger("relatorio_service")
setup_logger()


def gerar_relatorios_completos(
    db: Session,
    data_inicial: date | None = None,
    data_final: date | None = None
) -> dict[str, str]:
    try:
        logger.info("Iniciando geração de relatórios completos")
        query = db.query(ConfirmacaoServico).options(joinedload(ConfirmacaoServico.imagens))
        query = aplicar_filtros_query(query, data_inicial, data_final)
        todas = query.all()

        if not todas:
            raise HTTPException(status_code=404, detail="Nenhuma confirmação encontrada")

        confirmacoes_validas = mapear_confirmacoes_validas(todas)
        total_imagens = calcular_total_imagens(confirmacoes_validas)

        primeira_tag = confirmacoes_validas[0].tag_doc
        observacao = gerar_observacao_relatorio(
            len(confirmacoes_validas), total_imagens, data_inicial, data_final
        )

        relatorio = criar_relatorio_confirmacao(db, primeira_tag, observacao)

        logger.info(f"RELATÓRIO REGISTRADO → {len(confirmacoes_validas)} confirmações, {total_imagens} imagens")
        return mapear_dados_relatorio(relatorio, data_inicial, data_final)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


def gerar_pdf_relatorio_completo(
    db: Session,
    data_inicial: date | None = None,
    data_final: date | None = None,
    imagens_excluir: list[int] | None = None,
) -> bytes:
    try:
        logger.info("Iniciando geração de PDF do relatório completo")

        query = db.query(ConfirmacaoServico).options(joinedload(ConfirmacaoServico.imagens))
        query = aplicar_filtros_query(query, data_inicial, data_final)
        confirmacoes = query.all()

        if not confirmacoes:
            raise HTTPException(status_code=404, detail="Nenhuma confirmação encontrada")

        confirmacoes_validas = mapear_confirmacoes_validas(confirmacoes)

        # === FILTRA APENAS AS IMAGENS EXCLUÍDAS (não remove a confirmação inteira) ===
        if imagens_excluir:
            ids_excluir = set(imagens_excluir)
            total_antes = sum(len(c.imagens or []) for c in confirmacoes_validas)
            
            confirmacoes_validas = filtrar_imagens_excluidas(confirmacoes_validas, imagens_excluir)
            
            total_depois = sum(len(c.imagens or []) for c in confirmacoes_validas)
            logger.info(f"Imagens excluídas do PDF: {total_antes - total_depois} (restam {total_depois})")

        # === CONTAGEM CORRETA: 1 card por imagem + 1 card por confirmação sem imagem ===
        total_confirmacoes = len(confirmacoes_validas)
        total_cards_no_pdf = len(expandir_confirmacoes_em_cards_imagem(confirmacoes_validas))

        logger.info(f"PDF → {total_confirmacoes} confirmações | {total_cards_no_pdf} cards exibidos")

        pdf_buffer = criar_pdf_visual(
            confirmacoes=confirmacoes_validas,
            data_inicial=data_inicial,
            data_final=data_final,
            total_confirmacoes=total_confirmacoes,
            total_imagens=total_cards_no_pdf   # ← aqui é o número que aparece no cabeçalho
        )

        pdf_bytes = pdf_buffer.getvalue()
        logger.info(f"PDF gerado com sucesso - {len(pdf_bytes)} bytes")
        return pdf_bytes

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")