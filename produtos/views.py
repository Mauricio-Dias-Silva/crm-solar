from django.shortcuts import render, redirect, get_object_or_404
from .models import CarouselImage, Pedido, Item
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login
from .forms import CustomUserCreationForm, ArquivoImpressaoForm
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

import stripe
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
# from .models import CarouselImage # <--- Descomente e importe se estiver usando este modelo

# Inicialize o Stripe com sua chave secreta
stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):

    categorias_esperadas = [
        'paineis_solares',
        'inversores',
        'baterias',
        'kits_fotovoltaicos',
        'estruturas_montagem',
        'acessorios',
        # 'outros', # Se você quiser que produtos sem categoria_id específica apareçam em uma categoria "outros"
    ]
    
    produtos_por_categoria = {}    
    for cat_name in categorias_esperadas:
        produtos_por_categoria[cat_name] = [] 

    all_products_from_stripe = [] # Lista para guardar todos os produtos processados (opcional para debug/outros usos)

    # ... (resto do código da view home) ...

    try:
        products_iterator = stripe.Product.list(active=True, expand=['data.default_price']).auto_paging_iter()
        
        for stripe_product in products_iterator:
            # --- DESCOMENTE ESTES PRINTS ---
            print(f"DEBUG: Processando produto Stripe: {stripe_product.name} (ID: {stripe_product.id})")
            print(f"DEBUG: Metadados do produto: {stripe_product.metadata.get('categoria_id')}")
            print(f"DEBUG: Preço padrão do produto (objeto Stripe): {stripe_product.get('default_price')}")
            print(f"DEBUG: Produto ativo (Stripe): {stripe_product.active}")

            if stripe_product.get('default_price') and \
               isinstance(stripe_product['default_price'], stripe.Price) and \
               stripe_product['default_price']['type'] == 'one_time': # <-- Verificação do tipo de preço
                
                preco_obj = stripe_product['default_price']
                preco_unitario = float(preco_obj['unit_amount']) / 100
                
                produto_categoria_id = stripe_product.metadata.get('categoria_id', 'outros').lower()
                
                if produto_categoria_id in categorias_esperadas: # Removi 'or produto_categoria_id == "outros"' para focar em categorias esperadas
                    produto_para_template = {
                        # ... (dados do produto) ...
                    }
                    if produto_categoria_id not in produtos_por_categoria:
                        produtos_por_categoria[produto_categoria_id] = []
                    produtos_por_categoria[produto_categoria_id].append(produto_para_template)
                    all_products_from_stripe.append(produto_para_template)                       
        

    except stripe.error.StripeError as e:
        messages.error(request, f"Não foi possível carregar os produtos no momento: {e}. Tente novamente mais tarde.")
    except Exception as e:
        messages.error(request, f"Ocorreu um erro inesperado ao carregar produtos: {e}.")

# ... (resto do código da view home) ...


    # Preparar a lista de categorias para o navbar dropdown e o segundo navbar
    categorias_para_template = [
        {'nome_url': cat, 'nome_exibicao': cat.replace('_', ' ').title()}
        for cat in categorias_esperadas
    ]
    # Se você quiser adicionar "Outros" no dropdown
    # if 'outros' in produtos_por_categoria and produtos_por_categoria['outros']:
    #     categorias_para_template.append({'nome_url': 'outros', 'nome_exibicao': 'Outros Produtos'})

    # Para o carrossel
    try:
        carousel_images = CarouselImage.objects.filter(is_active=True) 
    except NameError:
        messages.warning(request, "Modelo CarouselImage não encontrado. Carrossel não será exibido.")
        carousel_images = []
    except Exception as e:
        messages.error(request, f"ERRO ao carregar imagens do carrossel: {e}")
        carousel_images = []

    context = {
        'produtos_por_categoria': produtos_por_categoria,
        'carousel_images': carousel_images,
        'categorias_ativas': categorias_para_template,
    }
    return render(request, 'produtos/home.html', context)


