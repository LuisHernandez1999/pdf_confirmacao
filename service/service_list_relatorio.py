import logging
from io import BytesIO
from datetime import datetime, date
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, PageBreak

from domain.models.relatorio_confirmacao import RelatorioConfirmacao
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao

from templates.relatorio_templates import (
    criar_header_completo,
    criar_card_individual,
    adicionar_background_e_footer
)

logger = logging.getLogger("relatorio_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

def _expandir_confirmacoes_em_cards_imagem(confirmacoes: list[ConfirmacaoServico]) -> list[tuple[ConfirmacaoServico, ImagemConfirmacao]]:
    """Expande confirmações em lista de (confirmacao, imagem) para criar cards individuais"""
    cards_data = []
    for conf in confirmacoes:
        if conf.imagens and len(conf.imagens) > 0:
            for img in conf.imagens:
                cards_data.append((conf, img))
        else:
            cards_data.append((conf, None))
    return cards_data

def gerar_relatorios_completos(db: Session, data_inicial: date | None = None, data_final: date | None = None) -> dict[str, str]:
    """
    Gera relatório completo em PDF com filtros opcionais de data.
    Retorna informações sobre o relatório gerado.
    """
    try:
        logger.info("Iniciando geração de relatórios completos (PDF apenas)")
        
        query = db.query(ConfirmacaoServico).options(joinedload(ConfirmacaoServico.imagens))
        
        if data_inicial:
            logger.info(f"Aplicando filtro de data inicial: {data_inicial}")
            query = query.filter(ConfirmacaoServico.data_servico >= data_inicial)
        
        if data_final:
            logger.info(f"Aplicando filtro de data final: {data_final}")
            query = query.filter(ConfirmacaoServico.data_servico <= data_final)
        
        todas = query.all()

        if not todas:
            logger.warning("Nenhuma confirmação encontrada no banco")
            raise HTTPException(status_code=404, detail="Nenhuma confirmação encontrada")

        confirmacoes_validas = []
        for c in todas:
            if (c.tag_doc and 
                c.nome_vistoriador and 
                c.tipo_servico and 
                c.data_servico):
                confirmacoes_validas.append(c)
            else:
                logger.info(f"Confirmação ignorada (dados incompletos): tag_doc={c.tag_doc}")

        if not confirmacoes_validas:
            logger.warning("Nenhuma confirmação com dados completos")
            raise HTTPException(status_code=400, detail="Nenhuma confirmação com dados completos foi encontrada")

        total_imagens = sum(len(c.imagens) if c.imagens else 0 for c in confirmacoes_validas)
        
        primeira_tag = confirmacoes_validas[0].tag_doc
        logger.info(f"Processando {len(confirmacoes_validas)} confirmações com {total_imagens} imagens")

        observacao_parts = [f"RELATÓRIO COMPLETO - {len(confirmacoes_validas)} confirmações, {total_imagens} imagens"]
        if data_inicial or data_final:
            if data_inicial and data_final:
                observacao_parts.append(f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}")
            elif data_inicial:
                observacao_parts.append(f"A partir de: {data_inicial.strftime('%d/%m/%Y')}")
            else:
                observacao_parts.append(f"Até: {data_final.strftime('%d/%m/%Y')}")
        observacao_parts.append(f"{datetime.now():%d/%m/%Y %H:%M}")

        relatorio = RelatorioConfirmacao(
            confirmacao_tag=primeira_tag,
            observacao=" - ".join(observacao_parts)
        )
        db.add(relatorio)
        db.commit()
        db.refresh(relatorio)

        logger.info(f"RELATÓRIO REGISTRADO → {len(confirmacoes_validas)} confirmações, {total_imagens} imagens")

        return {
            "id": relatorio.id,
            "total_confirmacoes": len(confirmacoes_validas),
            "total_imagens": total_imagens,
            "data_geracao": relatorio.data_geracao.isoformat(),
            "data_inicial": data_inicial.isoformat() if data_inicial else None,
            "data_final": data_final.isoformat() if data_final else None,
            "observacao": " - ".join(observacao_parts)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

def gerar_pdf_relatorio_completo(db: Session, data_inicial: date | None = None, data_final: date | None = None) -> bytes:
    """
    Gera PDF do relatório completo com filtros de data
    """
    try:
        logger.info("Iniciando geração de PDF do relatório completo")
        
        query = db.query(ConfirmacaoServico).options(
            joinedload(ConfirmacaoServico.imagens)
        )
        
        if data_inicial:
            logger.info(f"Aplicando filtro de data inicial no PDF: {data_inicial}")
            query = query.filter(ConfirmacaoServico.data_servico >= data_inicial)
        
        if data_final:
            logger.info(f"Aplicando filtro de data final no PDF: {data_final}")
            query = query.filter(ConfirmacaoServico.data_servico <= data_final)
        
        confirmacoes = query.all()
        
        if not confirmacoes:
            raise HTTPException(status_code=404, detail="Nenhuma confirmação encontrada")
        
        confirmacoes_validas = [
            c for c in confirmacoes 
            if c.tag_doc and c.nome_vistoriador and c.tipo_servico and c.data_servico
        ]
        
        if not confirmacoes_validas:
            raise HTTPException(status_code=400, detail="Nenhuma confirmação com dados completos")
        
        logger.info(f"Gerando PDF visual com {len(confirmacoes_validas)} confirmações")
        
        pdf_buffer = _criar_pdf_visual(confirmacoes_validas, data_inicial, data_final)
        pdf_bytes = pdf_buffer.getvalue()
        
        logger.info(f"PDF gerado com sucesso - {len(pdf_bytes)} bytes")
        
        return pdf_bytes
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar PDF do relatório completo: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar PDF: {str(e)}"
        )

def _criar_pdf_visual(confirmacoes: list[ConfirmacaoServico], data_inicial: date | None = None, data_final: date | None = None) -> BytesIO:
    """
    Cria PDF visualmente atraente com cards formatados
    """
    try:
        logger.info(f"Criando PDF visual com {len(confirmacoes)} confirmações...")
        
        # Expandir confirmações em cards individuais
        cards_data = _expandir_confirmacoes_em_cards_imagem(confirmacoes)
        total_cards = len(cards_data)
        total_confirmacoes = len(confirmacoes)
        
        # Configurar documento PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=25*mm
        )
        
        story = []
        
        header_elements = criar_header_completo(
            total_confirmacoes, 
            total_cards, 
            data_inicial, 
            data_final
        )
        story.extend(header_elements)
        
        # Processar cards em linhas de 3
        cards_por_linha = 3
        
        for i in range(0, total_cards, cards_por_linha):
            linha_cards_data = cards_data[i:i + cards_por_linha]
            
            card_data = []
            for conf, img in linha_cards_data:
                card_content = criar_card_individual(conf, img)
                card_data.append(card_content)
            
            # Preencher linha se não tiver 3 cards
            while len(card_data) < cards_por_linha:
                card_data.append("")
            
            # Criar tabela para esta linha
            tabela = Table(
                [card_data],
                colWidths=[85*mm, 85*mm, 85*mm],
                rowHeights=[70*mm]
            )
            
            # Estilo da tabela
            tabela.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
                ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
            ]))
            
            story.append(tabela)
            story.append(Spacer(1, 8*mm))
            
            # Page break a cada 2 linhas (6 cards)
            if (i + cards_por_linha) % 6 == 0 and i + cards_por_linha < total_cards:
                story.append(PageBreak())
        
        doc.build(
            story, 
            onFirstPage=adicionar_background_e_footer, 
            onLaterPages=adicionar_background_e_footer
        )
        pdf_buffer.seek(0)
        
        logger.info(f"PDF visual criado com sucesso - {len(pdf_buffer.getvalue())} bytes")
        return pdf_buffer
        
    except Exception as e:
        logger.error(f"Erro ao criar PDF visual: {str(e)}", exc_info=True)
        raise
