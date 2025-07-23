# core/utils.py
import re
from bs4 import BeautifulSoup # Importe BeautifulSoup

def extract_placeholders(html_code):
    """
    Extrai todos os placeholders no formato [LP_SECAO_CAMPO] do código HTML.
    Retorna um set de strings dos placeholders encontrados.
    """
    placeholders = re.findall(r'\[(LP_[A-Z0-9_]+)\]', html_code)
    return set(placeholders)

def add_editable_attributes(html_code):
    """
    Adiciona os atributos data-gaya-editable e data-gaya-placeholder aos elementos HTML
    que contêm placeholders. Isso é feito no lado do servidor com BeautifulSoup.
    """
    soup = BeautifulSoup(html_code, 'html.parser')
    
    # Padrões de tags que podem conter texto ou URLs editáveis
    elements_with_text_placeholders = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'strong', 'em', 'li', 'blockquote', 'cite', 'button', 'a']
    elements_with_url_placeholders = ['a', 'img'] # Links e imagens
    
    all_placeholders = extract_placeholders(html_code) # Reusa a função para pegar todos os placeholders
    
    for placeholder in all_placeholders:
        # Tenta encontrar o placeholder como TEXTO dentro de elementos
        for tag_name in elements_with_text_placeholders:
            # Encontra tags que contêm o placeholder como texto exato [LP_NOME]
            for element in soup.find_all(tag_name, string=re.compile(r'\[{}\]'.format(re.escape(placeholder)))):
                # Adiciona os atributos de edição visual
                element['data-gaya-editable'] = 'true'
                element['data-gaya-placeholder'] = placeholder
        
        # Tenta encontrar o placeholder como URL em atributos src/href
        for tag_name in elements_with_url_placeholders:
            # Busca em 'src' (para img)
            for element in soup.find_all(tag_name, src=re.compile(r'\[{}\]'.format(re.escape(placeholder)))):
                # Adiciona os atributos de edição visual
                element['data-gaya-editable'] = 'true'
                element['data-gaya-placeholder'] = placeholder
            # Busca em 'href' (para a)
            for element in soup.find_all(tag_name, href=re.compile(r'\[{}\]'.format(re.escape(placeholder)))):
                # Adiciona os atributos de edição visual
                element['data-gaya-editable'] = 'true'
                element['data-gaya-placeholder'] = placeholder

    return str(soup) # Retorna o HTML modificado como string


def inject_content_into_html(base_html_code, content_data):
    """
    Substitui TODOS os placeholders no HTML base pelos dados fornecidos.
    Se um placeholder não tem valor em content_data, ele é substituído por uma string vazia.
    """
    final_html = base_html_code
    
    all_placeholders_in_code = extract_placeholders(base_html_code) 

    for placeholder in all_placeholders_in_code:
        value_from_data = content_data.get(placeholder, "") 
        str_value = str(value_from_data) if value_from_data is not None else "" 

        # Esta regex substitui [PLACEHOLDER] mesmo dentro de aspas ou parênteses,
        # para garantir que URLs e outros atributos sejam corretamente limpos se vazios.
        # Ex: src="[LP_IMAGEM_URL]" vira src=""
        # Ex: url('[LP_BG_IMAGEM_URL]') vira url('')
        final_html = re.sub(
            r'(\["\']?|\()?' + re.escape(f'[{placeholder}]') + r'(\[\"\'\]?|\))?', 
            r'\1' + str_value + r'\2', 
            final_html
        )
            
    return final_html