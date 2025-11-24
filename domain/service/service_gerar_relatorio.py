import logging
from io import BytesIO
from datetime import datetime
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload
from domain.models.relatorio_confirmacao import RelatorioConfirmacao
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, BaseDocTemplate, Frame, PageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
import requests
from PIL import Image as PILImage
import os
from pathlib import Path
import folium
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("relatorio_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDO_PATH = Path(__file__).resolve().parents[2] / "imagens" / "fundo.jpeg"

# <CHANGE> Cache de estilos para evitar recriação em cada PDF
_STYLES_CACHE = None
_CM_TO_PX_FACTOR = 72 / 2.54  # Fator de conversão cm → pixels

def _get_styles_cache():
    """Retorna estilos em cache, evitando recriação"""
    global _STYLES_CACHE
    if _STYLES_CACHE is not None:
        return _STYLES_CACHE
    
    styles = getSampleStyleSheet()
    COLOR_PRIMARY = '#0F2944'
    COLOR_SECONDARY = '#1E5A96'
    COLOR_ACCENT = '#00A0D6'
    COLOR_TEXT = '#2D2D2D'
    COLOR_LIGHT = '#F5F7FA'
    COLOR_BORDER = '#D8E0E8'
    
    _STYLES_CACHE = {
        'colors': {
            'primary': COLOR_PRIMARY, 'secondary': COLOR_SECONDARY,
            'accent': COLOR_ACCENT, 'text': COLOR_TEXT,
            'light': COLOR_LIGHT, 'border': COLOR_BORDER
        },
        'titulo': ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=28, textColor=colors.HexColor(COLOR_PRIMARY),
            spaceAfter=2, alignment=TA_CENTER, fontName='Helvetica-Bold', leading=32
        ),
        'subtitulo': ParagraphStyle(
            'CustomSubtitle', parent=styles['Normal'],
            fontSize=12, textColor=colors.HexColor(COLOR_SECONDARY),
            spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold'
        ),
        'texto': ParagraphStyle(
            'CustomBody', parent=styles['Normal'],
            fontSize=9, textColor=colors.HexColor(COLOR_TEXT),
            spaceAfter=8, fontName='Helvetica', leading=12, alignment=TA_JUSTIFY
        ),
        'label': ParagraphStyle(
            'CustomLabel', parent=styles['Normal'],
            fontSize=8, textColor=colors.HexColor(COLOR_SECONDARY),
            fontName='Helvetica-Bold', spaceAfter=2
        )
    }
    return _STYLES_CACHE

def _cm_to_px(cm_value):
    """Conversão rápida cm → pixels"""
    return int(cm_value * _CM_TO_PX_FACTOR)

def _gerar_mapa_interativo(latitude: float, longitude: float, max_width: float = 6.5 * cm) -> BytesIO | None:
    """Gera mapa interativo com folium + screenshot via Selenium (ou fallback estático)"""
    try:
        lat = float(latitude)
        lon = float(longitude)

        # Criar mapa com folium
        mapa = folium.Map(
            location=[lat, lon],
            zoom_start=18,
            tiles='OpenStreetMap',
            control_scale=True
        )

        # Marcador com popup e ícone bonito
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(
                f"<b>Localização do Serviço</b><br>Lat: {lat:.6f}<br>Lon: {lon:.6f}<br>{datetime.now().strftime('%d/%m/%Y %H:%M')}",
                max_width=300
            ),
            tooltip="Clique para mais detalhes",
            icon=folium.Icon(color="blue", icon="map-marker", prefix='fa')
        ).add_to(mapa)

        # Círculo de 50m ao redor
        folium.Circle(
            location=[lat, lon],
            radius=50,
            color="#0066CC",
            weight=2,
            fill=True,
            fillColor="#3388FF",
            fillOpacity=0.2,
            popup="Área aproximada do serviço (50m)"
        ).add_to(mapa)

        # === Tentar usar Selenium para screenshot de alta qualidade ===
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By

            # Salvar HTML temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                mapa.save(f.name)
                html_path = f.name

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1000,1000")
            chrome_options.add_argument("--force-device-scale-factor=2")

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(f"file://{html_path}")
            
            # <CHANGE> Usar WebDriverWait explícito em vez de sleep fixo
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "leaflet-tile"))
                )
            except:
                time.sleep(2)

            screenshot = driver.get_screenshot_as_png()
            driver.quit()

            # Remover arquivo temporário
            try:
                os.unlink(html_path)
            except:
                pass

            # <CHANGE> Otimizar redimensionamento com cache de dimensões
            target_px = _cm_to_px(max_width)
            img = PILImage.open(BytesIO(screenshot))
            img = img.resize((target_px, target_px), PILImage.Resampling.LANCZOS)

            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True, quality=85)
            buffer.seek(0)
            logger.info("Mapa gerado com sucesso via Selenium")
            return buffer

        except ImportError:
            logger.warning("Selenium não instalado → usando fallback estático")
        except Exception as e:
            logger.warning(f"Selenium falhou ({e}) → usando fallback estático")

        # === Fallback: mapa estático de alta qualidade ===
        return _gerar_mapa_estatico(lat, lon, max_width)

    except Exception as e:
        logger.error(f"Erro crítico ao gerar mapa: {e}")
        return None


