# service/relatorio_service.py
import logging
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from src.domain.models.confirmacao_servico import ConfirmacaoServico
from src.utils.relatorio_pdf_utils import (
    setup_logger,
    expandir_confirmacoes_em_cards_imagem,
    aplicar_filtros_query,
    criar_pdf_visual
)
from src.mapper.relatorio_mapper import (
    mapear_confirmacoes_validas,
    calcular_total_imagens,
    gerar_observacao_relatorio,
    mapear_dados_relatorio,
    criar_relatorio_confirmacao,
    filtrar_imagens_excluidas
)

logger = logging.getLogger("relatorio_service")
setup_logger()


# ============================================================
# RETORNO JSON → traz imagens recentes + IDs para o frontend
# ============================================================


from src.domain.models.confirmacao_servico import ConfirmacaoServico
from src.utils.relatorio_pdf_utils import (
    setup_logger,
    expandir_confirmacoes_em_cards_imagem,
    aplicar_filtros_query,
    criar_pdf_visual
)
from src.mapper.relatorio_mapper import (
    mapear_confirmacoes_validas,
    calcular_total_imagens,
    gerar_observacao_relatorio,
    mapear_dados_relatorio,
    criar_relatorio_confirmacao,
    filtrar_imagens_excluidas
)

logger = logging.getLogger("relatorio_service")
setup_logger()


# ============================================================
# RETORNO JSON → traz imagens recentes + IDs para o frontend
# ============================================================