def produtos_por_categoria(request, categoria_id):
    # O nome de exibição da categoria é gerado a partir do categoria_id da URL
    categoria_nome_exibicao = categoria_id.replace('_', ' ').title()

    produtos_na_categoria = []

    try:
        # Busca produtos do Stripe com EXPAND para carregar o preço junto
        products_iterator = stripe.Product.list(active=True, expand=['data.default_price']).auto_paging_iter()
        
        for produto_stripe in products_iterator:
            # Garante que o produto tem preço e que o preço foi expandido
            if produto_stripe.get('default_price') and isinstance(produto_stripe['default_price'], stripe.Price):
                preco_obj = produto_stripe['default_price']
                preco_unitario = float(preco_obj['unit_amount']) / 100
                
                # Obtém a categoria do metadado e CONVERTE PARA MINÚSCULAS para a comparação
                produto_categoria_meta_id = produto_stripe.metadata.get('categoria_id', '').lower()
                
                # Compara a categoria do metadado (em minúsculas) com a categoria_id da URL (também em minúsculas)
                if produto_categoria_meta_id == categoria_id.lower(): 
                    # Adiciona apenas produtos que pertencem a esta categoria E que têm imagens
                    if produto_stripe.images: # Assumindo que você quer apenas produtos com imagens
                        produtos_na_categoria.append({
                            'id': produto_stripe.id,
                            'name': produto_stripe.name,
                            'description': produto_stripe.description,
                            'images': produto_stripe.images, # Lista de URLs de imagem
                            'preco': preco_unitario, # 'preco' está disponível
                            'categoria_url': categoria_id, 
                            'categoria_exibicao': categoria_nome_exibicao, # Nome formatado para o template
                        })
                    else:
                        print(f"DEBUG: Produto '{produto_stripe.name}' (ID: {produto_stripe.id}) não tem imagens e foi pulado na categoria {categoria_id}.")
            else:
                print(f"DEBUG: Produto '{produto_stripe.name}' (ID: {produto_stripe.id}) sem default_price ou preço não expandido na categoria {categoria_id}.")

    except stripe.error.StripeError as e:
        print(f"ERRO STRIPE na categoria {categoria_id}: Não foi possível listar produtos. Erro: {e}")
        messages.error(request, "Não foi possível carregar os produtos desta categoria no momento.")
    except Exception as e:
        print(f"ERRO INESPERADO na categoria {categoria_id}: {e}")
        messages.error(request, "Ocorreu um erro ao carregar os produtos desta categoria.")

    # Constrói o objeto categoria para o template
    categoria_para_template = {
        'id': categoria_id, 
        'nome': categoria_nome_exibicao,
    }

    return render(request, 'produtos/produtos_por_categoria.html', {
        'categoria': categoria_para_template,
        'produtos': produtos_na_categoria,
    })

def about(request):
    return render(request, 'produtos/about.html')


def produto_detalhes(request, produto_id):
    produto = stripe.Product.retrieve(produto_id)
    default_price_id = produto['default_price']
    preco = stripe.Price.retrieve(default_price_id)
    produto['preco'] = preco['unit_amount'] / 100  # Convertendo centavos para reais
    produto['tipo'] = produto.metadata.get('tipo', 'unidade')  # Adicionar o tipo de produto

    if request.method == 'POST':
        if produto['tipo'] == 'metro_quadrado':
            altura = float(request.POST.get('altura', 0)) / 100  # Converter para metros
            largura = float(request.POST.get('largura', 0)) / 100  # Converter para metros
            quantidade = int(request.POST.get('quantidade', 1))
            preco_total = produto['preco'] * altura * largura * quantidade
        else:
            quantidade = int(request.POST.get('quantidade', 1))
            preco_total = produto['preco'] * quantidade

        carrinho = request.session.get('carrinho', {})
        carrinho[produto_id] = {
            'nome': produto['name'],
            'preco': preco_total,
            'imagem': produto['images'][0] if produto['images'] else None,
            'quantidade': quantidade,
        }
        request.session['produtos:carrinho'] = carrinho
        return redirect('produtos:ver_carrinho')  # Redireciona para visualizar o carrinho

    return render(request, 'produtos/produto_detalhe.html', {'produto': produto})

