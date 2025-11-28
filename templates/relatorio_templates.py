"""Templates HTML e SVG para relatórios"""

from datetime import datetime
from domain.templates.relatorio_styles import (
    COLORS, CARD_WIDTH, CARD_HEIGHT, CARD_IMAGE_HEIGHT,
    PAGE_WIDTH, HEADER_HEIGHT, FOOTER_HEIGHT,
    get_html_styles, get_svg_defs, get_svg_script
)


def gerar_svg_header(logo_base64: str | None, total: int) -> str:
    """Gera o cabeçalho SVG"""
    header = f'<rect x="0" y="0" width="{PAGE_WIDTH}" height="{HEADER_HEIGHT}" fill="rgba(255,255,255,0.95)" filter="url(#sombra)"/>'
    
    if logo_base64:
        header += f'''
            <g>
                <image href="data:image/png;base64,{logo_base64}" x="50" y="30" width="100" height="100" preserveAspectRatio="xMidYMid meet"/>
                <text x="100" y="155" font-size="18" font-weight="bold" text-anchor="middle" fill="{COLORS['primary']}">Consórcio LimpaGyn</text>
            </g>
        '''
    
    header += f'''
        <text x="{PAGE_WIDTH/2}" y="70" font-size="42" font-weight="bold" text-anchor="middle" fill="{COLORS['primary']}">RELATÓRIO CONFIRMAÇÃO SERVIÇO</text>
        <text x="{PAGE_WIDTH/2}" y="115" font-size="22" text-anchor="middle" fill="{COLORS['primary']}" opacity="0.95">Confirmações neste Relatório: {total}</text>
        <text x="{PAGE_WIDTH/2}" y="150" font-size="16" text-anchor="middle" fill="{COLORS['primary']}" opacity="0.85">Gerado em: {datetime.now().strftime("%d/%m/%Y")}</text>
    '''
    
    return header


def gerar_svg_footer(page_height: int) -> str:
    """Gera o rodapé SVG"""
    footer_y = page_height - FOOTER_HEIGHT
    return f'''
        <rect x="0" y="{footer_y}" width="{PAGE_WIDTH}" height="{FOOTER_HEIGHT}" fill="rgba(255,255,255,0.95)" filter="url(#sombra)"/>
        <text x="{PAGE_WIDTH/2}" y="{footer_y + 35}" font-size="20" font-weight="bold" text-anchor="middle" fill="{COLORS['primary']}">Consórcio LimpaGyn</text>
        <text x="{PAGE_WIDTH/2}" y="{footer_y + 60}" font-size="14" text-anchor="middle" fill="{COLORS['secondary']}">Relatório gerado automaticamente</text>
    '''


