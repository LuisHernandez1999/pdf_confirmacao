import base64
from io import BytesIO
from datetime import datetime, date
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, A4
import logging
from PIL import Image as PILImage

from src.domain.models.confirmacao_servico import ConfirmacaoServico
from src.domain.models.imagem_confirmacao import ImagemConfirmacao
from src.styles.relatorio_styles import (
    get_styles, 
    get_card_colors, 
    LOGO_PATH, 
    FUNDO_PATH,
    COLORS
)

logger = logging.getLogger("relatorio_template")

def criar_header_completo(total_confirmacoes: int, total_cards: int, data_inicial: date | None, data_final: date | None):
    """
    Cria o header completo do PDF com logo, título e contadores
    Design clean e profissional com layout moderno
    
    Args:
        total_confirmacoes: Número total de confirmações
        total_cards: Número total de imagens
        data_inicial: Data inicial do filtro (opcional)
        data_final: Data final do filtro (opcional)
    
    Returns:
        Lista de elementos do platypus para adicionar à story
    """
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.utils import ImageReader

    styles = get_styles()
    colors = get_card_colors()
    elements = []

    logo_base64 = _encode_image_base64(str(LOGO_PATH))
    
    if logo_base64:
        logo_data = base64.b64decode(logo_base64)
        logo_img = RLImage(BytesIO(logo_data), width=32*mm, height=32*mm)

        # Informações da empresa - layout vertical compacto
        company_info = [
            [Paragraph("Consórcio LimpaGyn", styles['company_name'])],
            [Paragraph("Relatórios de Serviço", styles['tagline'])]
        ]
        company_info_table = Table(company_info, colWidths=[90*mm])
        company_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ]))

        # Logo + Company info (esquerda)
        header_left_content = [[logo_img, company_info_table]]
        header_left = Table(header_left_content, colWidths=[35*mm, 90*mm])
        header_left.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        header_left = Paragraph("Consórcio LimpaGyn", styles['company_name'])

    data_geracao = datetime.now().strftime('%d/%m/%Y')
    data_content = [
        [Paragraph(f"{data_geracao}", styles['data_grande'])]
    ]
    data_table = Table(data_content, colWidths=[45*mm])
    data_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    top_header = Table(
        [[header_left, data_table]], 
        colWidths=[220*mm, 45*mm]
    )
    top_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(top_header)
    elements.append(Spacer(1, 8*mm))

    titulo_content = [
        [Paragraph("Relatório de Confirmações", styles['titulo_principal'])],
        [Paragraph("Análise completa dos serviços realizados", styles['subtitulo'])]
    ]
    titulo_table = Table(titulo_content, colWidths=[265*mm])
    titulo_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))

    elements.append(titulo_table)
    elements.append(Spacer(1, 10*mm))

    contadores = criar_contadores(total_confirmacoes, total_cards, data_inicial, data_final)
    elements.append(contadores)
    elements.append(Spacer(1, 10*mm))

    separador = Table([['']], colWidths=[265*mm], rowHeights=[0.5])
    separador.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors['separador']),
    ]))
    elements.append(separador)
    elements.append(Spacer(1, 8*mm))

    return elements

