"""Estilos e configurações visuais para relatórios"""

COLORS = {
    'primary': '#2D5016',
    'secondary': '#4A8C5E',
    'accent': '#6BBF59',
    'text': '#2D3748',
    'light': '#EDF2F7',
    'border': '#CBD5E0',
    'white': '#FFFFFF',
}

# Dimensões dos cards
CARD_WIDTH = 340
CARD_HEIGHT = 510
CARD_IMAGE_HEIGHT = 200

# Dimensões da página
PAGE_WIDTH = 2000
HEADER_HEIGHT = 240
FOOTER_HEIGHT = 80

# Espaçamento
ESPACO_X = 0
ESPACO_Y = 60

# Cards por página (para paginação)
CARDS_POR_PAGINA = 6

def get_html_styles() -> str:
    """Retorna os estilos CSS para o HTML"""
    return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f5f5f5;
            padding: 0;
            margin: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            object-fit: cover;
        }
        .container { 
            position: relative;
            z-index: 1;
            max-width: 1400px; 
            margin: 0 auto;
            padding: 20px;
            flex: 1;
        }
        .header {
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
        }
        .header-logo-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        .header-logo {
            width: 120px;
            height: 120px;
            object-fit: contain;
        }
        .company-name {
            color: #2D5016;
            font-size: 1.3em;
            font-weight: bold;
        }
        .header-content {
            flex: 1;
            min-width: 300px;
        }
        .header h1 { color: #2D5016; font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #4A8C5E; font-size: 1.2em; margin: 5px 0; }
        
        .footer {
            background: rgba(255, 255, 255, 0.98);
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
            text-align: center;
            margin-top: 40px;
            backdrop-filter: blur(10px);
            position: relative;
            z-index: 1;
        }
        .footer h3 {
            color: #2D5016;
            font-size: 1.5em;
            margin-bottom: 8px;
        }
        .footer p {
            color: #4A8C5E;
            font-size: 1em;
        }
        .controls {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
            backdrop-filter: blur(10px);
        }
        .pagination {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .btn-nav {
            background: #2D5016;
            color: white;
        }
        .btn-nav:hover:not(:disabled) {
            background: #3a6b1d;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(45, 80, 22, 0.3);
        }
        .btn-nav:disabled {
            background: #CBD5E0;
            cursor: not-allowed;
            opacity: 0.6;
        }
        .page-info {
            font-size: 16px;
            font-weight: 600;
            color: #2D5016;
            min-width: 120px;
            text-align: center;
        }
        .cards-grid {
            display: grid;
            gap: 30px;
            justify-content: center;
        }
        .pagina {
            display: none;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 30px;
            justify-content: center;
        }
        .pagina.ativa {
            display: grid;
        }
        .svg-container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .svg-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8em; }
            .header p { font-size: 1em; }
            .header-logo { width: 80px; height: 80px; }
            .company-name { font-size: 1.1em; }
            .controls { flex-direction: column; }
            .cards-grid { gap: 20px; }
        }
    """

def get_svg_defs() -> str:
    """Retorna as definições SVG (filtros, gradientes, etc)"""
    return """
    <defs>
        <filter id="sombra">
            <feDropShadow dx="0" dy="6" stdDeviation="8" flood-opacity="0.25"/>
        </filter>
    </defs>
    """

def get_svg_script() -> str:
    """Retorna o JavaScript para navegação no carrossel SVG"""
    return """
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
    """
