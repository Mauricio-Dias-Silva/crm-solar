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
from .forms import CustomUserCreationForm, ProdutoForm, ProdutoImageForm
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


# seu_app/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import user_passes_test # Para proteger a view

from .models import Produto, ProdutoImage
from .forms import ProdutoForm, ProdutoImageForm

# Função auxiliar para verificar permissões (ex: staff ou superuser)
def is_manager_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)
    # Alternativamente, use user.has_perm('produtos.add_produto') para permissão específica

@user_passes_test(is_manager_or_admin, login_url='login')
def adicionar_produto(request):
    ProdutoImageFormSet = inlineformset_factory(
        Produto, ProdutoImage, form=ProdutoImageForm, extra=1, can_delete=True, max_num=5
    )

    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        formset = ProdutoImageFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            produto = form.save() # Salva o produto para obter um ID
            formset.instance = produto # Associa as imagens ao produto salvo
            formset.save()
            return redirect('produtos:home') # Redirecionar após o sucesso
        else:
            # Se houver erros, os formulários serão renderizados novamente com feedback
            pass
    else:
        form = ProdutoForm()
        formset = ProdutoImageFormSet()

    context = {
        'form': form,
        'formset': formset,
        'is_adding': True, # Flag para personalizar o template se for "Adicionar"
        'produto': None # Nenhum produto existente ao adicionar
    }
    return render(request, 'produtos/modificar_produto.html', context) # Reutiliza o template


# crmsolar/produtos/views.py

# ... (all your existing imports, e.g., render, get_object_or_404, redirect,
#      inlineformset_factory, user_passes_test, Produto, ProdutoImage,
#      ProdutoForm, ProdutoImageForm) ...

# Your permission function (assuming it's defined correctly above)
def is_manager_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_manager_or_admin, login_url='account_login')
def modificar_produto(request, produto_id):
    # 1. Get the existing product object
    produto = get_object_or_404(Produto, pk=produto_id)

    # 2. Define the FormSet for images (this is outside the if/else as it's always needed)
    ProdutoImageFormSet = inlineformset_factory(
        Produto, ProdutoImage, form=ProdutoImageForm, extra=1, can_delete=True, max_num=5
    )

    # 3. Handle POST vs GET requests
    if request.method == 'POST':
        # If the form was submitted (POST request)
        form = ProdutoForm(request.POST, instance=produto)
        formset = ProdutoImageFormSet(request.POST, request.FILES, instance=produto)

        if form.is_valid() and formset.is_valid():
            # If both forms are valid, save the data
            form.save()
            formset.save()
            # Redirect to the product list after successful modification
            return redirect('produtos:lista_produtos')
        # ELSE (if validation fails for POST):
        # The 'form' and 'formset' variables are already defined above (with errors attached).
        # The code will simply proceed to render the template with these forms.

    else: # This block handles GET requests (when the page is first loaded)
        # For GET requests, initialize the forms with the existing product's data
        form = ProdutoForm(instance=produto)
        formset = ProdutoImageFormSet(instance=produto)

    # 4. Prepare the context dictionary (THIS IS LINE 497 IN YOUR TRACEBACK)
    #    'form' and 'formset' are GUARANTEED to be defined here because:
    #    - If it was a POST request, they were defined in the 'if request.method == "POST":' block.
    #    - If it was a GET request, they were defined in the 'else:' block.
    context = {
        'form': form,
        'formset': formset,
        'produto': produto,
        'is_adding': False # Indicate this is a modification page
    }

    # 5. Render the template
    return render(request, 'produtos/modificar_produto.html', context)

# ... (rest of your views and other code) ...


def is_manager_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# View para listar produtos (sua nova "central de gerenciamento")
def lista_produtos(request):
    produtos = Produto.objects.all().order_by('name') # Ordena por nome
    context = {
        'produtos': produtos
    }
    return render(request, 'produtos/lista_produtos.html', context)



# crmsolar/produtos/views.py

# (Certifique-se de que todas as suas importações estão no topo do arquivo)
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import user_passes_test

from .models import Produto, ProdutoImage
from .forms import ProdutoForm, ProdutoImageForm

# Sua função de verificação de permissão (assumindo que está correta e definida acima)
def is_manager_or_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_manager_or_admin, login_url='account_login')
def modificar_produto(request, produto_id):
    # 1. Obtenha o objeto Produto existente
    # Se o produto não for encontrado, get_object_or_404 levanta um 404
    produto = get_object_or_404(Produto, pk=produto_id)

    # 2. Defina o FormSet para as imagens (isso fica fora do if/else, pois sempre será necessário)
    ProdutoImageFormSet = inlineformset_factory(
        Produto, ProdutoImage, form=ProdutoImageForm, extra=1, can_delete=True, max_num=5
    )

    # 3. Lógica para requisições POST vs GET
    if request.method == 'POST':
        # Se a requisição é POST (o formulário foi enviado)
        # Instancia os formulários com os dados enviados (request.POST, request.FILES)
        # e associa à instância existente do produto (instance=produto)
        form = ProdutoForm(request.POST, instance=produto)
        formset = ProdutoImageFormSet(request.POST, request.FILES, instance=produto)

        # Verifica se ambos os formulários são válidos
        if form.is_valid() and formset.is_valid():
            form.save()      # Salva as alterações no produto
            formset.save()   # Salva as alterações nas imagens (incluindo novas, atualizações e exclusões)
            
            # Redireciona para a lista de produtos após a modificação bem-sucedida
            # Você pode mudar para 'produtos:produto_detalhe' produto_id=produto.pk se preferir ir para a página de detalhes
            return redirect('produtos:lista_produtos')
        
        # Se a validação falhar (o if acima for False), o código continua aqui.
        # As variáveis 'form' e 'formset' já estão definidas acima (com os dados e erros).
        # Elas serão passadas para o contexto e o template as exibirá com as mensagens de erro.

    else: # Este bloco é executado para requisições GET (quando a página é carregada pela primeira vez)
        # Para requisições GET, inicializa os formulários com os dados do produto existente
        form = ProdutoForm(instance=produto) # <-- 'form' é definido aqui
        formset = ProdutoImageFormSet(instance=produto) # <-- 'formset' é definido aqui

    # 4. Prepare o dicionário de contexto
    # As variáveis 'form' e 'formset' SEMPRE estarão definidas neste ponto do código,
    # seja porque foram definidas no bloco 'if POST' ou no bloco 'else GET'.
    context = {
        'form': form,
        'formset': formset,
        'produto': produto,         # Passa o objeto produto para o template
        'is_adding': False          # Indica que esta é a página de modificação (não de adição)
    }

    # 5. Renderiza o template 'modificar_produto.html' com o contexto
    return render(request, 'produtos/modificar_produto.html', context)

# (Não se esqueça de manter o restante do seu arquivo views.py abaixo desta função)

# View para excluir produto
@user_passes_test(is_manager_or_admin, login_url='account_login')
def excluir_produto(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id)
    if request.method == 'POST':
        produto.delete()
        # Opcional: Adicionar mensagem de sucesso aqui com django.contrib.messages
        # messages.success(request, f'Produto "{produto.name}" excluído com sucesso!')
        return redirect('produtos:lista_produtos')
    
    # Se for GET, você pode renderizar uma página de confirmação de exclusão
    return render(request, 'produtos/confirmar_exclusao_produto.html', {'produto': produto})

# ... outras views ...