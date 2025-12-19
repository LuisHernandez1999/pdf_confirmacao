# utils/relatorio_pdf_utils.py
import logging
from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, CondPageBreak

from src.domain.models.confirmacao_servico import ConfirmacaoServico
from src.domain.models.imagem_confirmacao import ImagemConfirmacao

from src.styles.templates.relatorio_templates import (
    criar_header_completo,
    criar_card_individual,
    adicionar_background_e_footer
)

logger = logging.getLogger("relatorio_utils")

def setup_logger():
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

def expandir_confirmacoes_em_cards_imagem(confirmacoes: list[dict]) -> list[tuple[dict, dict | None]]:


    cards_data = []

    for conf in confirmacoes:
        imagens = conf.get("imagens", [])

        # Se tem imagens → 1 card por imagem
        if imagens:
            for img in imagens:
                cards_data.append((conf, img))

        else:
            # Sem imagens → 1 card sem imagem
            cards_data.append((conf, None))

    return cards_data

def aplicar_filtros_query(query, data_inicial: date | None = None, data_final: date | None = None, tipo_servico: str | None=None):
    if data_inicial:
        logger.info(f"Aplicando filtro de data inicial: {data_inicial}")
        query = query.filter(ConfirmacaoServico.data_servico >= data_inicial)
    if data_final:
        logger.info(f"Aplicando filtro de data final: {data_final}")
        query = query.filter(ConfirmacaoServico.data_servico <= data_final)
    if tipo_servico:
        query=query.filter(ConfirmacaoServico.tipo_servico<=tipo_servico)
    return query


def criar_pdf_visual(
    confirmacoes: list[ConfirmacaoServico],
    data_inicial: date | None = None,
    data_final: date | None = None,
    total_confirmacoes: int | None = None,   # opcional
    total_imagens: int | None = None          # ← MANTIVE O NOME ORIGINAL que o header espera!
) -> BytesIO:
    """
    Cria o PDF visual.
    Agora aceita total_imagens de fora → assim o cabeçalho mostra o número CORRETO após exclusão.
    """
    setup_logger()
    
    if total_confirmacoes is None:
        total_confirmacoes = len(confirmacoes)

    # Calcula quantas imagens realmente vão aparecer no PDF
    cards_data = expandir_confirmacoes_em_cards_imagem(confirmacoes)
    total_cards = len(cards_data)

    # Se não passaram o total_imagens, calcula aqui (fallback)
    if total_imagens is None:
        total_imagens = total_cards

    logger.info(f"PDF → {total_confirmacoes} confirmações | {total_imagens} imagens exibidas (cabeçalho)")

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
    
    # ← AQUI USA O total_imagens que veio de fora (ou o calculado)
    header_elements = criar_header_completo(
        total_confirmacoes,
        total_imagens,        # ← nome exatamente como o template espera
        data_inicial,
        data_final
    )
    story.extend(header_elements)

    # ... resto do código 100% igual (cards, tabelas, etc.)
    cards_por_linha = 3
    for i in range(0, total_cards, cards_por_linha):
        linha_cards_data = cards_data[i:i + cards_por_linha]
        card_data = []

        for conf, img in linha_cards_data:
            card_content = criar_card_individual(conf, img)
            card_data.append(card_content)
        
        while len(card_data) < cards_por_linha:
            vazio = Table([['']], colWidths=[78*mm])
            vazio.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), 'white')]))
            card_data.append(vazio)

        tabela = Table(
            [card_data],
            colWidths=[85*mm, 85*mm, 85*mm]
            # REMOVIDO rowHeights → agora ReportLab calcula sozinho e não pula páginas vazias
        )
        tabela.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
        ]))
        
        story.append(tabela)
        story.append(Spacer(1, 8*mm))
        
        
        story.append(CondPageBreak(80*mm))  
        
    story.append(CondPageBreak(50*mm))
    
    doc.build(
        story,
        onFirstPage=adicionar_background_e_footer,
        onLaterPages=adicionar_background_e_footer
    )
    
    pdf_buffer.seek(0)
    logger.info(f"PDF gerado → {total_confirmacoes} confirmações, {total_imagens} imagens no relatório")
    return pdf_buffer