def contact(request):
    if request.method == "POST":
        # Lógica para processar o formulário de contato
        pass
    return render(request, 'produtos/contact.html')

def search(request):
    query = request.GET.get('q')
    produtos = []

    if query:
        produtos_stripe = stripe.Product.search(
            query=f"name:'{query}'",
            limit=10  # Defina um limite de resultados, se necessário
        )
        produtos = produtos_stripe['data']

    return render(request, 'produtos/home.html', {'produtos': produtos})


def success(request):
    # 1. Obter o session_id do Stripe da URL (GET parameter)
    session_id = request.GET.get('session_id')
    print(f"DEBUG Success View: session_id recebido da URL: {session_id}")

    if not session_id:
        messages.error(request, "ID da sessão de checkout não encontrado. Sua compra pode não ter sido concluída.")
        print("DEBUG Success View: session_id não encontrado na URL.")
        return redirect('produtos:home') # Redireciona para home ou carrinho se não tiver ID

    try:
        # 2. Buscar o Pedido Django usando o stripe_id (que é o session_id)
        # Usamos .get_object_or_404 para levantar um 404 se o pedido não existir
        pedido = get_object_or_404(Pedido, stripe_id=session_id)
        itens = pedido.itens.all() # Acessa os itens relacionados a este pedido
        print(f"DEBUG Success View: Pedido {pedido.id} encontrado para session_id: {session_id}")

        # 3. Limpar o carrinho do usuário
        # É seguro limpar o carrinho AQUI, pois o pagamento já foi confirmado pelo Stripe
        # e o pedido já foi salvo no DB.
        if 'carrinho' in request.session:
            del request.session['carrinho']
            request.session.modified = True
            messages.success(request, "Seu carrinho foi limpo com sucesso!")
            print("DEBUG Success View: Carrinho limpo da sessão.")

        # Opcional: Atualizar status do pedido (se o webhook não fizer isso ou para reforçar)
        if pedido.status == 'pendente':
            pedido.status = 'pago' # Ou 'concluido', 'processando'
            pedido.data_pagamento = timezone.now() # Agora timezone está definido
            pedido.save()
            print(f"DEBUG Success View: Status do pedido {pedido.id} atualizado para 'pago'.")
        
        # 4. Renderizar a página de sucesso (sem lógica de formulário de arquivo)
        messages.success(request, f"Sua compra (Pedido #{pedido.id}) foi realizada com sucesso! Um e-mail de confirmação será enviado.")
        return render(request, 'produtos/success.html', {
            'pedido': pedido,
            'itens': itens,
        })

    except Pedido.DoesNotExist:
        messages.error(request, f"Pedido correspondente ao ID da sessão '{session_id}' não encontrado no nosso sistema.")
        print(f"ERRO Success View: Pedido com stripe_id '{session_id}' não encontrado no DB.")
        return redirect('produtos:home')
    except Exception as e:
        messages.error(request, f"Ocorreu um erro inesperado ao processar sua compra: {e}")
        print(f"ERRO Success View: Erro inesperado: {e}")
        return redirect('produtos:home')


def cancel(request):
    # Se você tiver o produto_id armazenado em algum lugar (por exemplo, na sessão):
    produto_id = request.session.get('produto_id') 
    if produto_id:
        return redirect('produtos:produto_detalhe', produto_id=produto_id) 
    else:
        # Se não tiver o produto_id, redirecionar para a página inicial ou outra página apropriada
        return redirect('home') 

def termos_de_servico(request):
    return render(request, 'produtos/termos_de_servico.html', {})


def politica_privacidade(request):
    return render(request, 'produtos/politica_privacidade.html', {})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Use o backend apropriado para logar o usuário
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('produtos:home')  # Redirecionar para a página inicial ou outra página
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})