def criar_contadores(total_confirmacoes: int, total_cards: int, data_inicial: date | None, data_final: date | None):
    """
    Cria os cards de contadores com design minimalista e profissional
    
    Args:
        total_confirmacoes: Número de confirmações
        total_cards: Número de imagens
        data_inicial: Data inicial do período
        data_final: Data final do período
    
    Returns:
        Table com os contadores em layout horizontal
    """
    styles = get_styles()
    colors = get_card_colors()

    contador_confirmacoes = [
        [Paragraph(str(total_confirmacoes), styles['contador_numero'])],
        [Paragraph("Confirmações", styles['contador_label'])]
    ]

    contador_imagens = [
        [Paragraph(str(total_cards), styles['contador_numero'])],
        [Paragraph("Imagens", styles['contador_label'])]
    ]

    periodo_display = ""
    if data_inicial and data_final:
        periodo_display = f"{data_inicial.strftime('%d/%m/%Y')} — {data_final.strftime('%d/%m/%Y')}"
    elif data_inicial:
        periodo_display = f"A partir de {data_inicial.strftime('%d/%m/%Y')}"
    elif data_final:
        periodo_display = f"Até {data_final.strftime('%d/%m/%Y')}"
    else:
        periodo_display = "Todos os períodos"

    contador_periodo = [
        [Paragraph("Período", styles['periodo_label'])],
        [Paragraph(periodo_display, styles['periodo_text'])]
    ]

    table_conf = Table(contador_confirmacoes, colWidths=[65*mm])
    table_conf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors['contador_bg']),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors['contador_borda']),
        ('LEFTPADDING', (0, 0), (-1, -1), 5*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 5*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5*mm),
    ]))

    table_img = Table(contador_imagens, colWidths=[65*mm])
    table_img.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors['contador_bg']),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors['contador_borda']),
        ('LEFTPADDING', (0, 0), (-1, -1), 5*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 5*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5*mm),
    ]))

    table_periodo = Table(contador_periodo, colWidths=[120*mm])
    table_periodo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors['contador_bg']),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors['contador_borda']),
        ('LEFTPADDING', (0, 0), (-1, -1), 5*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5*mm),
        ('TOPPADDING', (0, 0), (-1, -1), 5*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5*mm),
    ]))

    contadores_row = Table(
        [[table_conf, table_img, table_periodo]], 
        colWidths=[70*mm, 70*mm, 125*mm],
        spaceBefore=0,
        spaceAfter=0
    )
    contadores_row.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 2.5*mm),
        ('LEFTPADDING', (1, 0), (1, 0), 2.5*mm),
        ('RIGHTPADDING', (1, 0), (1, 0), 2.5*mm),
        ('LEFTPADDING', (2, 0), (2, 0), 2.5*mm),
        ('RIGHTPADDING', (2, 0), (2, 0), 0),
    ]))

    return contadores_row

def criar_card_individual(conf: dict, img: dict | None) -> Table:
    """
    Cria um card individual formatado para o PDF
    Adaptado para trabalhar com dicionários, sem objetos ORM
    """

    styles = get_styles()
    colors = get_card_colors()

    # Preparar dados vindo de dict
    tag_doc = conf.get("tag_doc", "NULO")
    vistoriador = conf.get("nome_vistoriador", "NULO")
    servico = conf.get("tipo_servico", "NULO")

    data_serv = conf.get("data_servico")
    if isinstance(data_serv, (date, datetime)):
        data = data_serv.strftime("%d/%m/%Y")
    else:
        data = "NULO"

    # Status de imagem
    if img and img.get("imagem"):
        status_img = "📷 Imagem disponível"
        cor_status = colors['accent']
    else:
        status_img = "❌ SEM IMAGEM"
        cor_status = colors['erro']

    # Localização
    latitude = None
    longitude = None
    if img:
        latitude = img.get("latitude")
        longitude = img.get("longitude")

    if latitude and longitude:
        localizacao = f"📍 {latitude:.6f}, {longitude:.6f}"
    else:
        localizacao = "📍 Localização: NULO"

    # Criar conteúdo do card
    status_style = styles['card_status'].clone('StatusClone')
    status_style.textColor = cor_status

    card_content = [
        [Paragraph(f"DOC: {tag_doc}", styles['card_doc'])],
        [Paragraph(status_img, status_style)],
        [Paragraph("Vistoriador:", styles['card_label'])],
        [Paragraph(vistoriador, styles['card_valor'])],
        [Paragraph("Serviço:", styles['card_label'])],
        [Paragraph(servico, styles['card_valor'])],
        [Paragraph("Data:", styles['card_label'])],
        [Paragraph(data, styles['card_valor'])],
        [Paragraph(localizacao, styles['card_localizacao'])],
    ]

    # Criar tabela do card
    card_table = Table(
        card_content,
        colWidths=[78*mm],
        rowHeights=[10*mm, 6*mm, 4*mm, 6*mm, 4*mm, 6*mm, 4*mm, 6*mm, 8*mm]
    )

    # Aplicar estilo visual ao card
    card_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors['borda']),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ('BACKGROUND', (0, 0), (-1, 0), colors['primaria']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, 1), colors['fundo_claro']),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('BACKGROUND', (0, 2), (-1, -2), white),
        ('LEFTPADDING', (0, 2), (-1, -2), 3*mm),
        ('RIGHTPADDING', (0, 2), (-1, -2), 3*mm),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, -1), (-1, -1), colors['fundo_claro']),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))

    return card_table

