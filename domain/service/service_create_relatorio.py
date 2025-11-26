import logging
import base64
from io import BytesIO
from datetime import datetime
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, joinedload
from domain.models.relatorio_confirmacao import RelatorioConfirmacao
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao
import requests
from PIL import Image as PILImage
import os
from pathlib import Path
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

COLORS = {
    'primary': '#2D5F3F',
    'secondary': '#4A8C5E',
    'accent': '#7BC996',
    'text': '#1F1F1F',
    'light': '#F0F5F2',
    'border': '#C8DCD0',
    'white': '#FFFFFF',
}

DIMENSIONS = {
    'page_width': 1100,
    'page_height': 1500,
    'margin': 50,
    'header_height': 110,
}

def _encode_image_base64(image_path: str) -> str | None:
    """Converte imagem para base64 para embedar no SVG"""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Erro ao encodar imagem {image_path}: {e}")
        return None

def _image_to_base64(buffer: BytesIO, format: str = 'PNG') -> str:
    """Converte BytesIO de imagem para base64"""
    if isinstance(buffer, BytesIO):
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    return ""

def _gerar_mapa_estatico_svg(latitude: float, longitude: float, width: int = 400, height: int = 300) -> str:
    """
    Gera um mapa estático com link direto para Google Maps.
    Retorna um elemento clicável que abre o mapa em nova aba.
    """
    try:
        url = (
            f"https://maps.geoapify.com/v1/staticmap?"
            f"style=osm-bright&width={width}&height={height}"
            f"&center=lonlat:{longitude},{latitude}&zoom=18&"
            f"marker=lonlat:{longitude},{latitude};color:%234A8C5E;size:large|"
            f"&apiKey="
        )
        
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            img_base64 = base64.b64encode(response.content).decode('utf-8')
            mapa_link = f"https://www.google.com/maps?q={latitude},{longitude}"
            return f'''
            <a href="{mapa_link}" target="_blank" style="cursor: pointer;">
                <image x="0" y="0" width="{width}" height="{height}" 
                       href="data:image/png;base64,{img_base64}" 
                       style="border: 3px solid {COLORS['accent']}; border-radius: 4px; cursor: pointer;">
                    <title>Clique para abrir localização no Google Maps</title>
                </image>
            </a>
            '''
        
        logger.warning(f"Mapa estático falhou: {response.status_code}, usando fallback")
        return _mapa_fallback_svg(latitude, longitude, width, height)
    except Exception as e:
        logger.error(f"Erro ao gerar mapa: {e}")
        return _mapa_fallback_svg(latitude, longitude, width, height)

def _mapa_fallback_svg(latitude: float, longitude: float, width: int = 400, height: int = 300) -> str:
    """Fallback: mapa com link direto ao Google Maps - design profissional"""
    mapa_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    return f'''
    <g onclick="window.open('{mapa_link}', '_blank')" style="cursor: pointer;">
        <rect x="0" y="0" width="{width}" height="{height}" 
              fill="{COLORS['light']}" stroke="{COLORS['accent']}" stroke-width="2" rx="4"/>
        <text x="{width/2}" y="{height/2 - 30}" font-size="18" font-weight="bold" 
              text-anchor="middle" fill="{COLORS['primary']}">
            📍 Localização
        </text>
        <text x="{width/2}" y="{height/2}" font-size="11" 
              text-anchor="middle" fill="{COLORS['text']}">
            Lat: {latitude:.6f}
        </text>
        <text x="{width/2}" y="{height/2 + 20}" font-size="11" 
              text-anchor="middle" fill="{COLORS['text']}">
            Lon: {longitude:.6f}
        </text>
        <text x="{width/2}" y="{height/2 + 60}" font-size="12" font-weight="bold"
              text-anchor="middle" fill="{COLORS['accent']}" style="cursor: pointer; text-decoration: underline;">
            Clique para abrir no Google Maps
        </text>
    </g>
    '''