def gerar_relatorios_completos(
    db: Session,
    data_inicial: date | None = None,
    data_final: date | None = None,
    tipo_servico: str | None = None
) -> dict:

    logger.info("📄 Iniciando geração de relatórios completos")
    logger.info(f"➡️ Filtros recebidos: data_inicial={data_inicial}, data_final={data_final}, tipo_servico={tipo_servico}")

    try:
        # =====================================================
        # 🔒 1) VALIDAR ENTRADAS ANTES DE USAR NO BANCO
        # =====================================================

        # ---- VALIDAÇÃO DE DATAS ----
        if data_inicial and data_final:
            if data_inicial > data_final:
                logger.warning("⚠️ Datas invertidas! Ajustando automaticamente: data_inicial > data_final")
                data_inicial, data_final = data_final, data_inicial  # troca automática

        # ---- VALIDAÇÃO DE TIPO DE SERVIÇO ----
        if tipo_servico:
            tipo_servico = tipo_servico.strip()
            if tipo_servico.lower() in ["todos", "todas", "0", ""]:
                logger.info("ℹ️ tipo_servico='Todos' → ignorando filtro de tipo")
                tipo_servico = None


        # =====================================================
        # 🔍 2) MONTAR QUERY BASE
        # =====================================================
        query = db.query(ConfirmacaoServico).options(
            joinedload(ConfirmacaoServico.imagens)
        )

        filtros_aplicados = any([data_inicial, data_final, tipo_servico])

        if not filtros_aplicados:
            logger.info("⚠️ Nenhum filtro aplicado → pegando 50 mais recentes")
            query = query.order_by(ConfirmacaoServico.data_servico.desc()).limit(50)
        else:
            logger.info("🧮 Aplicando filtros seguros...")
            query = aplicar_filtros_query(query, data_inicial, data_final, tipo_servico)

        # =====================================================
        # 🔎 3) EXECUTAR QUERY COM TRY SEPARADO
        # =====================================================
        try:
            todas = query.all()
        except Exception as e:
            logger.error(f"💥 Erro ao executar consulta SQL (possível filtro inválido): {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="Parâmetros de filtro inválidos")

        logger.info(f"🔎 Total de confirmações encontradas: {len(todas)}")

        if not todas:
            logger.warning("❌ Nenhuma confirmação encontrada")
            raise HTTPException(status_code=404, detail="Nenhuma confirmação encontrada")


        # =====================================================
        # 📦 4) MONTAR DADOS PARA PDF
        # =====================================================
        relatorio_pdf = []

        for item in todas:
            imagens = [{"imagem_id": img.id} for img in (item.imagens or [])]

            logger.debug(f"📌 Confirmação ID {item.id} — {len(imagens)} imagens")

            relatorio_pdf.append({
                "id": item.id,
                "tag_doc": item.tag_doc,
                "tipo_servico": item.tipo_servico,
                "data_servico": item.data_servico,
                "imagens": imagens
            })

        logger.info("✅ Relatório completo montado com sucesso")

        return {
            "data_inicial": data_inicial,
            "data_final": data_final,
            "tipo_servico": tipo_servico,
            "total_registros": len(relatorio_pdf),
            "confirmacoes": relatorio_pdf
        }

    except HTTPException:
        # já tratado
        raise
    except Exception as e:
        logger.error(f"💥 Erro inesperado ao gerar relatório: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ==================================================================================
# PDF → EXCLUI SOMENTE AS IMAGENS ESCOLHIDAS PELO USUÁRIO
# ==================================================================================
def gerar_pdf_relatorio_completo(
    db: Session,
    data_inicial: date | None = None,
    data_final: date | None = None,
    tipo_servico: str | None = None,
    imagens_excluir: list[int] | None = None,
) -> bytes:

    try:
        logger.info("🧾 Iniciando geração de PDF do relatório completo")
        logger.info(f"➡️ Filtros recebidos: data_inicial={data_inicial}, data_final={data_final}, tipo_servico={tipo_servico}")
        logger.info(f"➡️ IDs de imagens a excluir: {imagens_excluir}")

        query = db.query(ConfirmacaoServico).options(
            joinedload(ConfirmacaoServico.imagens)
        )

        filtros_aplicados = data_inicial or data_final or tipo_servico

        if not filtros_aplicados:
            logger.info("⚠️ Nenhum filtro aplicado — Pegando os 50 registros mais recentes")
            query = query.order_by(ConfirmacaoServico.data_servico.desc()).limit(50)
        else:
            logger.info("🧮 Aplicando filtros na query…")
            query = aplicar_filtros_query(query, data_inicial, data_final, tipo_servico)

        confirmacoes = query.all()
        logger.info(f"🔎 Total de confirmações encontradas: {len(confirmacoes)}")

        if not confirmacoes:
            logger.warning("❌ Nenhuma confirmação encontrada")
            raise HTTPException(status_code=404, detail="Nenhuma confirmação encontrada")

        # Mapeia confirmações
        confirmacoes_validas = mapear_confirmacoes_validas(confirmacoes)
        logger.info(f"📦 Total de confirmações válidas após mapeamento: {len(confirmacoes_validas)}")

        # Calcula total de imagens ANTES da exclusão
        total_imagens_antes = calcular_total_imagens(confirmacoes_validas)
        logger.info(f"🖼️ Total de imagens ANTES da exclusão: {total_imagens_antes}")

        # Coleta todos os IDs de imagens existentes para verificação
        all_image_ids = {img["id"] for c in confirmacoes_validas for img in c.get("imagens", [])}

        # ====================================================
        # EXCLUI AS IMAGENS SELECIONADAS
        # ====================================================
        total_excluidas = 0

        if imagens_excluir:
            imagens_excluir_set = set(imagens_excluir)
            not_found = imagens_excluir_set - all_image_ids
            if not_found:
                logger.warning(f"⚠️ IDs de imagens solicitados para exclusão mas não encontrados no conjunto atual: {sorted(list(not_found))}")

            logger.info(f"🗑️ Aplicando exclusão de imagens: {imagens_excluir_set}")

            for c in confirmacoes_validas:
                imagens_antes = len(c.get("imagens", []))

                c["imagens"] = [
                    img for img in c.get("imagens", [])
                    if img["id"] not in imagens_excluir_set
                ]

                excluidas = imagens_antes - len(c["imagens"])
                total_excluidas += excluidas

                if excluidas > 0:
                    logger.debug(f"❌ Confirmação ID {c['id']} — {excluidas} imagens removidas")

        logger.info(f"🧹 Total de imagens removidas: {total_excluidas}")

        # Remove confirmações que ficaram sem imagens
        confirmacoes_validas = [c for c in confirmacoes_validas if c.get("imagens")]
        logger.info(f"📦 Total de confirmações após remoção de vazias: {len(confirmacoes_validas)}")

        # Conta imagens finais (validação cruzada)
        total_imagens_depois = calcular_total_imagens(confirmacoes_validas)
        logger.info(f"🖼️ Total de imagens DEPOIS da exclusão: {total_imagens_depois}")

        # Expande para cards e usa como total para PDF
        total_cards_no_pdf = len(
            expandir_confirmacoes_em_cards_imagem(confirmacoes_validas)
        )
        logger.info(f"🖼️ Total de imagens que irão para o PDF (após expansão): {total_cards_no_pdf}")

        # Gera PDF visual
        pdf_buffer = criar_pdf_visual(
            confirmacoes=confirmacoes_validas,
            data_inicial=data_inicial,
            data_final=data_final,
            total_confirmacoes=len(confirmacoes_validas),
            total_imagens=total_cards_no_pdf
        )

        logger.info("✅ PDF gerado com sucesso")

        return pdf_buffer.getvalue()

    except Exception as e:
        logger.error(f"💥 Erro ao gerar PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao gerar PDF")