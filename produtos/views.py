# produtos/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login 
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse # Importe HttpResponse
from django.views.decorators.http import require_POST # Importe require_POST para as views POST
from .models import CarouselImage, Pedido, Item, Produto, ProdutoImage, RegiaoFrete
from .forms import CustomUserCreationForm 
from decimal import Decimal  # coloque no topo do arquivo
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    categorias_esperadas = [
        'paineis_solares', 'inversores', 'baterias', 'kits_fotovoltaicos',
        'estruturas_montagem', 'acessorios', 'outros',
        'sistemas_backup', 'ferramentas_instalacao', # Novas categorias
    ]
    
    produtos_por_categoria = {cat_name: [] for cat_name in categorias_esperadas}
    
    # Busca produtos ATIVOS do seu banco de dados Django e pré-busca imagens
    all_products = Produto.objects.filter(is_active=True).prefetch_related('images')

    for produto_obj in all_products:
        produto_categoria_id = produto_obj.categoria_id.lower() if produto_obj.categoria_id else 'outros'
        
        if produto_categoria_id in categorias_esperadas:
            produtos_por_categoria[produto_categoria_id].append(produto_obj)
        else:
            if 'outros' in categorias_esperadas:
                produtos_por_categoria['outros'].append(produto_obj)

    categorias_para_template = [
        {'nome_url': cat, 'nome_exibicao': cat.replace('_', ' ').title()}
        for cat in categorias_esperadas
    ]

    carousel_images = []
    try:
        carousel_images = CarouselImage.objects.filter(is_active=True)
    except Exception as e:
        messages.error(request, f"Erro ao carregar imagens do carrossel: {e}")

    context = {
        'produtos_por_categoria': produtos_por_categoria,
        'carousel_images': carousel_images,
        'categorias_ativas': categorias_para_template,
    }
    return render(request, 'produtos/home.html', context)

# produtos/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Produto # Você não precisa de Categoria aqui se não a usa como model

def produtos_por_categoria(request, categoria_slug):
    categorias_validas = [
        'paineis_solares', 'inversores', 'baterias', 'kits_fotovoltaicos',
        'estruturas_montagem', 'acessorios', 'outros',
        'sistemas_backup', 'ferramentas_instalacao',
    ]

    if categoria_slug not in categorias_validas:
        messages.error(request, "Categoria inválida.")
        return redirect('produtos:home')

   
    produtos_da_categoria = Produto.objects.filter(categoria_id=categoria_slug, is_active=True).prefetch_related('images')

    # Para cada produto na lista, encontre a imagem a ser exibida e anexe-a ao objeto produto
    for produto in produtos_da_categoria:
        imagem_selecionada = produto.images.filter(is_main=True).first()
        if not imagem_selecionada:
            imagem_selecionada = produto.images.first()
        produto.imagem_do_card = imagem_selecionada

    nome_categoria_exibicao = categoria_slug.replace('_', ' ').title()

    categorias_para_template = [
        {'nome_url': cat, 'nome_exibicao': cat.replace('_', ' ').title()}
        for cat in categorias_validas
    ]

    context = {
        'categoria_atual': nome_categoria_exibicao, # Continua sendo uma STRING
        'produtos': produtos_da_categoria, # Agora cada produto tem 'imagem_do_card'
        'categorias_ativas': categorias_para_template,
    }
    return render(request, 'produtos/produtos_por_categoria.html', context)



def produto_detalhe(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id, is_active=True)

    imagem_para_exibir = produto.images.filter(is_main=True).first()
    if not imagem_para_exibir:
        imagem_para_exibir = produto.images.first()

    # ✅ Cálculo do valor com 20% a mais
    preco_com_desconto = produto.preco
    preco_original = preco_com_desconto * Decimal('1.2')

    context = {
        'produto': produto,
        'imagem_para_exibir': imagem_para_exibir,
        'preco_com_desconto': preco_com_desconto,
        'preco_original': preco_original,
    }

    return render(request, 'produtos/produto_detalhe.html', context)