def _download_imagem(url: str, max_width: int = 300, max_height: int = 300) -> str | None:
    """Baixa imagem e retorna como base64 para embedar no SVG"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        img = PILImage.open(BytesIO(response.content))
        
        img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
        
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True, quality=85)
        
        return f"data:image/png;base64,{_image_to_base64(buffer, 'PNG')}"
    except Exception as e:
        logger.error(f"Erro ao baixar/redimensionar imagem {url}: {e}")
        return None

def gerar_svg_relatorio(dados: dict) -> str:
    WIDTH = DIMENSIONS['page_width']
    HEIGHT = DIMENSIONS['page_height']
    MARGIN = DIMENSIONS['margin']
    CONTENT_WIDTH = WIDTH - (2 * MARGIN)
    
    svg_parts = []
    
    svg_parts.append(
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'style="width: 100%; height: auto; max-width: 100%; background: {COLORS["white"]};">'
    )
    
    if os.path.exists(FUNDO_PATH):
        try:
            fundo_base64 = _encode_image_base64(FUNDO_PATH)
            if fundo_base64:
                svg_parts.append(
                    f'<image x="0" y="0" width="{WIDTH}" height="{HEIGHT}" '
                    f'href="data:image/jpeg;base64,{fundo_base64}" opacity="0.90"/>'
                )
        except Exception as e:
            logger.warning(f"Erro ao adicionar fundo: {e}")
    
    svg_parts.append(f'''
    <defs>
        <linearGradient id="headerGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style="stop-color:{COLORS['secondary']};stop-opacity:1" />
            <stop offset="100%" style="stop-color:{COLORS['primary']};stop-opacity:1" />
        </linearGradient>
        <filter id="shadow">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
        </filter>
    </defs>
    <script type="text/javascript">
        <![CDATA[
        function gerarPDF() {{
            if (typeof html2pdf !== 'undefined') {{
                const element = document.querySelector('svg');
                const opt = {{
                    margin: 10,
                    filename: 'relatorio-confirmacao.pdf',
                    image: {{ type: 'png', quality: 0.98 }},
                    html2canvas: {{ scale: 2 }},
                    jsPDF: {{ orientation: 'portrait', unit: 'mm', format: 'a4' }}
                }};
                html2pdf().set(opt).from(element).save();
            }} else {{
                alert('Biblioteca PDF não carregada. Por favor, atualize a página.');
            }}
        }}
        ]]>
    </script>
    ''')
    
    y_pos = 0
    
    # ====== HEADER PROFISSIONAL ======
    svg_parts.append(
        f'<rect x="0" y="0" width="{WIDTH}" height="127" '
        f'fill="url(#headerGradient)" rx="0" filter="url(#shadow)"/>'
    )
    
    # Título principal
    svg_parts.append(
        f'<text x="{WIDTH/2 - 80}" y="45" font-size="32" font-weight="bold" '
        f'text-anchor="middle" fill="{COLORS["white"]}" '
        f'font-family="Arial, sans-serif" letter-spacing="1">RELATÓRIO DE CONFIRMAÇÃO DE SERVIÇO</text>'
    )
    
    # <CHANGE> Botão de imprimir no header
    svg_parts.append(
        f'<g onclick="gerarPDF()" style="cursor: pointer;" title="Clique para gerar PDF">'
        f'<rect x="{WIDTH - 90}" y="15" width="70" height="40" '
        f'fill="{COLORS["accent"]}" rx="4" opacity="0.9"/>'
        f'<text x="{WIDTH - 55}" y="42" font-size="14" font-weight="bold" '
        f'text-anchor="middle" fill="{COLORS["white"]}" '
        f'font-family="Arial, sans-serif">🖨️ PDF</text>'
        f'</g>'
    )
    
    # Protocolo
    protocol = dados.get('confirmacao', {}).get('tag_doc', 'N/A')
    svg_parts.append(
        f'<text x="{MARGIN}" y="90" font-size="12" '
        f'fill="{COLORS["white"]}" opacity="0.9" font-family="Arial, sans-serif">'
        f'Número do documento: {protocol}</text>'
    )
    
    # Data
    data_servico = dados.get('confirmacao', {}).get('data_servico', 'N/A')
    svg_parts.append(
        f'<text x="{WIDTH - MARGIN}" y="90" font-size="12" '
        f'fill="{COLORS["white"]}" opacity="0.9" text-anchor="end" font-family="Arial, sans-serif">'
        f'Data do serviço: {data_servico}</text>'
    )
    
    y_pos = 130
    
    # ====== INFORMAÇÕES GERAIS ======
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="32" '
        f'fill="{COLORS["secondary"]}" rx="4"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 15}" y="{y_pos + 23}" font-size="14" font-weight="bold" '
        f'fill="{COLORS["white"]}" font-family="Arial, sans-serif">INFORMAÇÕES GERAIS</text>'
    )
    
    y_pos += 50
    
    # Campo: Vistoriador
    vistoriador = dados.get('confirmacao', {}).get('nome_vistoriador', 'N/A')
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="32" '
        f'fill="{COLORS["light"]}" stroke="{COLORS["border"]}" stroke-width="1" rx="3"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 10}" y="{y_pos + 12}" font-size="10" '
        f'fill="{COLORS["text"]}" font-weight="bold" font-family="Arial, sans-serif">VISTORIADOR</text>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 10}" y="{y_pos + 25}" font-size="12" '
        f'fill="{COLORS["text"]}" font-family="Arial, sans-serif">{vistoriador}</text>'
    )
    
    y_pos += 40
    
    # Campo: Tipo de Serviço
    tipo_servico = dados.get('confirmacao', {}).get('tipo_servico', 'N/A')
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="32" '
        f'fill="{COLORS["light"]}" stroke="{COLORS["border"]}" stroke-width="1" rx="3"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 10}" y="{y_pos + 12}" font-size="10" '
        f'fill="{COLORS["text"]}" font-weight="bold" font-family="Arial, sans-serif">TIPO DE SERVIÇO</text>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 10}" y="{y_pos + 25}" font-size="12" '
        f'fill="{COLORS["text"]}" font-family="Arial, sans-serif">{tipo_servico}</text>'
    )
    
    y_pos += 50
    
    # ====== SEÇÃO: LOCALIZAÇÃO COM MAPA ======
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="32" '
        f'fill="{COLORS["secondary"]}" rx="4"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 15}" y="{y_pos + 23}" font-size="14" font-weight="bold" '
        f'fill="{COLORS["white"]}" font-family="Arial, sans-serif">LOCALIZAÇÃO</text>'
    )
    
    y_pos += 50
    
    latitude = dados.get('confirmacao', {}).get('latitude', 0)
    longitude = dados.get('confirmacao', {}).get('longitude', 0)
    
    # Mapa interativo com link
    if latitude and longitude:
        mapa_svg = _gerar_mapa_estatico_svg(latitude, longitude, 380, 300)
        
        svg_parts.append(
            f'<g transform="translate({MARGIN + (CONTENT_WIDTH - 380) / 2}, {y_pos})">'
            f'{mapa_svg}'
            f'</g>'
        )
        
        y_pos += 330
    
    # ====== SEÇÃO: ANTES E DEPOIS ======
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="32" '
        f'fill="{COLORS["secondary"]}" rx="4"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 15}" y="{y_pos + 23}" font-size="14" font-weight="bold" '
        f'fill="{COLORS["white"]}" font-family="Arial, sans-serif">REGISTRO FOTOGRÁFICO</text>'
    )
    
    y_pos += 50
    
    imgs_utilizadas = dados.get('imagens_utilizadas', {})
    img_antes_url = imgs_utilizadas.get('antes', {}).get('url')
    img_depois_url = imgs_utilizadas.get('depois', {}).get('url')
    
    img_antes_base64 = None
    img_depois_base64 = None
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            'antes': executor.submit(_download_imagem, img_antes_url, 250, 250) if img_antes_url else None,
            'depois': executor.submit(_download_imagem, img_depois_url, 250, 250) if img_depois_url else None,
        }
        
        for key, future in futures.items():
            if future:
                try:
                    resultado = future.result(timeout=20)
                    if key == 'antes':
                        img_antes_base64 = resultado
                    else:
                        img_depois_base64 = resultado
                except Exception as e:
                    logger.error(f"Erro ao processar imagem {key}: {e}")
    
    # Imagens lado a lado
    if img_antes_base64 or img_depois_base64:
        # Antes
        if img_antes_base64:
            svg_parts.append(
                f'<rect x="{MARGIN + 20}" y="{y_pos}" width="260" height="280" '
                f'fill="{COLORS["light"]}" stroke="{COLORS["accent"]}" stroke-width="2" rx="4"/>'
            )
            svg_parts.append(
                f'<image x="{MARGIN + 25}" y="{y_pos + 5}" width="250" height="250" '
                f'href="{img_antes_base64}" preserveAspectRatio="xMidYMid slice"/>'
            )
            svg_parts.append(
                f'<text x="{MARGIN + 155}" y="{y_pos + 270}" font-size="12" font-weight="bold" '
                f'text-anchor="middle" fill="{COLORS["primary"]}" font-family="Arial, sans-serif">ANTES</text>'
            )
        
        # Depois
        if img_depois_base64:
            svg_parts.append(
                f'<rect x="{MARGIN + CONTENT_WIDTH - 280}" y="{y_pos}" width="260" height="280" '
                f'fill="{COLORS["light"]}" stroke="{COLORS["accent"]}" stroke-width="2" rx="4"/>'
            )
            svg_parts.append(
                f'<image x="{MARGIN + CONTENT_WIDTH - 275}" y="{y_pos + 5}" width="250" height="250" '
                f'href="{img_depois_base64}" preserveAspectRatio="xMidYMid slice"/>'
            )
            svg_parts.append(
                f'<text x="{MARGIN + CONTENT_WIDTH - 150}" y="{y_pos + 270}" font-size="12" font-weight="bold" '
                f'text-anchor="middle" fill="{COLORS["primary"]}" font-family="Arial, sans-serif">DEPOIS</text>'
            )
        
        y_pos += 310
    
    # ====== OBSERVAÇÕES ======
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="32" '
        f'fill="{COLORS["secondary"]}" rx="4"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 15}" y="{y_pos + 23}" font-size="14" font-weight="bold" '
        f'fill="{COLORS["white"]}" font-family="Arial, sans-serif">OBSERVAÇÕES</text>'
    )
    
    y_pos += 50
    
    obs_antes = dados.get('obs_antes', 'Sem observações')
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="60" '
        f'fill="{COLORS["light"]}" stroke="{COLORS["border"]}" stroke-width="1" rx="3"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 10}" y="{y_pos + 12}" font-size="10" '
        f'fill="{COLORS["text"]}" font-weight="bold" font-family="Arial, sans-serif">ANTES</text>'
    )
    svg_parts.append(
        f'<foreignObject x="{MARGIN + 10}" y="{y_pos + 18}" width="{CONTENT_WIDTH - 20}" height="38">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="font-size: 11px; color: {COLORS["text"]}; '
        f'font-family: Arial, sans-serif; line-height: 1.3; overflow: hidden; text-overflow: ellipsis;">'
        f'{obs_antes}</div></foreignObject>'
    )
    
    y_pos += 70
    
    obs_depois = dados.get('obs_depois', 'Sem observações')
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="60" '
        f'fill="{COLORS["light"]}" stroke="{COLORS["border"]}" stroke-width="1" rx="3"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 10}" y="{y_pos + 12}" font-size="10" '
        f'fill="{COLORS["text"]}" font-weight="bold" font-family="Arial, sans-serif">DEPOIS</text>'
    )
    svg_parts.append(
        f'<foreignObject x="{MARGIN + 10}" y="{y_pos + 18}" width="{CONTENT_WIDTH - 20}" height="38">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="font-size: 11px; color: {COLORS["text"]}; '
        f'font-family: Arial, sans-serif; line-height: 1.3; overflow: hidden; text-overflow: ellipsis;">'
        f'{obs_depois}</div></foreignObject>'
    )
    
    y_pos += 70
    
    observacao = dados.get('observacao', 'Sem observações adicionais')
    svg_parts.append(
        f'<rect x="{MARGIN}" y="{y_pos}" width="{CONTENT_WIDTH}" height="70" '
        f'fill="{COLORS["light"]}" stroke="{COLORS["border"]}" stroke-width="1" rx="3"/>'
    )
    svg_parts.append(
        f'<text x="{MARGIN + 10}" y="{y_pos + 12}" font-size="10" '
        f'fill="{COLORS["text"]}" font-weight="bold" font-family="Arial, sans-serif">OBSERVAÇÃO GERAL</text>'
    )
    svg_parts.append(
        f'<foreignObject x="{MARGIN + 10}" y="{y_pos + 18}" width="{CONTENT_WIDTH - 20}" height="48">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="font-size: 11px; color: {COLORS["text"]}; '
        f'font-family: Arial, sans-serif; line-height: 1.3; overflow: hidden; text-overflow: ellipsis;">'
        f'{observacao}</div></foreignObject>'
    )
    
    # Fechar SVG
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)
   

def gerar_svg_relatorio_buffer(dados: dict) -> BytesIO:
    """Wrapper que retorna BytesIO em vez de string"""
    svg_content = gerar_svg_relatorio(dados)
    buffer = BytesIO()
    buffer.write(svg_content.encode('utf-8'))
    buffer.seek(0)
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
    confirmacao = db.query(ConfirmacaoServico).filter(
        ConfirmacaoServico.tag_doc == confirmacao_tag
    ).first()
    if not confirmacao:
        raise HTTPException(status_code=404, detail="Confirmação não encontrada.")
    
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