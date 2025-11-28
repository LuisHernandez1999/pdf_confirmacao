import logging
import base64
from io import BytesIO
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from domain.models.relatorio_confirmacao import RelatorioConfirmacao
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao
import requests
from PIL import Image as PILImage
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader  # Corrigindo import do ImageReader para o módulo correto
import traceback

logger = logging.getLogger("relatorio_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDO_PATH = Path(__file__).resolve().parents[2] / "imagens" / "fundo.jpeg"
LOGO_PATH = Path(__file__).resolve().parents[2] / "imagens" / "limpalogo.png"

# Verificar se o arquivo existe
if not FUNDO_PATH.exists():
    logger.warning(f"Arquivo de fundo não encontrado em: {FUNDO_PATH}")
    logger.warning(f"Diretório atual: {Path(__file__).resolve()}")
else:
    logger.info(f"Arquivo de fundo encontrado: {FUNDO_PATH}")

if not LOGO_PATH.exists():
    logger.warning(f"Arquivo de logo não encontrado em: {LOGO_PATH}")
    logger.warning(f"Diretório atual: {Path(__file__).resolve()}")
else:
    logger.info(f"Arquivo de logo encontrado: {LOGO_PATH}")

COLORS = {
    'primary': '#2D5016',
    'secondary': '#4A8C5E',
    'accent': '#6BBF59',
    'text': '#2D3748',
    'light': '#EDF2F7',
    'border': '#CBD5E0',
    'white': '#FFFFFF',
}

def _encode_image_base64(image_path: str) -> str | None:
    """Codifica imagem em base64 para usar no SVG"""
    try:
        if not os.path.exists(image_path):
            logger.error(f"Arquivo não encontrado: {image_path}")
            return None
            
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            logger.info(f"Imagem codificada com sucesso: {len(encoded)} caracteres")
            return encoded
    except Exception as e:
        logger.error(f"Erro ao carregar fundo: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def _download_imagem(url: str) -> str | None:
    """Baixa imagem da URL e retorna em base64"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        img = PILImage.open(BytesIO(response.content))
        img.thumbnail((600, 400), PILImage.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True, quality=95)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    except Exception as e:
        logger.error(f"Erro ao baixar imagem {url}: {e}")
        return None

# ===================== CARD COM CARROSSEL RESPONSIVO =====================
def _gerar_card_com_carrossel(confirmacao: ConfirmacaoServico, card_id: str, x: int, y: int) -> str:
    """Gera card com carrossel responsivo"""
    imagens = confirmacao.imagens or []
    total_imagens = len(imagens)

    imagens_b64 = []
    if imagens:
        with ThreadPoolExecutor() as pool:
            resultados = pool.map(_download_imagem, [img.imagem for img in imagens])
            imagens_b64 = [r for r in resultados if r]

    largura_card = 340
    altura_card = 510
    altura_fotos = 200

    linhas = [f'<g transform="translate({x},{y})">']
    linhas.append(f'<rect x="0" y="0" width="{largura_card}" height="{altura_card}" fill="white" stroke="{COLORS["border"]}" stroke-width="2" rx="12" filter="url(#sombra)"/>')

    # === IMAGENS COM CLIPPING ===
    if imagens_b64:
        linhas.append(f'<clipPath id="clip_{card_id}"><rect x="10" y="10" width="{largura_card-20}" height="{altura_fotos}" rx="10"/></clipPath>')
        linhas.append(f'<g clip-path="url(#clip_{card_id})"><g id="slides_{card_id}">')
        for i, img64 in enumerate(imagens_b64):
            linhas.append(f'<image x="{10 + i * (largura_card-20)}" y="10" width="{largura_card-20}" height="{altura_fotos}" href="{img64}" preserveAspectRatio="xMidYMid slice"/>')
        linhas.append('</g></g>')

        # BOTÕES DE NAVEGAÇÃO
        if total_imagens > 1:
            linhas.append(f'''
                <g onclick="navegar('{card_id}', -1)" style="cursor:pointer"><circle cx="35" cy="{altura_fotos/2 + 10}" r="22" fill="{COLORS["primary"]}" opacity="0.8"/><text x="35" y="{altura_fotos/2 + 18}" font-size="28" fill="white" text-anchor="middle">‹</text></g>
                <g onclick="navegar('{card_id}', 1)" style="cursor:pointer"><circle cx="{largura_card-35}" cy="{altura_fotos/2 + 10}" r="22" fill="{COLORS["primary"]}" opacity="0.8"/><text x="{largura_card-35}" y="{altura_fotos/2 + 18}" font-size="28" fill="white" text-anchor="middle">›</text></g>
                <text id="contador_{card_id}" x="{largura_card/2}" y="{altura_fotos + 35}" font-size="13" text-anchor="middle" fill="{COLORS["text"]}">1 / {total_imagens}</text>
            ''')
    else:
        linhas.append(f'''
            <rect x="10" y="10" width="{largura_card-20}" height="{altura_fotos}" fill="{COLORS["light"]}" rx="10"/>
            <text x="{largura_card/2}" y="{altura_fotos/2 + 10}" font-size="18" font-weight="bold" text-anchor="middle" fill="#e74c3c">SEM IMAGENS</text>
        ''')

    # === INFORMAÇÕES DO CARD ===
    y_info = 250

    # DOC
    tag_doc = confirmacao.tag_doc or "NULO"
    linhas.append(f'<rect x="10" y="{y_info}" width="{largura_card-20}" height="34" fill="{COLORS["primary"]}" rx="8"/>')
    linhas.append(f'<text x="{largura_card/2}" y="{y_info+22}" font-size="13" font-weight="bold" text-anchor="middle" fill="white">DOC: {tag_doc}</text>')

    y_info += 50

    dados = [
        ("Vistoriador", confirmacao.nome_vistoriador or "NULO"),
        ("Serviço",     confirmacao.tipo_servico     or "NULO"),
        ("Data",        confirmacao.data_servico.strftime("%d/%m/%Y") if confirmacao.data_servico else "NULO"),
    ]

    for rotulo, valor in dados:
        linhas.append(f'<text x="15" y="{y_info}" font-size="11" fill="{COLORS["primary"]}" font-weight="bold">{rotulo}:</text>')
        linhas.append(f'<text x="15" y="{y_info+18}" font-size="15" fill="{COLORS["text"]}" font-weight="bold">{valor}</text>')
        y_info += 40

    # LOCALIZAÇÃO
    if confirmacao.latitude and confirmacao.longitude:
        link = f"https://www.google.com/maps?q={confirmacao.latitude},{confirmacao.longitude}"
        linhas.append(f'''
            <text x="15" y="{y_info}" font-size="11" fill="{COLORS["primary"]}" font-weight="bold">Localização:</text>
            <a href="{link}" target="_blank">
                <rect x="15" y="{y_info+10}" width="{largura_card-30}" height="40" fill="{COLORS["light"]}" stroke="{COLORS["accent"]}" stroke-width="2" rx="8"/>
                <text x="{largura_card/2}" y="{y_info+33}" font-size="11" text-anchor="middle" fill="{COLORS["text"]}">📍 {confirmacao.latitude:.6f}, {confirmacao.longitude:.6f}</text>
            </a>
        ''')
    else:
        linhas.append(f'<text x="15" y="{y_info}" font-size="13" fill="#e74c3c" font-weight="bold">Localização: NULO</text>')

    linhas.append('</g>')
    return "\n".join(linhas)

# ===================== SVG COMPLETO RESPONSIVO =====================
def gerar_svg_relatorio_completo(confirmacoes: list[ConfirmacaoServico], para_pdf: bool = False) -> str:
    """
    Gera SVG completo com todas as confirmações lado a lado, sem paginação.
    """
    PAGE_WIDTH = 2000
    HEADER_HEIGHT = 240  # Increased for company name under logo
    FOOTER_HEIGHT = 80   # Added footer height
    CARD_WIDTH = 700
    CARD_HEIGHT = 600
    CARDS_PER_ROW = 1
    ESPACO_X = 0
    ESPACO_Y = 60

    total = len(confirmacoes)
    linhas = total
    PAGE_HEIGHT = HEADER_HEIGHT + linhas * (CARD_HEIGHT + ESPACO_Y) + FOOTER_HEIGHT + 100  # Added footer

    svg = [f'''<svg width="100%" height="100%" viewBox="0 0 {PAGE_WIDTH} {PAGE_HEIGHT}" 
        xmlns="http://www.w3.org/2000/svg" 
        preserveAspectRatio="xMidYMid meet"
        style="background:white; font-family: 'Arial', 'Helvetica', sans-serif; max-width: {PAGE_WIDTH}px; margin: 0 auto; display: block;">''']

    fundo = _encode_image_base64(str(FUNDO_PATH))
    if fundo:
        svg.append(f'<image href="data:image/jpeg;base64,{fundo}" width="{PAGE_WIDTH}" height="{PAGE_HEIGHT}" preserveAspectRatio="xMidYMid slice"/>')

    svg.append('''
    <defs>
        <filter id="sombra">
            <feDropShadow dx="0" dy="6" stdDeviation="8" flood-opacity="0.25"/>
        </filter>
    </defs>
    ''')

    if not para_pdf:
        svg.append('''
        <script type="text/javascript"><![CDATA[
            const estado = {};
            function navegar(id, dir) {
                if (!estado[id]) {
                    const total = document.querySelectorAll('#slides_' + id + ' image').length || 1;
                    estado[id] = {atual: 0, total: total};
                }
                let e = estado[id];
                e.atual = (e.atual + dir + e.total) % e.total;
                const desl = -e.atual * 670;
                document.getElementById('slides_' + id).setAttribute('transform', `translate(${desl + 15},15)`);
                document.getElementById('contador_' + id).textContent = (e.atual + 1) + " / " + e.total;
            }
        ]]></script>
        ''')

    logo_base64 = _encode_image_base64(str(LOGO_PATH))
    svg.append(f'''
        <rect x="0" y="0" width="{PAGE_WIDTH}" height="{HEADER_HEIGHT}" fill="rgba(255,255,255,0.95)" filter="url(#sombra)"/>
    ''')
    
    if logo_base64:
        svg.append(f'''
            <g>
                <image href="data:image/png;base64,{logo_base64}" x="50" y="30" width="100" height="100" preserveAspectRatio="xMidYMid meet"/>
                <text x="100" y="155" font-size="18" font-weight="bold" text-anchor="middle" fill="#2D5016">Consórcio LimpaGyn</text>
            </g>
        ''')
    
    svg.append(f'''
        <text x="{PAGE_WIDTH/2}" y="70" font-size="42" font-weight="bold" text-anchor="middle" fill="#2D5016">RELATÓRIO CONFIRMAÇÃO SERVIÇO</text>
        <text x="{PAGE_WIDTH/2}" y="115" font-size="22" text-anchor="middle" fill="#2D5016" opacity="0.95">Confirmações neste Relatório: {total}</text>
        <text x="{PAGE_WIDTH/2}" y="150" font-size="16" text-anchor="middle" fill="#2D5016" opacity="0.85">Gerado em: {datetime.now().strftime("%d/%m/%Y")}</text>
    ''')

    y_inicio = HEADER_HEIGHT + 40
    x_card = (PAGE_WIDTH - CARD_WIDTH) / 2
    
    for i, conf in enumerate(confirmacoes):
        y_card = y_inicio + i * (CARD_HEIGHT + ESPACO_Y)
        svg.append(_gerar_card_com_carrossel(conf, f"c{i}", int(x_card), y_card))

    footer_y = PAGE_HEIGHT - FOOTER_HEIGHT
    svg.append(f'''
        <rect x="0" y="{footer_y}" width="{PAGE_WIDTH}" height="{FOOTER_HEIGHT}" fill="rgba(255,255,255,0.95)" filter="url(#sombra)"/>
        <text x="{PAGE_WIDTH/2}" y="{footer_y + 35}" font-size="20" font-weight="bold" text-anchor="middle" fill="#2D5016">Consórcio LimpaGyn</text>
        <text x="{PAGE_WIDTH/2}" y="{footer_y + 60}" font-size="14" text-anchor="middle" fill="#4A8C5E">Relatório gerado automaticamente</text>
    ''')

    svg.append('</svg>')
    return ''.join(svg)

# ===================== HTML COM PAGINAÇÃO =====================
def gerar_html_relatorio_paginado(confirmacoes: list[ConfirmacaoServico], cards_por_pagina: int = 6) -> str:
    """Gera HTML completo com paginação responsiva (6 cards por página)"""
    
    total_confirmacoes = len(confirmacoes)
    total_paginas = (total_confirmacoes + cards_por_pagina - 1) // cards_por_pagina
    
    fundo_base64 = _encode_image_base64(str(FUNDO_PATH))
    logo_base64 = _encode_image_base64(str(LOGO_PATH))
    
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Completo</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f5f5f5;
            padding: 0;
            margin: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .background {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            object-fit: cover;
        }}
        .container {{ 
            position: relative;
            z-index: 1;
            max-width: 1400px; 
            margin: 0 auto;
            padding: 20px;
            flex: 1;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.98);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
        }}
        .header-logo-section {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }}
        .header-logo {{
            width: 120px;
            height: 120px;
            object-fit: contain;
        }}
        .company-name {{
            color: #2D5016;
            font-size: 1.3em;
            font-weight: bold;
        }}
        .header-content {{
            flex: 1;
            min-width: 300px;
        }}
        .header h1 {{ color: #2D5016; font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ color: #4A8C5E; font-size: 1.2em; margin: 5px 0; }}
        
        .footer {{
            background: rgba(255, 255, 255, 0.98);
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
            text-align: center;
            margin-top: 40px;
            backdrop-filter: blur(10px);
            position: relative;
            z-index: 1;
        }}
        .footer h3 {{
            color: #2D5016;
            font-size: 1.5em;
            margin-bottom: 8px;
        }}
        .footer p {{
            color: #4A8C5E;
            font-size: 1em;
        }}
    </style>
</head>
<body>
    {'<img src="data:image/jpeg;base64,' + fundo_base64 + '" alt="" class="background">' if fundo_base64 else ''}
    <div class="container">
        <div class="header">
            {'<div class="header-logo-section"><img src="data:image/png;base64,' + logo_base64 + '" alt="LimpGyn Logo" class="header-logo"><div class="company-name">Consórcio LimpaGyn</div></div>' if logo_base64 else ''}
            <div class="header-content">
                <h1>RELATÓRIO COMPLETO</h1>
                <p>Confirmações neste Relatório: {total_confirmacoes}</p>
                <p style="font-size: 0.9em; opacity: 0.8;">Gerado em: {datetime.now().strftime("%d/%m/%Y")}</p>
            </div>
        </div>
        
       
        
        <div class="cards-grid">
    """
    
    # Gerar páginas com cards
    for pagina_num in range(total_paginas):
        inicio = pagina_num * cards_por_pagina
        fim = min(inicio + cards_por_pagina, total_confirmacoes)
        cards_pagina = confirmacoes[inicio:fim]
        
        html += f'<div class="pagina {"ativa" if pagina_num == 0 else ""}" data-pagina="{pagina_num}">'
        
        for i, conf in enumerate(cards_pagina):
            card_id = f"p{pagina_num}_c{i}"
            
            svg_card = f'''
            <div class="svg-container">
                <svg width="340" height="510" viewBox="0 0 340 510" xmlns="http://www.w3.org/2000/svg" style="font-family: Arial, sans-serif;">
                    <defs>
                        <filter id="sombra_{card_id}">
                            <feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.2"/>
                        </filter>
                    </defs>
                    <script type="text/javascript"><![CDATA[
                        window.estado_{card_id} = {{atual: 0, total: {len(conf.imagens) if conf.imagens else 0}}};
                        window.navegar_{card_id} = function(dir) {{
                            let e = window.estado_{card_id};
                            if (e.total <= 1) return;
                            e.atual = (e.atual + dir + e.total) % e.total;
                            const desl = -e.atual * 320;
                            document.getElementById('slides_{card_id}').setAttribute('transform', 'translate(' + desl + ',0)');
                            document.getElementById('contador_{card_id}').textContent = (e.atual + 1) + " / " + e.total;
                        }};
                    ]]></script>
                    {_gerar_card_com_carrossel(conf, card_id, 0, 0).replace(f"onclick=\"navegar('{card_id}'", f"onclick=\"navegar_{card_id}(")}
                </svg>
            </div>
            '''
            html += svg_card
        
        html += '</div>'
    
    html += f'''
        </div>
    </div>
</body>
</html>
    '''
    
    return html

# ===================== FUNÇÃO PRINCIPAL =====================
def gerar_relatorio_completo(db: Session) -> dict[str, str]:
    try:
        logger.info("Iniciando geração de relatório completo")
        
        todas = db.query(ConfirmacaoServico).options(joinedload(ConfirmacaoServico.imagens)).all()

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

        primeira_tag = confirmacoes_validas[0].tag_doc

        logger.info(f"Gerando HTML paginado para {len(confirmacoes_validas)} confirmações válidas")
        html_final = gerar_html_relatorio_paginado(confirmacoes_validas)

        relatorio = RelatorioConfirmacao(
            confirmacao_tag=primeira_tag,
            observacao=f"RELATÓRIO COMPLETO - {len(confirmacoes_validas)} registros - {datetime.now():%d/%m/%Y %H:%M}"
        )
        db.get(relatorio)
        db.commit()
        db.refresh(relatorio)

        logger.info(f"✅ RELATÓRIO GERADO → {len(confirmacoes_validas)} cards com paginação")

        return {
            "id": relatorio.id,
            "html": html_final,  # Retorna HTML em vez de SVG
            "total_confirmacoes": len(confirmacoes_validas),
            "data_geracao": relatorio.data_geracao.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ===================== NOVA FUNÇÃO PARA GERAR PDF =====================
def gerar_pdf_relatorio_completo(db: Session) -> bytes:
    """
    Gera PDF completo com todas as confirmações usando reportlab puro.
    Retorna bytes do PDF pronto para download.
    """
    try:
        from domain.models.confirmacao_servico import ConfirmacaoServico
        
        logger.info("Iniciando geração de PDF do relatório completo")
        
        # Busca todas as confirmações
        confirmacoes = db.query(ConfirmacaoServico).options(
            joinedload(ConfirmacaoServico.imagens)
        ).all()
        
        if not confirmacoes:
            raise HTTPException(status_code=404, detail="Nenhuma confirmação encontrada")
        
        # Filtrar confirmações válidas
        confirmacoes_validas = [
            c for c in confirmacoes 
            if c.tag_doc and c.nome_vistoriador and c.tipo_servico and c.data_servico
        ]
        
        if not confirmacoes_validas:
            raise HTTPException(status_code=400, detail="Nenhuma confirmação com dados completos")
        
        logger.info(f"Gerando PDF visual com {len(confirmacoes_validas)} confirmações")
        
        # Gera PDF visual usando reportlab
        pdf_buffer = _criar_pdf_visual(confirmacoes_validas)
        pdf_bytes = pdf_buffer.getvalue()
        
        logger.info(f"PDF gerado com sucesso - {len(pdf_bytes)} bytes")
        
        return pdf_bytes
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar PDF do relatório completo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao gerar PDF: {str(e)}"
        )

# ===================== SVG PARA PDF COM REPORTLAB =====================
def _criar_pdf_visual(confirmacoes: list[ConfirmacaoServico]) -> BytesIO:
    """
    Cria PDF visualmente atraente com cards formatados usando reportlab puro.
    """
    try:
        logger.info(f"Criando PDF visual com {len(confirmacoes)} cards...")
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=landscape(A4),
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=25*mm  # Added space for footer
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Estilo customizado para título
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=32,
            textColor=HexColor('#2D5016'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para subtítulo
        subtitulo_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=HexColor('#4A8C5E'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        logo_base64 = _encode_image_base64(str(LOGO_PATH))
        if logo_base64:
            logo_data = base64.b64decode(logo_base64)
            logo_img = ImageReader(BytesIO(logo_data))
            logo = RLImage(BytesIO(logo_data), width=30*mm, height=30*mm)
            
            company_style = ParagraphStyle(
                'CompanyName',
                parent=styles['Normal'],
                fontSize=14,
                textColor=HexColor('#2D5016'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            company_name = Paragraph("Consórcio LimpaGyn", company_style)
            
            logo_section = Table([[logo], [company_name]], colWidths=[30*mm])
            logo_section.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Criar tabela para logo section + título
            header_data = [[logo_section, Paragraph("RELATÓRIO COMPLETO", titulo_style)]]
            header_table = Table(header_data, colWidths=[40*mm, 225*mm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ]))
            story.append(header_table)
        else:
            story.append(Paragraph("RELATÓRIO COMPLETO", titulo_style))
        
        story.append(Paragraph(
            f"Confirmações neste Relatório: {len(confirmacoes)}", 
            subtitulo_style
        ))
        story.append(Paragraph(
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", 
            subtitulo_style
        ))
        story.append(Spacer(1, 15*mm))

        # GERAR CARDS EM TABELA (3 por linha)
        cards_por_linha = 3
        
        for i in range(0, len(confirmacoes), cards_por_linha):
            linha_cards = confirmacoes[i:i + cards_por_linha]
            
            # Criar linha de cards
            card_data = []
            for conf in linha_cards:
                card_content = _criar_card_pdf(conf)
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
            if (i + cards_por_linha) % 6 == 0 and i + cards_por_linha < len(confirmacoes):
                story.append(PageBreak())
        
        # Gerar PDF com background and footer
        doc.build(story, onFirstPage=_add_background_and_footer, onLaterPages=_add_background_and_footer)
        pdf_buffer.seek(0)
        
        logger.info(f"PDF visual criado com sucesso - {len(pdf_buffer.getvalue())} bytes")
        return pdf_buffer
        
    except Exception as e:
        logger.error(f"Erro ao criar PDF visual: {str(e)}", exc_info=True)
        raise

# ===================== NOVA FUNÇÃO PARA CRIAR CADA CARD FORMATADO =====================
def _criar_card_pdf(conf: ConfirmacaoServico) -> Table:
    """
    Cria um card individual formatado para o PDF.
    """
    from reportlab.lib.colors import HexColor
    
    # Cores do design
    cor_primaria = HexColor('#2D5016')
    cor_secundaria = HexColor('#4A8C5E')
    cor_accent = HexColor('#6BBF59')
    cor_texto = HexColor('#2D3748')
    cor_borda = HexColor('#CBD5E0')
    
    # Estilo para labels
    label_style = ParagraphStyle(
        'Label',
        fontSize=8,
        textColor=cor_primaria,
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    
    # Estilo para valores
    valor_style = ParagraphStyle(
        'Valor',
        fontSize=10,
        textColor=cor_texto,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    
    # Estilo para DOC (cabeçalho)
    doc_style = ParagraphStyle(
        'Doc',
        fontSize=11,
        textColor=white,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    # Preparar dados
    tag_doc = conf.tag_doc or "NULO"
    vistoriador = conf.nome_vistoriador or "NULO"
    servico = conf.tipo_servico or "NULO"
    data = conf.data_servico.strftime("%d/%m/%Y") if conf.data_servico else "NULO"
    
    # Status de imagens
    if conf.imagens and len(conf.imagens) > 0:
        status_img = f"📷 {len(conf.imagens)} imagens"
        cor_status = cor_accent
    else:
        status_img = "❌ SEM IMAGENS"
        cor_status = HexColor('#e74c3c')
    
    # Localização
    if conf.latitude and conf.longitude:
        localizacao = f"📍 {conf.latitude:.6f}, {conf.longitude:.6f}"
    else:
        localizacao = "📍 Localização: NULO"
    
    # Criar conteúdo do card
    card_content = [
        # CABEÇALHO COM DOC
        [Paragraph(f"DOC: {tag_doc}", doc_style)],
        # STATUS DE IMAGENS
        [Paragraph(status_img, ParagraphStyle('Status', fontSize=9, textColor=cor_status, alignment=TA_CENTER, fontName='Helvetica-Bold'))],
        # VISTORIADOR
        [Paragraph("Vistoriador:", label_style)],
        [Paragraph(vistoriador, valor_style)],
        # SERVIÇO
        [Paragraph("Serviço:", label_style)],
        [Paragraph(servico, valor_style)],
        # DATA
        [Paragraph("Data:", label_style)],
        [Paragraph(data, valor_style)],
        # LOCALIZAÇÃO
        [Paragraph(localizacao, ParagraphStyle('Loc', fontSize=8, textColor=cor_texto, alignment=TA_CENTER))],
    ]
    
    # Criar tabela do card
    card_table = Table(
        card_content,
        colWidths=[78*mm],
        rowHeights=[10*mm, 6*mm, 4*mm, 6*mm, 4*mm, 6*mm, 4*mm, 6*mm, 8*mm]
    )
    
    # Aplicar estilo visual ao card
    card_table.setStyle(TableStyle([
        # Borda externa do card
        ('BOX', (0, 0), (-1, -1), 2, cor_borda),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        
        # Cabeçalho DOC (primeira linha)
        ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Status de imagens (segunda linha)
        ('BACKGROUND', (0, 1), (-1, 1), HexColor('#f8f9fa')),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        
        # Resto do conteúdo
        ('BACKGROUND', (0, 2), (-1, -2), white),
        ('LEFTPADDING', (0, 2), (-1, -2), 3*mm),
        ('RIGHTPADDING', (0, 2), (-1, -2), 3*mm),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Última linha (localização)
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#f8f9fa')),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        
        # Padding geral
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    
    return card_table

# ===================== FUNÇÃO PARA ADICIONAR FUNDO E FOOTER EM CADA PÁGINA DO PDF =====================
def _add_background_and_footer(canvas, doc):
    """
    Callback para adicionar imagem de fundo e footer em cada página do PDF.
    """
    try:
        if FUNDO_PATH.exists():
            canvas.saveState()
            
            # Obter dimensões da página
            width, height = landscape(A4)
            
            # Abrir imagem para obter dimensões originais
            from PIL import Image
            img = Image.open(str(FUNDO_PATH))
            img_width, img_height = img.size
            img_ratio = img_width / img_height
            page_ratio = width / height
            
            # Calcular dimensões mantendo aspect ratio e cobrindo toda a página
            if img_ratio > page_ratio:
                # Imagem mais larga - ajustar pela altura
                draw_height = height
                draw_width = height * img_ratio
                x = -(draw_width - width) / 2
                y = 0
            else:
                # Imagem mais alta - ajustar pela largura
                draw_width = width
                draw_height = width / img_ratio
                x = 0
                y = -(draw_height - height) / 2
            
            # Desenhar imagem de fundo sem opacidade
            canvas.drawImage(
                str(FUNDO_PATH), 
                x, y, 
                width=draw_width, 
                height=draw_height,
                mask='auto'
            )
            
            # Adicionar footer
            canvas.setFillColor(HexColor('#2D5016'))
            canvas.setFont('Helvetica-Bold', 16)
            canvas.drawCentredString(width / 2, 15*mm, "Consórcio LimpaGyn")
            
            canvas.setFillColor(HexColor('#4A8C5E'))
            canvas.setFont('Helvetica', 10)
            canvas.drawCentredString(width / 2, 10*mm, "Relatório gerado automaticamente")
            
            canvas.restoreState()
    except Exception as e:
        logger.error(f"Erro ao adicionar fundo e footer ao PDF: {e}")