def adicionar_ao_carrinho(request, produto_id):
    print(f"\n--- Início da view adicionar_ao_carrinho para produto_id: {produto_id} ---")
    print(f"Método da requisição: {request.method}")
    print(f"Conteúdo de POST: {request.POST}")

    if request.method == 'POST':
        try:
            # 1. Recupera o produto do Stripe
            stripe_product = stripe.Product.retrieve(produto_id)
            print(f"Produto Stripe recuperado: {stripe_product['name']}")
            if not stripe_product.get('active') or not stripe_product.get('default_price'):
                messages.error(request, "Produto não disponível para compra.")
                print("ERRO: Produto não ativo ou sem preço padrão.")
                return redirect('produtos:home')

            stripe_price_id = stripe_product['default_price']
            stripe_price = stripe.Price.retrieve(stripe_price_id)
            
            # Garanta que o preço unitário seja um float
            preco_unitario = float(stripe_price['unit_amount']) / 100 
            print(f"Preço unitário: {preco_unitario}")

        except stripe.error.StripeError as e:
            messages.error(request, f"Erro ao buscar produto no Stripe: {e}")
            print(f"ERRO Stripe: {e}")
            return redirect('produtos:home')
        except Exception as e:
            messages.error(request, f"Ocorreu um erro inesperado: {e}")
            print(f"ERRO Geral: {e}")
            return redirect('produtos:home')

        # 2. Obtém a quantidade do formulário (agora sem altura/largura)
        quantidade = int(request.POST.get('quantidade', 1))
        
        print(f"Dados do formulário: Quantidade={quantidade}")

        carrinho = request.session.get('carrinho', {})
        print(f"Carrinho ANTES da modificação na sessão: {carrinho}")

        # Lógica para adicionar ou atualizar o item no carrinho (SÓ POR PRODUTO_ID)
        item_key = produto_id # A chave do item no carrinho é o próprio produto_id

        if item_key in carrinho:
            # Item já existe, atualiza a quantidade e recalcula o subtotal
            carrinho[item_key]['quantidade'] += quantidade
            carrinho[item_key]['subtotal'] = preco_unitario * carrinho[item_key]['quantidade']
            print(f"Item '{carrinho[item_key]['nome']}' atualizado. Nova quantidade: {carrinho[item_key]['quantidade']}")
        else:
            # Item novo, adiciona ao carrinho
            carrinho[item_key] = {
                'produto_id': produto_id,
                'nome': stripe_product['name'],
                'preco_unitario': preco_unitario,
                'imagem': stripe_product['images'][0] if stripe_product['images'] else None,
                'quantidade': quantidade,
                'subtotal': preco_unitario * quantidade,
            }
            print(f"Novo item '{carrinho[item_key]['nome']}' adicionado.")
        
        request.session['carrinho'] = carrinho
        request.session.modified = True 
        
        print(f"Carrinho DEPOIS da modificação na sessão: {request.session['carrinho']}")
        print(f"Sessão modificada: {request.session.modified}")
        print("--- Fim da view adicionar_ao_carrinho ---\n")

        messages.success(request, f"{stripe_product['name']} adicionado ao carrinho com sucesso!")
        return redirect('produtos:ver_carrinho')

    messages.error(request, "Método de requisição inválido para adicionar ao carrinho.")
    return redirect('produtos:home')

# views.py

def remover_do_carrinho(request, produto_id): # Mudado de item_key para produto_id
    carrinho = request.session.get('carrinho', {})
    if produto_id in carrinho: # Agora verifica apenas por produto_id
        del carrinho[produto_id]
        request.session['carrinho'] = carrinho 
        request.session.modified = True 
        messages.success(request, "Item removido do carrinho.")
    else:
        messages.error(request, "Item não encontrado no carrinho.")
    return redirect('produtos:ver_carrinho')