def about(request):
    return render(request, 'produtos/about.html')


def contact(request):
    if request.method == "POST":

        pass
    return render(request, 'produtos/contact.html')

def termos_de_servico(request):
    return render(request, 'produtos/termos_de_servico.html', {})

def politica_privacidade(request):
    return render(request, 'produtos/politica_privacidade.html', {})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('produtos:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def adicionar_ao_carrinho(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    
    first_image_url = ''
    main_image = produto.images.filter(is_main=True).first()
    if main_image:
        first_image_url = main_image.image.url
    elif produto.images.first():
        first_image_url = produto.images.first().image.url

    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id)

    if produto_id_str in carrinho:
        carrinho[produto_id_str]['quantidade'] += 1
        carrinho[produto_id_str]['subtotal'] = carrinho[produto_id_str]['quantidade'] * carrinho[produto_id_str]['preco_unitario']
    else:
        carrinho[produto_id_str] = {
            'produto_id': produto.id,
            'nome': produto.name,
            'preco_unitario': float(produto.preco),
            'quantidade': 1,
            'imagem': first_image_url,
            'description': produto.description,
            'subtotal': float(produto.preco)
        }

    request.session['carrinho'] = carrinho
    request.session.modified = True
    messages.success(request, f'Produto "{produto.name}" adicionado ao carrinho.')

    return redirect('produtos:ver_carrinho')

def remover_do_carrinho(request, produto_id):
    carrinho = request.session.get('carrinho', {})
    produto_id_str = str(produto_id) # Garanta que a chave seja string

    if produto_id_str in carrinho:
        del carrinho[produto_id_str]
        request.session['carrinho'] = carrinho 
        request.session.modified = True 
        messages.success(request, "Item removido do carrinho.")
    else:
        messages.error(request, "Item não encontrado no carrinho.")
    return redirect('produtos:ver_carrinho')

def ver_carrinho(request):
    carrinho_atual = request.session.get('carrinho', {})
    itens_carrinho = []
    total_carrinho = 0

    novo_carrinho_sessao = {}

    for produto_id_str, dados_item in carrinho_atual.items():
        try:
            if 'quantidade' not in dados_item or 'preco_unitario' not in dados_item or 'nome' not in dados_item:
                messages.error(request, f"Erro: Dados incompletos para um item no carrinho (ID: {produto_id_str}). Será removido.")
                continue

            produto_db = get_object_or_404(Produto, pk=int(produto_id_str))
            quantidade = dados_item['quantidade']
            preco_unitario_item = dados_item['preco_unitario']
            subtotal_item = preco_unitario_item * quantidade
            total_carrinho += subtotal_item

            itens_carrinho.append({
                'produto': produto_db,
                'quantidade': quantidade,
                'preco_unitario': preco_unitario_item,
                'subtotal': subtotal_item,
                'imagem': dados_item.get('imagem', ''),
            })

            novo_carrinho_sessao[produto_id_str] = dados_item

        except Produto.DoesNotExist:
            messages.warning(request, f"O produto '{dados_item.get('nome', produto_id_str)}' não foi encontrado e foi removido do seu carrinho.")
            continue
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao processar um item do carrinho: {e}. Item ID: {produto_id_str}")
            continue

    request.session['carrinho'] = novo_carrinho_sessao
    request.session.modified = True

    # 🔽 Recupera o frete da sessão (mesmo que seja 0)
    valor_frete = request.session.get('valor_frete')
    try:
        frete_decimal = Decimal(str(valor_frete)) if valor_frete is not None else Decimal("0.00")
    except Exception as e:
        messages.warning(request, f"Erro ao recuperar o valor do frete: {e}")
        frete_decimal = Decimal("0.00")

    # Garante que o total do carrinho também é Decimal
    total_carrinho_decimal = Decimal(str(total_carrinho))
    total_com_frete = total_carrinho_decimal + frete_decimal

    context = {
        'itens_carrinho': itens_carrinho,
        'total_carrinho': total_carrinho,
        'frete': frete_decimal,
        'total_com_frete': total_com_frete,
    }

    return render(request, 'produtos/ver_carrinho.html', context)


