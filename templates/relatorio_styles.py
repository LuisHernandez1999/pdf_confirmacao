"""
Estilos e configurações visuais para os relatórios em PDF
"""
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from pathlib import Path
import os

# Caminhos para recursos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDO_PATH = Path(__file__).resolve().parents[1] / "imagens" / "planejamento_limpa.png"
LOGO_PATH = Path(__file__).resolve().parents[1] / "imagens" / "limpalogo.png"

COLORS = {
    'primary': '#059669',           # Verde escuro elegante
    'primary_light': "#1F9C29",     # Verde médio
    'secondary': '#4F7942',         # Verde natural
    'accent': '#88B04B',            # Verde suave
    'gold': '#D4AF37',              # Dourado premium
    'success': '#059669',           # Verde sucesso
    'warning': '#F59E0B',           # Laranja aviso
    'danger': '#DC2626',            # Vermelho erro
    'text': '#0F172A',              # Preto azulado
    'text_secondary': '#475569',    # Cinza médio
    'text_light': '#94A3B8',        # Cinza claro
    'light': '#F8FAFC',             # Branco suave
    'light_blue': '#F0F9FF',        # Azul claro
    'border': '#E2E8F0',            # Borda suave
    'white': '#FFFFFF',             # Branco puro
    'shadow': 'rgba(0, 0, 0, 0.08)', # Sombra sutil
}

def get_styles():
    """Retorna todos os estilos customizados para o PDF"""
    styles = getSampleStyleSheet()
    
    custom_styles = {
        'company_name': ParagraphStyle(
            'CompanyName',
            parent=styles['Normal'],
            fontSize=22,
            leading=26,
            textColor=HexColor(COLORS['primary']),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=3,
            letterSpacing=0.5
        ),
        
        'tagline': ParagraphStyle(
            'Tagline',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=0,
            letterSpacing=0.3
        ),
        
        'titulo_principal': ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=32,
            leading=38,
            textColor=HexColor(COLORS['primary']),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceBefore=0,
            spaceAfter=4,
            letterSpacing=1.2
        ),
        
        'subtitulo': ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=13,
            leading=16,
            textColor=HexColor(COLORS['text_secondary']),
            spaceAfter=2,
            alignment=TA_CENTER,
            fontName='Helvetica',
            letterSpacing=0.5
        ),
        
        'contador_numero': ParagraphStyle(
            'ContadorStyle',
            parent=styles['Normal'],
            fontSize=28,
            leading=32,
            textColor=HexColor(COLORS['primary']),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=3
        ),
        
        'contador_label': ParagraphStyle(
            'ContadorLabel',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=0,
            letterSpacing=0.8
        ),
        
        'data_grande': ParagraphStyle(
            'DataGrande',
            fontSize=16,
            leading=20,
            textColor=HexColor(COLORS['primary']),
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold',
            letterSpacing=0.5
        ),
        
        'hora_pequena': ParagraphStyle(
            'HoraPequena',
            fontSize=11,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_RIGHT,
            fontName='Helvetica',
            letterSpacing=0.3
        ),
        
        'periodo_text': ParagraphStyle(
            'PeriodoText',
            fontSize=10,
            leading=14,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_CENTER,
            fontName='Helvetica',
            letterSpacing=0.2
        ),
        
        'card_label': ParagraphStyle(
            'Label',
            fontSize=8,
            textColor=HexColor(COLORS['primary']),
            fontName='Helvetica-Bold',
            spaceAfter=2
        ),
        
        'card_valor': ParagraphStyle(
            'Valor',
            fontSize=10,
            textColor=HexColor('#2D3748'),
            fontName='Helvetica-Bold',
            spaceAfter=4
        ),
        
        'card_doc': ParagraphStyle(
            'Doc',
            fontSize=11,
            textColor=white,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ),
        
        'card_status': ParagraphStyle(
            'Status',
            fontSize=9,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ),
        
        'card_localizacao': ParagraphStyle(
            'Loc',
            fontSize=8,
            textColor=HexColor('#2D3748'),
            alignment=TA_CENTER
        ),
        
        'icon_style': ParagraphStyle(
            'Icon',
            fontSize=22,
            alignment=TA_CENTER,
            spaceAfter=3
        )
    }
    
    return custom_styles

def get_card_colors():

    return {
        'primaria': HexColor(COLORS['primary']),
        'secundaria': HexColor(COLORS['secondary']),
        'accent': HexColor(COLORS['accent']),
        'gold': HexColor(COLORS['gold']),
        'texto': HexColor('#2D3748'),
        'borda': HexColor('#CBD5E0'),
        'fundo_claro': HexColor('#f8f9fa'),
        'erro': HexColor('#e74c3c'),
        'contador_azul': HexColor('#EFF6FF'),
        'contador_verde': HexColor('#ECFDF5'),
        'contador_amarelo': HexColor('#E1E5E6'),
        'borda_azul': HexColor("#E1E5E6"),
        'borda_verde': HexColor("#E1E5E6"),
        'borda_amarela': HexColor('#E1E5E6'),
        'separador': HexColor(COLORS['border']),
    }