def adicionar_background_e_footer(canvas, doc):
    """
    Callback para adicionar imagem de fundo e footer em cada página do PDF
    
    Args:
        canvas: Canvas do ReportLab
        doc: Documento do ReportLab
    """
    try:
        if FUNDO_PATH.exists():
            canvas.saveState()

            width, height = landscape(A4)

            # Abrir imagem para obter dimensões originais
            img = PILImage.open(str(FUNDO_PATH))
            img_width, img_height = img.size
            img_ratio = img_width / img_height
            page_ratio = width / height

            # Calcular dimensões mantendo aspect ratio
            if img_ratio > page_ratio:
                draw_height = height
                draw_width = height * img_ratio
                x = -(draw_width - width) / 2
                y = 0
            else:
                draw_width = width
                draw_height = width / img_ratio
                x = 0
                y = -(draw_height - height) / 2

            # Desenhar imagem de fundo
            canvas.drawImage(
                str(FUNDO_PATH), 
                x, y, 
                width=draw_width, 
                height=draw_height,
                mask='auto'
            )

            canvas.setFillColor(HexColor(COLORS['primary']))
            canvas.setFont('Helvetica-Bold', 10)
            canvas.drawCentredString(width / 2, 12*mm, "Consórcio LimpaGyn")

            canvas.setFillColor(HexColor(COLORS['text_secondary']))
            canvas.setFont('Helvetica', 8)
            canvas.drawCentredString(width / 2, 8*mm, "Relatório gerado automaticamente")

            canvas.restoreState()
    except Exception as e:
        logger.error(f"Erro ao adicionar fundo e footer ao PDF: {e}")

def _encode_image_base64(image_path: str) -> str | None:
    """Codifica imagem em base64"""
    import os
    import traceback

    try:
        if not os.path.exists(image_path):
            logger.error(f"Arquivo não encontrado: {image_path}")
            return None

        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            logger.info(f"Imagem codificada com sucesso: {len(encoded)} caracteres")
            return encoded
    except Exception as e:
        logger.error(f"Erro ao carregar imagem: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def gerar_relatorio_pdf(
    confirmacoes_validas: list[ConfirmacaoServico],
    imagens_por_confirmacao: dict[str, ImagemConfirmacao | None],
    data_inicial: date | None = None,
    data_final: date | None = None,
    output_path: str = "relatorio.pdf"
):
    from reportlab.platypus import SimpleDocTemplate, Table, Spacer, CondPageBreak

    total_confirmacoes = len(confirmacoes_validas)
    total_imagens = sum(1 for img in imagens_por_confirmacao.values() if img and img.imagem)

    story = []
    story.extend(criar_header_completo(total_confirmacoes, total_imagens, data_inicial, data_final))

    # Prepara os dados
    confirmacoes_com_imagens = [
        (conf, imagens_por_confirmacao.get(conf.tag_doc))
        for conf in confirmacoes_validas
    ]

    # ALTURA REAL de um card (some todas as rowHeights do criar_card_individual)
    ALTURA_CARD = 10+6+4+6+4+6+4+6+8  # = 54mm + margens ≈ 60-65mm com padding
    ALTURA_CARD_COM_ESPACO = 70*mm  # segurança + espaçamento entre linhas

    for i in range(0, len(confirmacoes_com_imagens), 3):
        batch = confirmacoes_com_imagens[i:i+3]
        cards_linha = []

        for conf, img in batch:
            card = criar_card_individual(conf, img)
            cards_linha.append(card)

        # Preenche com cards vazios se necessário (só pra manter layout)
        while len(cards_linha) < 3:
            vazio = Table([['']], colWidths=78*mm)
            vazio.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), white)]))
            cards_linha.append(vazio)

        # AQUI ESTÁ A MÁGICA: TABELA SEM rowHeights FIXO!
        linha_table = Table(
            [cards_linha],
            colWidths=[88*mm, 88*mm, 88*mm]
            # ← SEM rowHeights! ReportLab calcula automaticamente
        )
        linha_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('LEFTPADDING', (0,0), (-1,-1), 4*mm),
            ('RIGHTPADDING', (0,0), (-1,-1), 4*mm),
        ]))

        story.append(linha_table)
        story.append(Spacer(1, 8*mm))

        # FORÇA QUEBRA INTELIGENTE: só quebra se não couber mais UMA linha completa
        story.append(CondPageBreak(ALTURA_CARD_COM_ESPACO))

    # Remove possível página em branco no final
    story.append(CondPageBreak(50*mm))

    # Gera PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=15*mm, bottomMargin=25*mm
    )
    doc.build(story, onFirstPage=adicionar_background_e_footer, onLaterPages=adicionar_background_e_footer)

    logger.info(f"PDF gerado com sucesso: {output_path} | {total_confirmacoes} cards")
    return output_path