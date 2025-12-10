"""Estilos e configurações visuais para os relatórios em PDF"""
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from pathlib import Path
import os

# Caminhos para recursos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNDO_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "assets"
    / "imagens"
    / "planejamento_limpa.png"
)

LOGO_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "assets"
    / "imagens"
    / "limpalogo.png"
)

# Paleta de cores profissional e minimalista
COLORS = {
    'primary': '#1E293B',           # Slate escuro - profissional
    'primary_light': '#334155',     # Slate médio
    'secondary': '#64748B',         # Slate claro
    'accent': '#059669',            # Verde corporativo
    'success': '#059669',           # Verde sucesso
    'warning': '#F59E0B',           # Laranja aviso
    'danger': '#DC2626',            # Vermelho erro
    'text': '#0F172A',              # Texto principal
    'text_secondary': '#64748B',    # Texto secundário
    'text_light': '#94A3B8',        # Texto claro
    'light': '#F8FAFC',             # Fundo claro
    'border': '#E2E8F0',            # Borda suave
    'white': '#FFFFFF',             # Branco puro
    'divider': '#CBD5E0',           # Divisor
}

def get_styles():
    """Retorna todos os estilos customizados para o PDF"""
    styles = getSampleStyleSheet()

    custom_styles = {
        'company_name': ParagraphStyle(
            'CompanyName',
            parent=styles['Normal'],
            fontSize=18,
            leading=22,
            textColor=HexColor(COLORS['primary']),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=2,
        ),

        'tagline': ParagraphStyle(
            'Tagline',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=0,
        ),

        'titulo_principal': ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=HexColor(COLORS['primary']),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceBefore=0,
            spaceAfter=2,
        ),

        'subtitulo': ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            textColor=HexColor(COLORS['text_secondary']),
            spaceAfter=0,
            alignment=TA_LEFT,
            fontName='Helvetica',
        ),

        'contador_numero': ParagraphStyle(
            'ContadorStyle',
            parent=styles['Normal'],
            fontSize=32,
            leading=36,
            textColor=HexColor(COLORS['primary']),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=2
        ),

        'contador_label': ParagraphStyle(
            'ContadorLabel',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=0,
        ),

        'data_grande': ParagraphStyle(
            'DataGrande',
            fontSize=11,
            leading=14,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_RIGHT,
            fontName='Helvetica',
        ),

        'hora_pequena': ParagraphStyle(
            'HoraPequena',
            fontSize=9,
            textColor=HexColor(COLORS['text_light']),
            alignment=TA_RIGHT,
            fontName='Helvetica',
        ),

        'periodo_text': ParagraphStyle(
            'PeriodoText',
            fontSize=10,
            leading=14,
            textColor=HexColor(COLORS['text_secondary']),
            alignment=TA_LEFT,
            fontName='Helvetica',
        ),

        'periodo_label': ParagraphStyle(
            'PeriodoLabel',
            fontSize=8,
            textColor=HexColor(COLORS['text_light']),
            alignment=TA_LEFT,
            fontName='Helvetica',
            spaceAfter=1,
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
        'texto': HexColor('#2D3748'),
        'borda': HexColor(COLORS['border']),
        'fundo_claro': HexColor(COLORS['light']),
        'erro': HexColor(COLORS['danger']),
        'contador_bg': HexColor(COLORS['white']),
        'contador_borda': HexColor(COLORS['border']),
        'separador': HexColor(COLORS['divider']),
    }
