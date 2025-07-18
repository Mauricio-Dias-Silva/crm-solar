from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Permite acessar um item de um dicionário por chave no template.
    Ex: {{ my_dict|get_item:my_key }}
    """
    return dictionary.get(key)

@register.filter(name='replace')
def replace_string(value, arg):
    """
    Substitui todas as ocorrências de uma substring por outra.
    Uso: {{ value|replace:"'buscar','substituir'" }}
    """
    try:
        old_char, new_char = arg.split(',')
        return value.replace(old_char, new_char)
    except ValueError:
        # Lida com casos em que o argumento não está no formato esperado
        return value # Retorna o valor original se o arg for inválido