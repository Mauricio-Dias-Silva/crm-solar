# Em core/utils.py (ou um novo arquivo like core/placeholder_labels.py)
PLACEHOLDER_LABELS = {
    'LP_HERO_TITULO': 'Título Principal (Hero)',
    'LP_HERO_SUBTITULO': 'Subtítulo da Seção Principal',
    'LP_HERO_CTA_TEXTO': 'Texto do Botão de Ação (Hero)',
    'LP_HERO_CTA_LINK': 'URL do Botão de Ação (Hero)',
    'LP_IMAGEM_SECAO_GALERIA_1_URL': 'URL da Imagem da Galeria 1',
    'LP_IMAGEM_SECAO_GALERIA_1_ALT': 'Texto Alt da Imagem da Galeria 1',
    'LP_RODAPE_COPYRIGHT': 'Texto de Copyright do Rodapé',
    # Adicione todos os seus placeholders aqui
}

def get_friendly_label(placeholder_key):
    return PLACEHOLDER_LABELS.get(placeholder_key, placeholder_key.replace('LP_', '').replace('_', ' ').title())

# Em edit_site_view, você passaria isso para o template
# E no template, usaria {{ placeholder|get_friendly_label }}