def ver_carrinho(request):
    print(f"\n--- Início da view ver_carrinho ---")
    print(f"Sessão em ver_carrinho: {request.session.keys()}")
    
    if not request.user.is_authenticated:
        request.session['next_url'] = request.path
        messages.info(request, "Faça login para ver seu carrinho ou continue como convidado e insira seu e-mail no checkout.")
        print("Usuário não autenticado, redirecionando para login.")
        return redirect('produtos:login')

    carrinho_session = request.session.get('carrinho', {})
    print(f"Conteúdo de request.session.get('carrinho', {{}}): {carrinho_session}")
    
    carrinho_display = {}
    total_carrinho = 0.0 # Inicializa como float

    for item_key, item_data in carrinho_session.items():
        try:
            # Garanta que o subtotal é um float antes de somar
            current_subtotal = float(item_data.get('subtotal', 0.0))
            carrinho_display[item_key] = item_data
            total_carrinho += current_subtotal
            print(f"Adicionando item {item_data.get('nome')} com subtotal {current_subtotal}. Total acumulado: {total_carrinho}")
        except Exception as e:
            print(f"ERRO ao processar item do carrinho ({item_key}): {e} - Item data: {item_data}")
            messages.error(request, f"Erro ao processar item do carrinho: {item_data.get('nome')}. Por favor, tente novamente.")
            # Opcional: Remover o item problemático para não quebrar a página
            # del request.session['carrinho'][item_key]
            # request.session.modified = True


    context = {
        'carrinho': carrinho_display,
        'total_carrinho': total_carrinho,
    }
    print(f"Carrinho para display: {carrinho_display}")
    print(f"Total do carrinho: {total_carrinho}")
    print("--- Fim da view ver_carrinho ---\n")
    return render(request, 'produtos/ver_carrinho.html', context)

