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

# Importe TODOS os modelos que você usa
from .models import CarouselImage, Pedido, Item, Produto, ProdutoImage
# Certifique-se de que CustomUserCreationForm está definido em produtos/forms.py
from .forms import CustomUserCreationForm 

import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# --- FUNÇÕES DE RENDERIZAÇÃO DE PÁGINAS BÁSICAS ---

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

def produtos_por_categoria(request, categoria_slug):
    categorias_validas = [
        'paineis_solares', 'inversores', 'baterias', 'kits_fotovoltaicos',
        'estruturas_montagem', 'acessorios', 'outros',
        'sistemas_backup', 'ferramentas_instalacao', # Novas categorias
    ]

    if categoria_slug not in categorias_validas:
        messages.error(request, "Categoria inválida.")
        return redirect('produtos:home')

    produtos_da_categoria = Produto.objects.filter(categoria_id=categoria_slug, is_active=True).prefetch_related('images')

    nome_categoria_exibicao = categoria_slug.replace('_', ' ').title()

    categorias_para_template = [
        {'nome_url': cat, 'nome_exibicao': cat.replace('_', ' ').title()}
        for cat in categorias_validas
    ]

    context = {
        'categoria_atual': nome_categoria_exibicao,
        'produtos': produtos_da_categoria,
        'categorias_ativas': categorias_para_template,
    }
    return render(request, 'produtos/produtos_por_categoria.html', context)

def produto_detalhe(request, produto_id): # Renomeado de 'produto_detalhes' para consistência
    produto = get_object_or_404(Produto.objects.prefetch_related('images'), pk=produto_id)
    return render(request, 'produtos/produto_detalhe.html', {'produto': produto})

def about(request):
    return render(request, 'produtos/about.html')

def contact(request):
    if request.method == "POST":
        # Lógica para processar o formulário de contato (a ser implementada)
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

# --- FUNÇÕES DE CARRINHO ---

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
            # Validação extra para garantir que os dados necessários estão no item
            # e que o produto ainda existe no DB antes de processar
            if 'quantidade' not in dados_item or 'preco_unitario' not in dados_item or 'nome' not in dados_item:
                messages.error(request, f"Erro: Dados incompletos para um item no carrinho (ID: {produto_id_str}). Será removido.")
                continue # Pula este item problemático

            produto_db = get_object_or_404(Produto, pk=int(produto_id_str)) # Busque o objeto Produto real
            
            quantidade = dados_item['quantidade']
            preco_unitario_item = dados_item['preco_unitario'] 
            subtotal_item = preco_unitario_item * quantidade 
            total_carrinho += subtotal_item
            
            itens_carrinho.append({
                'produto': produto_db, # Passe o objeto Produto real para o template
                'quantidade': quantidade,
                'preco_unitario': preco_unitario_item,
                'subtotal': subtotal_item,
                'imagem': dados_item.get('imagem', ''), # Use a URL de imagem salva na sessão
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

    context = {
        'itens_carrinho': itens_carrinho,
        'total_carrinho': total_carrinho,
    }
    return render(request, 'produtos/ver_carrinho.html', context)

# produtos/views.py

# ... (seus imports e outras views) ...

# produtos/views.py

# ... (seus imports, incluindo 'Q' de django.db.models se ainda não o fez) ...

def search(request):
    query = request.GET.get('q')
    produtos_encontrados = []

    print(f"\n--- INÍCIO: search view ---") # DEBUG
    print(f"DEBUG: Termo de busca (query) recebido: '{query}'") # DEBUG

    if query:
        from django.db.models import Q # Garanta que Q está importado aqui

        # Busca produtos no seu próprio banco de dados Django
        produtos_encontrados = Produto.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True # Garante que apenas produtos ativos apareçam nos resultados
        ).distinct().prefetch_related('images')

        print(f"DEBUG: Consulta SQL gerada: {produtos_encontrados.query}") # DEBUG: Mostra a consulta SQL
        print(f"DEBUG: Número de produtos encontrados: {len(produtos_encontrados)}") # DEBUG

        if len(produtos_encontrados) > 0:
            print("DEBUG: Produtos encontrados:")
            for p in produtos_encontrados:
                print(f"  - ID: {p.id}, Nome: {p.name}, Ativo: {p.is_active}, Descrição: {p.description}") # DEBUG
        else:
            print("DEBUG: Nenhum produto encontrado para a busca.") # DEBUG

    print(f"--- FIM: search view ---") # DEBUG
    return render(request, 'produtos/search_results.html', {'query': query, 'produtos': produtos_encontrados})

# ... (restante das suas views) ...