def gerar_card_svg(confirmacao, card_id: str, x: int, y: int, imagens_b64: list[str]) -> str:
    """Gera um card SVG com informações da confirmação"""
    total_imagens = len(imagens_b64)
    
    linhas = [f'<g transform="translate({x},{y})">']
    linhas.append(f'<rect x="0" y="0" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" fill="white" stroke="{COLORS["border"]}" stroke-width="2" rx="12" filter="url(#sombra)"/>')

    # === IMAGENS COM CLIPPING ===
    if imagens_b64:
        linhas.append(f'<clipPath id="clip_{card_id}"><rect x="10" y="10" width="{CARD_WIDTH-20}" height="{CARD_IMAGE_HEIGHT}" rx="10"/></clipPath>')
        linhas.append(f'<g clip-path="url(#clip_{card_id})"><g id="slides_{card_id}">')
        for i, img64 in enumerate(imagens_b64):
            linhas.append(f'<image x="{10 + i * (CARD_WIDTH-20)}" y="10" width="{CARD_WIDTH-20}" height="{CARD_IMAGE_HEIGHT}" href="{img64}" preserveAspectRatio="xMidYMid slice"/>')
        linhas.append('</g></g>')

        # BOTÕES DE NAVEGAÇÃO
        if total_imagens > 1:
            linhas.append(f'''
                <g onclick="navegar('{card_id}', -1)" style="cursor:pointer"><circle cx="35" cy="{CARD_IMAGE_HEIGHT/2 + 10}" r="22" fill="{COLORS["primary"]}" opacity="0.8"/><text x="35" y="{CARD_IMAGE_HEIGHT/2 + 18}" font-size="28" fill="white" text-anchor="middle">‹</text></g>
                <g onclick="navegar('{card_id}', 1)" style="cursor:pointer"><circle cx="{CARD_WIDTH-35}" cy="{CARD_IMAGE_HEIGHT/2 + 10}" r="22" fill="{COLORS["primary"]}" opacity="0.8"/><text x="{CARD_WIDTH-35}" y="{CARD_IMAGE_HEIGHT/2 + 18}" font-size="28" fill="white" text-anchor="middle">›</text></g>
                <text id="contador_{card_id}" x="{CARD_WIDTH/2}" y="{CARD_IMAGE_HEIGHT + 35}" font-size="13" text-anchor="middle" fill="{COLORS["text"]}">1 / {total_imagens}</text>
            ''')
    else:
        linhas.append(f'''
            <rect x="10" y="10" width="{CARD_WIDTH-20}" height="{CARD_IMAGE_HEIGHT}" fill="{COLORS["light"]}" rx="10"/>
            <text x="{CARD_WIDTH/2}" y="{CARD_IMAGE_HEIGHT/2 + 10}" font-size="18" font-weight="bold" text-anchor="middle" fill="#e74c3c">SEM IMAGENS</text>
        ''')

    # === INFORMAÇÕES DO CARD ===
    y_info = 250
    tag_doc = confirmacao.tag_doc or "NULO"
    linhas.append(f'<rect x="10" y="{y_info}" width="{CARD_WIDTH-20}" height="34" fill="{COLORS["primary"]}" rx="8"/>')
    linhas.append(f'<text x="{CARD_WIDTH/2}" y="{y_info+22}" font-size="13" font-weight="bold" text-anchor="middle" fill="white">DOC: {tag_doc}</text>')

    y_info += 50

    dados = [
        ("Vistoriador", confirmacao.nome_vistoriador or "NULO"),
        ("Serviço", confirmacao.tipo_servico or "NULO"),
        ("Data", confirmacao.data_servico.strftime("%d/%m/%Y") if confirmacao.data_servico else "NULO"),
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
                <rect x="15" y="{y_info+10}" width="{CARD_WIDTH-30}" height="40" fill="{COLORS["light"]}" stroke="{COLORS["accent"]}" stroke-width="2" rx="8"/>
                <text x="{CARD_WIDTH/2}" y="{y_info+33}" font-size="11" text-anchor="middle" fill="{COLORS["text"]}">📍 {confirmacao.latitude:.6f}, {confirmacao.longitude:.6f}</text>
            </a>
        ''')
    else:
        linhas.append(f'<text x="15" y="{y_info}" font-size="13" fill="#e74c3c" font-weight="bold">Localização: NULO</text>')

    linhas.append('</g>')
    return "\n".join(linhas)


def gerar_html_header(logo_base64: str | None, fundo_base64: str | None, total: int) -> str:
    """Gera o cabeçalho HTML"""
    background_img = f'<img src="data:image/jpeg;base64,{fundo_base64}" alt="" class="background">' if fundo_base64 else ''
    logo_section = f'<div class="header-logo-section"><img src="data:image/png;base64,{logo_base64}" alt="LimpGyn Logo" class="header-logo"><div class="company-name">Consórcio LimpaGyn</div></div>' if logo_base64 else ''
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Completo</title>
    <style>
        {get_html_styles()}
    </style>
</head>
<body>
    {background_img}
    <div class="container">
        <div class="header">
            {logo_section}
            <div class="header-content">
                <h1>RELATÓRIO COMPLETO</h1>
                <p>Confirmações neste Relatório: {total}</p>
                <p style="font-size: 0.9em; opacity: 0.8;">Gerado em: {datetime.now().strftime("%d/%m/%Y")}</p>
            </div>
        </div>
    '''


def gerar_html_footer() -> str:
    """Gera o rodapé HTML"""
    return '''
    <div class="footer">
        <h3>Consórcio LimpaGyn</h3>
        <p>Relatório gerado automaticamente</p>
    </div>
    </div>
    </body>
    </html>
    '''


def gerar_html_pagination_script(total_paginas: int) -> str:
    """Gera o JavaScript para paginação"""
    return f'''
    <script>
        let paginaAtual = 0;
        const totalPaginas = {total_paginas};
        
        function mudarPagina(direcao) {{
            paginaAtual += direcao;
            
            if (paginaAtual < 0) paginaAtual = 0;
            if (paginaAtual >= totalPaginas) paginaAtual = totalPaginas - 1;
            
            document.querySelectorAll('.pagina').forEach((p, i) => {{
                p.classList.toggle('ativa', i === paginaAtual);
            }});
            
            document.getElementById('page-info').textContent = 
                'Página ' + (paginaAtual + 1) + ' de ' + totalPaginas;
            
            document.getElementById('btn-anterior').disabled = paginaAtual === 0;
            document.getElementById('btn-proximo').disabled = paginaAtual === totalPaginas - 1;
        }}
        
        // Inicializar paginação
        mudarPagina(0);
    </script>
    '''
