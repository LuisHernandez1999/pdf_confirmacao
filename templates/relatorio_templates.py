"""
Templates e componentes visuais para geração de PDFs
"""
import base64
from io import BytesIO
from datetime import datetime, date
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import landscape, A4
import logging
from PIL import Image as PILImage

from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao
from templates.relatorio_styles import (
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
    
    # Carregar logo
    logo_base64 = _encode_image_base64(str(LOGO_PATH))
    
    if logo_base64:
        logo_data = base64.b64decode(logo_base64)
        logo_img = RLImage(BytesIO(logo_data), width=42*mm, height=42*mm)
        
        company_info = [
            [Paragraph("Consórcio LimpaGyn", styles['company_name'])],
            [Paragraph("Relatórios de Serviço Profissionais", styles['tagline'])]
        ]
        company_info_table = Table(company_info, colWidths=[80*mm])
        company_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        header_left_content = [[logo_img, company_info_table]]
        header_left = Table(header_left_content, colWidths=[45*mm, 80*mm])
        header_left.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ]))
    else:
        header_left = Paragraph("Consórcio LimpaGyn", styles['company_name'])
    
    titulo_content = [
        [Paragraph("RELATÓRIO COMPLETO", styles['titulo_principal'])],
        [Paragraph("Confirmações de Serviço", styles['subtitulo'])]
    ]
    titulo_table = Table(titulo_content, colWidths=[100*mm])
    titulo_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
    ]))
    
    data_geracao = datetime.now().strftime('%d/%m/%Y')
    hora_geracao = datetime.now().strftime('%H:%M')
    data_content = [
        [Paragraph(data_geracao, styles['data_grande'])],
        [Paragraph(hora_geracao, styles['hora_pequena'])]
    ]
    data_table = Table(data_content, colWidths=[40*mm])
    data_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    
    main_header = Table(
        [[header_left, titulo_table, data_table]], 
        colWidths=[128*mm, 100*mm, 42*mm]
    )
    main_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    
    elements.append(main_header)
    elements.append(Spacer(1, 12*mm))
    
    contadores = criar_contadores(total_confirmacoes, total_cards, data_inicial, data_final)
    elements.append(contadores)
    elements.append(Spacer(1, 12*mm))
    
    separador = Table([['']], colWidths=[260*mm], rowHeights=[1.5])
    separador.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2.5, colors['separador']),
    ]))
    elements.append(separador)
    elements.append(Spacer(1, 10*mm))
    
    return elements

def criar_contadores(total_confirmacoes: int, total_cards: int, data_inicial: date | None, data_final: date | None):
    """
    Cria os cards de contadores com cores
    
    Args:
        total_confirmacoes: Número de confirmações
        total_cards: Número de imagens
        data_inicial: Data inicial do período
        data_final: Data final do período
    
    Returns:
        Table com os três contadores
    """
    styles = get_styles()
    colors = get_card_colors()
    
    contador_confirmacoes = [
        [Paragraph(str(total_confirmacoes), styles['contador_numero'])],
        [Paragraph("CONFIRMAÇÕES", styles['contador_label'])]
    ]
    
    contador_imagens = [
        [Paragraph(str(total_cards), styles['contador_numero'])],
        [Paragraph("IMAGENS", styles['contador_label'])]
    ]
    
    periodo_display = ""
    if data_inicial and data_final:
        periodo_display = f"{data_inicial.strftime('%d/%m/%Y')} - {data_final.strftime('%d/%m/%Y')}"
    elif data_inicial:
        periodo_display = f"A partir de {data_inicial.strftime('%d/%m/%Y')}"
    elif data_final:
        periodo_display = f"Até {data_final.strftime('%d/%m/%Y')}"
    else:
        periodo_display = "Todos os períodos"
    
    contador_periodo = [
        [Paragraph("📅", styles['icon_style'])],
        [Paragraph(periodo_display, styles['periodo_text'])]
    ]
    
    table_conf = Table(contador_confirmacoes, colWidths=[70*mm])
    table_conf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors['contador_azul']),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors['borda_azul']),
        ('TOPPADDING', (0, 0), (-1, -1), 6*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6*mm),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    
    table_img = Table(contador_imagens, colWidths=[70*mm])
    table_img.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors['contador_verde']),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors['borda_verde']),
        ('TOPPADDING', (0, 0), (-1, -1), 6*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6*mm),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    
    table_periodo = Table(contador_periodo, colWidths=[90*mm])
    table_periodo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors['contador_amarelo']),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors['borda_amarela']),
        ('TOPPADDING', (0, 0), (-1, -1), 6*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6*mm),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    
    contadores_row = Table(
        [[table_conf, table_img, table_periodo]], 
        colWidths=[75*mm, 75*mm, 95*mm],
        spaceBefore=0,
        spaceAfter=0
    )
    contadores_row.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5*mm),
    ]))
    
    return contadores_row

def criar_card_individual(conf: ConfirmacaoServico, img: ImagemConfirmacao | None) -> Table:
    """
    Cria um card individual formatado para o PDF
    
    Args:
        conf: Confirmação de serviço
        img: Imagem da confirmação (opcional)
    
    Returns:
        Table formatada como card
    """
    styles = get_styles()
    colors = get_card_colors()
    
    # Preparar dados
    tag_doc = conf.tag_doc or "NULO"
    vistoriador = conf.nome_vistoriador or "NULO"
    servico = conf.tipo_servico or "NULO"
    data = conf.data_servico.strftime("%d/%m/%Y") if conf.data_servico else "NULO"
    
    # Status de imagem
    if img and img.imagem:
        status_img = "📷 Imagem disponível"
        cor_status = colors['accent']
    else:
        status_img = "❌ SEM IMAGEM"
        cor_status = colors['erro']
    
    # Localização
    if img and img.latitude and img.longitude:
        localizacao = f"📍 {img.latitude:.6f}, {img.longitude:.6f}"
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
            
            # Adicionar footer
            canvas.setFillColor(HexColor(COLORS['primary']))
            canvas.setFont('Helvetica-Bold', 16)
            canvas.drawCentredString(width / 2, 15*mm, "Consórcio LimpaGyn")
            
            canvas.setFillColor(HexColor(COLORS['secondary']))
            canvas.setFont('Helvetica', 10)
            canvas.drawCentredString(width / 2, 10*mm, "Relatório gerado automaticamente")
            
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