def _gerar_mapa_estatico(latitude: float, longitude: float, max_width: float = 6.5 * cm) -> BytesIO | None:
    """Fallback: mapa estático via Geoapify (gratuito até certo limite)"""
    try:
        url = (
            f"https://maps.geoapify.com/v1/staticmap?"
            f"style=osm-bright&width=1000&height=1000&center=lonlat:{longitude},{latitude}&zoom=18.5&"
            f"marker=lonlat:{longitude},{latitude};color:%233388ff;size:large;icon:map-marker&"
            f"apiKey=YOUR_GEOAPIFY_KEY_IF_NEEDED"
        ).replace("YOUR_GEOAPIFY_KEY_IF_NEEDED", "")

        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # <CHANGE> Otimizar conversão e redimensionamento
            target_px = _cm_to_px(max_width)
            img = PILImage.open(BytesIO(response.content))
            img = img.resize((target_px, target_px), PILImage.Resampling.LANCZOS)

            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True, quality=85)
            buffer.seek(0)
            logger.info("Mapa estático gerado com sucesso")
            return buffer

        logger.warning(f"Mapa estático falhou: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Erro no mapa estático: {e}")
        return None


def _download_imagem(url: str, max_width: float = 7 * cm) -> BytesIO | None:
    """Baixa imagem da URL e retorna BytesIO redimensionado"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        img = PILImage.open(BytesIO(response.content))
        
        # <CHANGE> Otimizar cálculos de proporção
        aspect_ratio = img.height / img.width
        new_width_px = _cm_to_px(max_width)
        new_height_px = int(new_width_px * aspect_ratio)
        
        img = img.resize((new_width_px, new_height_px), PILImage.Resampling.LANCZOS)
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG', optimize=True, quality=85)
        img_buffer.seek(0)
        return img_buffer
    except Exception as e:
        logger.error(f"Erro ao baixar/redimensionar imagem {url}: {e}")
        return None

def on_page_background(canvas, doc):
    """Desenha a imagem de fundo em TODAS as páginas"""
    if os.path.exists(FUNDO_PATH):
        try:
            canvas.setPageCompression(0)
            canvas.drawImage(
                FUNDO_PATH,
                0, 0,
                width=A4[0],
                height=A4[1],
                preserveAspectRatio=True,
                mask='auto',
                anchor='c'
            )
            logger.debug(f"Fundo aplicado na página {doc.page}")
        except Exception as e:
            logger.error(f"Erro ao desenhar fundo: {e}")
    else:
        logger.warning(f"Imagem de fundo não encontrada: {FUNDO_PATH}")

def on_page_footer(canvas, doc):
    """Desenha rodapé com número de página e data"""
    canvas.saveState()
    try:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor('#8B8B8B'))
        page_text = f"Página {doc.page}"
        if hasattr(doc, 'pageCount') and doc.pageCount > 0:
            page_text += f" de {doc.pageCount}"
        canvas.drawRightString(A4[0] - 1.5 * cm, 0.8 * cm, page_text)
        canvas.drawString(1.5 * cm, 0.8 * cm,
                          f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    finally:
        canvas.restoreState()

def gerar_pdf_relatorio(dados: dict, output_filename: str | None = None) -> BytesIO:
    buffer = BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
        title="Relatório de Confirmação de Serviço",
        author="Sistema"
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height,
        id='normal'
    )
    template = PageTemplate(
        id='com_fundo',
        frames=frame,
        onPage=on_page_background,
        onPageEnd=on_page_footer
    )
    doc.addPageTemplates([template])
    
    story = []
    # <CHANGE> Usar cache de estilos
    styles_cache = _get_styles_cache()
    COLOR_PRIMARY = styles_cache['colors']['primary']
    COLOR_SECONDARY = styles_cache['colors']['secondary']
    COLOR_ACCENT = styles_cache['colors']['accent']
    COLOR_TEXT = styles_cache['colors']['text']
    COLOR_LIGHT = styles_cache['colors']['light']
    COLOR_BORDER = styles_cache['colors']['border']
    
    style_titulo = styles_cache['titulo']
    style_subtitulo = styles_cache['subtitulo']
    style_texto = styles_cache['texto']
    style_label = styles_cache['label']
    
    # Título
    story.append(Paragraph("RELATÓRIO DE CONFIRMAÇÃO", style_titulo))
    story.append(Paragraph(f"<b>{dados['confirmacao_tag']}</b>", style_subtitulo))
    
    line = Table([['']], colWidths=[17 * cm])
    line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor(COLOR_ACCENT)),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(line)
    
    # Seção Informações do Serviço
    section_header = Table([['INFORMAÇÕES DO SERVIÇO']], colWidths=[17 * cm])
    section_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARY)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(section_header)
    
    confirmacao = dados['confirmacao']
    data_servico = confirmacao.get('data_servico', 'N/A')
    # <CHANGE> Otimizar parsing de data com try-except mais eficiente
    if isinstance(data_servico, str) and data_servico != 'N/A':
        try:
            data_servico = datetime.fromisoformat(data_servico.replace('Z', '+00:00')).strftime('%d/%m/%Y')
        except (ValueError, AttributeError):
            pass
    
    info_servico = [
        ['Vistoriador', confirmacao.get('nome_vistoriador', 'N/A')],
        ['Data do Serviço', str(data_servico)],
        ['Tipo de Serviço', confirmacao.get('tipo_servico', 'N/A')],
        ['Latitude', confirmacao.get('latitude', 'N/A')],
        ['Longitude', confirmacao.get('longitude', 'N/A')],
    ]
    table_info = Table(info_servico, colWidths=[4 * cm, 13 * cm])
    table_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(COLOR_SECONDARY)),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor(COLOR_TEXT)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLOR_BORDER)),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(COLOR_LIGHT)),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table_info)
    story.append(Spacer(1, 1 * cm))
    
    latitude = confirmacao.get('latitude')
    longitude = confirmacao.get('longitude')
    if latitude and longitude:
        localizacao_header = Table([['LOCALIZAÇÃO']], colWidths=[17 * cm])
        localizacao_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARY)),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(localizacao_header)
        story.append(Spacer(1, 0.5 * cm))
        
        # === MAPA INTERATIVO (com Selenium) ou ESTÁTICO ===
        buffer_mapa = _gerar_mapa_interativo(latitude, longitude)
        if buffer_mapa:
            img_mapa = RLImage(buffer_mapa, width=16 * cm, height=12 * cm, kind='proportional')
            mapa_table = Table([[img_mapa]], colWidths=[17 * cm])
            mapa_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOX', (0,0), (-1,-1), 2, colors.HexColor(COLOR_ACCENT)),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
                ('TOPPADDING', (0,0), (-1,-1), 20),
                ('BOTTOMPADDING', (0,0), (-1,-1), 20),
            ]))
            story.append(mapa_table)
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph(
                f"<font size=8 color=#555555>Coordenadas: {latitude}, {longitude}</font>",
                style_texto
            ))
        else:
            # Fallback apenas coordenadas
            fallback = Table([
                ['Latitude', str(latitude)],
                ['Longitude', str(longitude)]
            ], colWidths=[5*cm, 12*cm])
            fallback.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor(COLOR_BORDER)),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(COLOR_LIGHT)),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('TOPPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(fallback)

        story.append(Spacer(1, 1 * cm))
    
    # Registro Fotográfico
    photo_header = Table([['REGISTRO FOTOGRÁFICO']], colWidths=[17 * cm])
    photo_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARY)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(photo_header)
    story.append(Spacer(1, 0.5 * cm))
    
    imgs_utilizadas = dados.get('imagens_utilizadas', {})
    img_antes_url = imgs_utilizadas.get('antes', {}).get('url')
    img_depois_url = imgs_utilizadas.get('depois', {}).get('url')
    
    # <CHANGE> Usar ThreadPoolExecutor para download paralelo de imagens
    row_labels = []
    row_images = []
    
    def download_and_prepare(label, url):
        if url:
            buffer_img = _download_imagem(url, max_width=7 * cm)
            return (label, buffer_img)
        return None
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        if img_antes_url:
            futures.append(executor.submit(download_and_prepare, "ANTES", img_antes_url))
        if img_depois_url:
            futures.append(executor.submit(download_and_prepare, "DEPOIS", img_depois_url))
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                label_text, buffer_img = result
                if buffer_img:
                    img_rl = RLImage(buffer_img, width=7 * cm, height=7 * cm, kind='proportional')
                    row_images.append(img_rl)
                    row_labels.append(Paragraph(f"<b style='color:{COLOR_ACCENT}'>{label_text}</b>", style_label))
                else:
                    row_images.append(Paragraph("Imagem indisponível", style_texto))
                    row_labels.append(Paragraph(f"<b style='color:{COLOR_ACCENT}'>{label_text}</b>", style_label))
    
    if row_images:
        table_fotos = Table([row_labels, row_images], colWidths=[8.5 * cm, 8.5 * cm])
        table_fotos.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 1), (-1, 1), 1.5, colors.HexColor(COLOR_BORDER)),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor(COLOR_LIGHT)),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ]))
        story.append(table_fotos)
    
    story.append(Spacer(1, 1 * cm))
    
    # Observações
    obs_antes = dados.get('obs_antes')
    obs_depois = dados.get('obs_depois')
    observacao = dados.get('observacao')
    
    if obs_antes or obs_depois or observacao:
        obs_header = Table([['OBSERVAÇÕES']], colWidths=[17 * cm])
        obs_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_PRIMARY)),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(obs_header)
        story.append(Spacer(1, 0.5 * cm))
        
        if obs_antes:
            story.append(Paragraph(f"<b style='color:{COLOR_ACCENT}'>Observação (Antes):</b> {obs_antes}", style_texto))
            story.append(Spacer(1, 0.4 * cm))
        if obs_depois:
            story.append(Paragraph(f"<b style='color:{COLOR_ACCENT}'>Observação (Depois):</b> {obs_depois}", style_texto))
            story.append(Spacer(1, 0.4 * cm))
        if observacao:
            story.append(Paragraph(f"<b style='color:{COLOR_ACCENT}'>Observação Geral:</b> {observacao}", style_texto))
    
    doc.multiBuild(story)
    buffer.seek(0)
    logger.info(f"PDF gerado com sucesso: {output_filename or 'relatorio_confirmacao.pdf'}")
    return buffer

def gerar_relatorio(
    db: Session,
    confirmacao_tag: str,
    imagem_antes_id: int,
    imagem_depois_id: int,
    obs_antes: str | None = None,
    obs_depois: str | None = None,
    observacao: str | None = None,
) -> dict:
    # <CHANGE> Otimizar queries com eager loading
    confirmacao = db.query(ConfirmacaoServico).filter(
        ConfirmacaoServico.tag_doc == confirmacao_tag
    ).first()
    if not confirmacao:
        raise HTTPException(status_code=404, detail="Confirmação não encontrada.")
    
    # <CHANGE> Buscar ambas imagens em uma única query com IN
    imagens = db.query(ImagemConfirmacao).filter(
        ImagemConfirmacao.confirmacao_id == confirmacao.id,
        ImagemConfirmacao.id.in_([imagem_antes_id, imagem_depois_id])
    ).all()
    
    img_dict = {img.id: img for img in imagens}
    img_antes = img_dict.get(imagem_antes_id)
    img_depois = img_dict.get(imagem_depois_id)
    
    if not img_antes or not img_depois:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")
    
    if imagem_antes_id == imagem_depois_id:
        raise HTTPException(status_code=400, detail="Imagens devem ser diferentes.")
    
    relatorio = RelatorioConfirmacao(
        confirmacao_tag=confirmacao_tag,
        obs_antes=obs_antes,
        obs_depois=obs_depois,
        observacao=observacao,
    )
    db.add(relatorio)
    db.commit()
    
    relatorio_carregado = (
        db.query(RelatorioConfirmacao)
        .options(
            joinedload(RelatorioConfirmacao.confirmacao),
            joinedload(RelatorioConfirmacao.imagens)
        )
        .filter(RelatorioConfirmacao.id == relatorio.id)
        .first()
    )
    
    # <CHANGE> Construir dict de forma mais eficiente
    objeto_bruto = {
        "id": relatorio_carregado.id,
        "confirmacao_tag": relatorio_carregado.confirmacao_tag,
        "obs_antes": relatorio_carregado.obs_antes,
        "obs_depois": relatorio_carregado.obs_depois,
        "observacao": relatorio_carregado.observacao,
        "data_geracao": relatorio_carregado.data_geracao,
        "confirmacao": {
            "id": relatorio_carregado.confirmacao.id,
            "tag_doc": relatorio_carregado.confirmacao.tag_doc,
            "nome_vistoriador": relatorio_carregado.confirmacao.nome_vistoriador,
            "data_servico": relatorio_carregado.confirmacao.data_servico,
            "tipo_servico": relatorio_carregado.confirmacao.tipo_servico,
            "latitude": relatorio_carregado.confirmacao.latitude,
            "longitude": relatorio_carregado.confirmacao.longitude,
        },
        "imagens_utilizadas": {
            "antes": {"id": img_antes.id, "url": img_antes.imagem},
            "depois": {"id": img_depois.id, "url": img_depois.imagem}
        }
    }
    
    return jsonable_encoder(objeto_bruto)