# A view criar_checkout_session (CORRIGIDA E MELHORADA)
def criar_checkout_session(request):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        
        # 1. Validação: Carrinho vazio?
        if not carrinho:
            messages.error(request, "Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.")
            return redirect('produtos:ver_carrinho')

        line_items = []
        total_pedido_calculado = 0.0 # Para calcular o total que será salvo no Pedido Django

        # 2. Obtenção e Validação do Email e Nome do Cliente
        customer_email = None
        customer_name = None

        if request.user.is_authenticated:
            customer_email = request.user.email
            customer_name = request.user.get_full_name() or request.user.username
            print(f"DEBUG: Cliente autenticado - Email: {customer_email}, Nome: {customer_name}")
        else:
            # Para usuários não autenticados, o email VEM do formulário
            customer_email = request.POST.get('email')
            # Validação básica de email
            if not customer_email or "@" not in customer_email or "." not in customer_email:
                messages.error(request, "Por favor, insira um e-mail válido para continuar como convidado.")
                print(f"ERRO: Email do convidado inválido/ausente: '{customer_email}'")
                return redirect('produtos:ver_carrinho')
            
            # Você pode pedir o nome também para convidados se desejar
            # customer_name = request.POST.get('nome_convidado', 'Convidado') 
            customer_name = "Convidado" # Default se não tiver campo de nome para convidado
            print(f"DEBUG: Cliente convidado - Email: {customer_email}, Nome: {customer_name}")

        # 3. Processar Itens do Carrinho para o Stripe
        for item_key, item_data in carrinho.items():
            try:
                # O PREÇO CORRETO NA SESSÃO É 'preco_unitario'
                if 'preco_unitario' not in item_data or 'quantidade' not in item_data or 'subtotal' not in item_data:
                    messages.error(request, f"Erro: Item '{item_data.get('nome', 'desconhecido')}' no carrinho está incompleto.")
                    print(f"DEBUG: Item incompleto: {item_key}, data: {item_data}")
                    return redirect('produtos:ver_carrinho')

                preco_em_centavos = int(item_data['preco_unitario'] * 100)
                quantidade_item = item_data['quantidade']
                
                # Descrição para o produto Stripe
                item_description = item_data.get('description', 'Produto de energia solar') # Use 'description' do produto Stripe se existir
                if 'altura' in item_data and 'largura' in item_data: # Se por algum motivo ainda houver dados de metro quadrado
                    item_description += f" ({item_data['altura']}cm x {item_data['largura']}cm)"

                line_items.append({
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': item_data['nome'],
                            'description': item_description,
                            'images': [item_data['imagem']] if item_data['imagem'] else [],
                        },
                        'unit_amount': preco_em_centavos,
                    },
                    'quantity': quantidade_item,
                })
                total_pedido_calculado += item_data['subtotal'] # Soma o subtotal já calculado do item
            except KeyError as e:
                messages.error(request, f"Erro ao processar item do carrinho: Chave ausente '{e}' para um produto.")
                print(f"DEBUG: KeyError no item do carrinho: {e}, item_data: {item_data}")
                return redirect('produtos:ver_carrinho')
            except Exception as e:
                messages.error(request, f"Erro inesperado ao processar um item do carrinho: {e}")
                print(f"DEBUG: Erro inesperado no loop de line_items: {e}, item_data: {item_data}")
                return redirect('produtos:ver_carrinho')

        # 4. Criar ou Obter Cliente Stripe
        customer_stripe_id = None
        try:
            clientes = stripe.Customer.list(email=customer_email, limit=1) # Limita a 1 para ser mais rápido
            if clientes.data:
                customer = clientes.data[0]
                customer_stripe_id = customer.id
                print(f"DEBUG: Cliente Stripe existente: {customer_stripe_id}")
            else:
                customer = stripe.Customer.create(email=customer_email, name=customer_name)
                customer_stripe_id = customer.id
                print(f"DEBUG: Novo cliente Stripe criado: {customer_stripe_id}")
        except stripe.error.StripeError as e:
            messages.error(request, f"Erro ao gerenciar cliente Stripe: {e.user_message}")
            print(f"ERRO Stripe ao gerenciar cliente: {e}")
            return redirect('produtos:ver_carrinho')
        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao gerenciar cliente Stripe: {e}")
            print(f"ERRO Geral ao gerenciar cliente: {e}")
            return redirect('produtos:ver_carrinho')

        # 5. Criar Sessão de Checkout Stripe
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                customer=customer_stripe_id, # Associa o cliente Stripe à sessão
                # URLs de sucesso/cancelamento com namespaces corrigidos e session_id
                success_url=request.build_absolute_uri(reverse('produtos:compra_sucesso')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('produtos:ver_carrinho')),
                # customer_email=customer_email, # Não é necessário se 'customer' for associado
            )
            print(f"DEBUG: Sessão de checkout Stripe criada: {checkout_session.id}")
        except stripe.error.StripeError as e:
            messages.error(request, f"Erro ao criar sessão de checkout: {e.user_message}")
            print(f"ERRO Stripe ao criar sessão de checkout: {e}")
            return redirect('produtos:ver_carrinho')
        except Exception as e:
            messages.error(request, f"Ocorreu um erro inesperado ao criar a sessão de checkout: {e}")
            print(f"ERRO Geral ao criar sessão de checkout: {e}")
            return redirect('produtos:ver_carrinho')

        # 6. Salvar Pedido no Modelo Django (ANTES do redirecionamento para o Stripe)
        # O status inicial do pedido pode ser 'pendente', 'criado', etc.
        try:
            pedido = Pedido.objects.create(
                stripe_id=checkout_session.id,
                usuario=request.user if request.user.is_authenticated else None,
                email_cliente=customer_email, # Salva o email do cliente (autenticado ou convidado)
                total=total_pedido_calculado, # Total calculado a partir dos subtotais do carrinho
                status='pendente' # Status inicial do pedido
            )
            for item_key, item_data in carrinho.items():
                Item.objects.create(
                    pedido=pedido,
                    stripe_product_id=item_data['produto_id'], # ID do produto Stripe
                    nome=item_data['nome'],
                    preco_unitario=item_data['preco_unitario'],
                    quantidade=item_data['quantidade'],
                    subtotal=item_data['subtotal']
                    # Adicione altura/largura se ainda forem relevantes para o item
                    # altura=item_data.get('altura'),
                    # largura=item_data.get('largura'),
                )
            request.session['pedido_em_criacao_id'] = pedido.id # Guarda o ID do pedido para o webhook
            print(f"DEBUG: Pedido Django criado com ID: {pedido.id}")
        except Exception as e:
            messages.error(request, f"Erro ao salvar o pedido no banco de dados: {e}")
            print(f"ERRO ao salvar pedido Django: {e}")
            return redirect('produtos:ver_carrinho')

        # 7. Redirecionar para o Stripe Checkout
        return redirect(checkout_session.url, code=303)

    messages.error(request, "Método de requisição inválido para finalizar a compra.")
    return redirect('produtos:home') # Redireciona para home se não for POST