def search(request):
    query = request.GET.get('q')
    produtos_encontrados = []

    if query:
        from django.db.models import Q 

        produtos_encontrados = Produto.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True 
        ).distinct().prefetch_related('images')


        if len(produtos_encontrados) > 0:    
            for p in produtos_encontrados:
                print(f"  - ID: {p.id}, Nome: {p.name}, Ativo: {p.is_active}, Descrição: {p.description}")
 
    return render(request, 'produtos/search_results.html', {'query': query, 'produtos': produtos_encontrados})

# Exemplo de prefixos de CEP liberados
#CEPS_ATENDIDOS = {
#    '060': {'cidade': 'Osasco', 'valor': 35.00, 'prazo': 2},
#    '061': {'cidade': 'Osasco', 'valor': 38.00, 'prazo': 3},
#    '063': {'cidade': 'Carapicuíba', 'valor': 40.00, 'prazo': 3},
#    '064': {'cidade': 'Barueri', 'valor': 42.00, 'prazo': 4},
#}

def calcular_frete(request, produto_id):
    from decimal import Decimal

    produto = get_object_or_404(Produto, id=produto_id)
    imagem_para_exibir = produto.images.filter(is_main=True).first()
    if not imagem_para_exibir:
        imagem_para_exibir = produto.images.first()

    # Preço original e com desconto
    preco_com_desconto = produto.preco
    preco_original = preco_com_desconto * Decimal('1.2')

    if request.method == 'POST':
        cep = request.POST.get('cep', '').replace('-', '').strip()

        if len(cep) < 3:
            return render(request, 'produtos/produto_detalhe.html', {
                'produto': produto,
                'imagem_para_exibir': imagem_para_exibir,
                'preco_original': preco_original,
                'preco_com_desconto': preco_com_desconto,
                'frete_indisponivel': True,
            })

        prefixo = cep[:3]
        regiao = RegiaoFrete.objects.filter(prefixo_cep=prefixo).first()

        if regiao:
            # ✅ Salva o valor do frete na sessão para ser usado no carrinho
            request.session['valor_frete'] = float(regiao.valor_frete)
            request.session.modified = True

            return render(request, 'produtos/produto_detalhe.html', {
                'produto': produto,
                'imagem_para_exibir': imagem_para_exibir,
                'preco_original': preco_original,
                'preco_com_desconto': preco_com_desconto,
                'frete_disponivel': True,
                'valor_frete': f"{regiao.valor_frete:.2f}",
                'prazo': regiao.prazo_entrega,
            })
        else:
            return render(request, 'produtos/produto_detalhe.html', {
                'produto': produto,
                'imagem_para_exibir': imagem_para_exibir,
                'preco_original': preco_original,
                'preco_com_desconto': preco_com_desconto,
                'frete_indisponivel': True,
            })

    return render(request, 'produtos/produto_detalhe.html', {
        'produto': produto,
        'imagem_para_exibir': imagem_para_exibir,
        'preco_original': preco_original,
        'preco_com_desconto': preco_com_desconto,
    })

@require_POST
def calcular_frete_carrinho(request):
    cep = request.POST.get('cep', '').replace('-', '').strip()
    if len(cep) < 3:
        messages.error(request, "CEP inválido para cálculo do frete.")
        return redirect('produtos:ver_carrinho')

    prefixo = cep[:3]
    regiao = RegiaoFrete.objects.filter(prefixo_cep=prefixo).first()

    if regiao:
        request.session['valor_frete'] = float(regiao.valor_frete)
        request.session.modified = True
        messages.success(request, f"Frete para o CEP {cep} calculado com sucesso.")
    else:
        messages.error(request, f"Não encontramos uma região com base no CEP informado ({cep}).")

    return redirect('produtos:ver_carrinho')
