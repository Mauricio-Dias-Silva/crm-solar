# utils.py - APENAS o trecho da função extract_placeholders

import re
from bs4 import BeautifulSoup

def extract_placeholders(html_code):
    all_found_placeholders = set()

    # 1. Placeholders de texto direto [LP_HERO_TITULO]
    all_found_placeholders.update(re.findall(r'\[(LP_[A-Z0-9_]+)\]', html_code))

    # 2. Placeholders em atributos src (para <img>)
    # Ex: src="[LP_IMAGEM_BENEFIT_1_URL]"
    all_found_placeholders.update(re.findall(r'src="\[(LP_IMAGEM_[A-Z0-9_]+_URL)\]"', html_code))

    # 3. Placeholders em atributos alt (para <img>)
    # Ex: alt="[LP_IMAGEM_BENEFIT_1_ALT]"
    all_found_placeholders.update(re.findall(r'alt="\[(LP_IMAGEM_[A-Z0-9_]+_ALT)\]"', html_code))

    # 4. Placeholders em background-image no CSS (url('[LP_HERO_BG_IMAGEM_URL]'))
    # Considera aspas simples ou duplas, e também sem aspas
    all_found_placeholders.update(re.findall(r"url\(['\"]?\[(LP_[A-Z0-9_]+_IMAGEM_URL)\]['\"]?\)", html_code))
    
    # Adicionar placeholders para fotos de depoimento se a IA os gera (DEP_1_PHOTO, etc.)
    all_found_placeholders.update(re.findall(r'src="\[(LP_IMAGEM_DEP_[0-9]+_PHOTO_URL)\]"', html_code))
    all_found_placeholders.update(re.findall(r'alt="\[(LP_IMAGEM_DEP_[0-9]+_PHOTO_ALT)\]"', html_code))

    return sorted(list(all_found_placeholders))


# core/utils.py - Apenas a função inject_content_into_html

import re
from bs4 import BeautifulSoup

# ... (Sua função extract_placeholders aqui, não alterada) ...

def inject_content_into_html(base_html, content_data):
    # Primeiramente, faça substituições de string no HTML bruto para garantir
    # que TODOS os placeholders (incluindo os em CSS, JS ou texto puro) sejam preenchidos.
    processed_html_str = base_html 

    for key, value in content_data.items():
        # Converte o valor para string para garantir que a substituição funcione
        value_str = str(value) 

        # 1. Substituir placeholders em URLs de CSS (background-image: url('[KEY]'))
        # Tenta pegar aspas simples, aspas duplas, e sem aspas
        processed_html_str = processed_html_str.replace(f"url('[{key}]')", f"url('{value_str}')")
        processed_html_str = processed_html_str.replace(f'url("[{key}]")', f'url("{value_str}")')
        processed_html_str = processed_html_str.replace(f'url([L{key}])', f'url({value_str})') # Para o caso exótico sem aspas

        # 2. Substituir placeholders em atributos HTML (src="", alt="", href="")
        # Usamos uma regex mais flexível para capturar o atributo e substituir o placeholder dentro dele
        # Isso cobre imagens (src, alt), links (href) e outros atributos que possam usar placeholders.
        # Ex: src="[LP_IMAGEM_URL]", alt="[LP_IMAGEM_ALT]", href="[LP_LINK_URL]"
        processed_html_str = re.sub(
            r'(\w+)=["\']?\[{}\]["\']?'.format(re.escape(key)), # Procura atributo="[PLACEHOLDER]" ou atributo=[PLACEHOLDER]
            r'\1="{}"'.format(value_str), # Substitui por atributo="VALOR"
            processed_html_str
        )
        # O re.escape(key) é crucial para garantir que caracteres especiais no nome do placeholder sejam tratados.


        # 3. Substituir placeholders de texto direto no HTML (seja dentro de tags <p>, <h1>, <span> etc.)
        # Esta é uma substituição genérica para qualquer [PLACEHOLDER] que não esteja em um atributo
        # que já foi pego pelas regras acima.
        # Fazemos isso por último para não interferir nas substituições de atributos/URLs.
        processed_html_str = processed_html_str.replace(f'[{key}]', value_str)


    # Depois de todas as substituições de string, use Beautiful Soup para manipular a estrutura HTML
    # e adicionar a tag <base>.
    soup = BeautifulSoup(processed_html_str, 'html.parser')

    # Adicionar a tag <base> para URLs absolutas no iframe
    head = soup.find('head')
    if head:
        # Verifica se já existe uma tag base para não duplicar
        if not head.find('base'):
            base_tag = soup.new_tag("base")
            base_tag['href'] = "/" # Isso faz com que todas as URLs relativas (como /media/...)
                                    # sejam resolvidas a partir da raiz do domínio.
            head.insert(0, base_tag) # Insere no início do <head>
    
    return str(soup)

# ... (Sua função add_editable_attributes aqui, se ainda estiver usando, não alterada) ...