# A view stripe_webhook (CORRIGIDA E MELHORADA para lidar com Pedidos Django)
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    # Obtenha a chave de webhook do settings.py
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET 

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print(f"DEBUG Webhook: Evento recebido - Tipo: {event['type']}, ID: {event['id']}")
    except ValueError as e:
        print(f"ERRO Webhook: Payload inválido - {e}")
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"ERRO Webhook: Assinatura inválida - {e}")
        return JsonResponse({'status': 'invalid signature'}, status=400)
    except Exception as e:
        print(f"ERRO Webhook: Erro inesperado - {e}")
        return JsonResponse({'status': 'error'}, status=500)


    # Lidar com os tipos de evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        checkout_session_id = session.id
        customer_email = session.customer_details['email'] if session.customer_details else 'N/A'
        
        print(f"DEBUG Webhook: checkout.session.completed para Session ID: {checkout_session_id}, Email: {customer_email}")

        # Tenta encontrar o pedido Django correspondente
        try:
            # Use o stripe_id salvo para encontrar o pedido
            pedido = Pedido.objects.get(stripe_id=checkout_session_id)
            print(f"DEBUG Webhook: Pedido Django encontrado (ID: {pedido.id}, Status: {pedido.status})")

            if pedido.status == 'pendente': # Garante que não processa o mesmo pedido várias vezes
                pedido.status = 'pago' # Ou 'concluido', 'processando'
                pedido.data_pagamento = timezone.now() # Adicione data_pagamento ao seu modelo Pedido
                pedido.save()

                messages.success(request, "Sua compra foi confirmada com sucesso!") # Não será exibido diretamente
                print(f"DEBUG Webhook: Pedido {pedido.id} atualizado para 'pago'.")
            else:
                print(f"DEBUG Webhook: Pedido {pedido.id} já processado (Status: {pedido.status}).")

        except Pedido.DoesNotExist:
            print(f"ERRO Webhook: Pedido Django com stripe_id {checkout_session_id} não encontrado.")
            # Você pode registrar este evento e talvez criar um novo pedido aqui
            # para lidar com casos onde o pedido não foi salvo no DB (ex: erro na criação da sessão inicial)
        except Exception as e:
            print(f"ERRO Webhook: Erro ao processar evento checkout.session.completed para {checkout_session_id}: {e}")
            return JsonResponse({'status': 'error processing event'}, status=500) # Retorne 500 para o Stripe tentar novamente

    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"DEBUG Webhook: payment_intent.succeeded para Payment Intent ID: {payment_intent.id}")
        # Use este evento se você criar Payment Intents diretamente.
        # Geralmente, 'checkout.session.completed' é o suficiente para o fluxo de checkout.

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        print(f"DEBUG Webhook: payment_intent.payment_failed para Payment Intent ID: {payment_intent.id}")
        # Lidar com falhas de pagamento: atualizar status do pedido para 'falhou', notificar cliente, etc.

    # Sempre retorne 200 OK para o Stripe, mesmo que não processe o evento
    return JsonResponse({'status': 'success'}, status=200)



@login_required(login_url='login')
def finalizar_compra(request):
    # Lógica para limpar o carrinho ou finalizar a compra
    request.session['carrinho'] = {}
    return redirect('compra_sucesso')
