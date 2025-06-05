from django.shortcuts import render, redirect, get_object_or_404
from .models import CarouselImage, Pedido, Item
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login
from .forms import CustomUserCreationForm, ArquivoImpressaoForm
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def criar_checkout_session(request):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        line_items = []

        if request.user.is_authenticated:
            email = request.user.email
            nome = request.user.get_full_name()
        else:
            email = request.POST.get('email', 'email_do_cliente@example.com')
            nome = 'Nome do Cliente'

        for produto_id, produto in carrinho.items():
            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': produto['nome'],
                    },
                    'unit_amount': int(produto['preco'] * 100),  # valor em centavos
                },
                'quantity': produto['quantidade'],
            })

        clientes = stripe.Customer.list(email=email)
        if clientes.data:
            customer = clientes.data[0]
        else:
            customer = stripe.Customer.create(email=email, name=nome)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer=customer.id,
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('cancel')),
        )

        # Salvar informações do pedido no modelo Django
        pedido = Pedido.objects.create(
            stripe_id=session.id,
            usuario=request.user if request.user.is_authenticated else None,
            total=sum(item['preco'] * item['quantidade'] for item in carrinho.values())
        )
        for produto_id, produto in carrinho.items():
            Item.objects.create(
                nome=produto['nome'],
                quantidade=produto['quantidade'],
                pedido=pedido
            )

        request.session['pedido_id'] = pedido.id
        return redirect(session.url, code=303)
    return redirect('home')


def home(request):
    categorias = [
        'adesivos',
        'banners',
        'faixas',
    ]

    produtos_por_categoria = {}
    produtos = stripe.Product.list(active=True)

    for categoria in categorias:
        produtos_categoria = []
        for produto in produtos['data']:
            if produto.metadata.get('categoria_id') == categoria:
                preco_id = produto['default_price']
                if preco_id:
                    preco = stripe.Price.retrieve(preco_id)
                    produto['preco'] = preco['unit_amount'] / 100  # Convertendo centavos para reais
                produtos_categoria.append(produto)
        produtos_por_categoria[categoria] = produtos_categoria

    carousel_images = CarouselImage.objects.filter(is_active=True)

    return render(request, 'produtos/home.html', {
        'produtos_por_categoria': produtos_por_categoria,
        'carousel_images': carousel_images,
    })


def produtos_por_categoria(request, categoria_id):
    categoria_nome = {
        'adesivos': 'Adesivos',
        'banners': 'Banners',
        'faixas': 'Faixas'
    }

    produtos = stripe.Product.list(active=True)
    produtos_categoria = []

    for produto in produtos['data']:
        if produto.metadata.get('categoria_id') == categoria_id:
            preco_id = produto['default_price']
            if preco_id:
                preco = stripe.Price.retrieve(preco_id)
                produto['preco'] = preco['unit_amount'] / 100  # Convertendo centavos para reais
            produtos_categoria.append(produto)

    return render(request, 'produtos/produtos_por_categoria.html', {
        'categoria': {'id': categoria_id, 'nome': categoria_nome.get(categoria_id, 'Categoria Desconhecida')},
        'produtos': produtos_categoria
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
        request.session['carrinho'] = carrinho
        return redirect('ver_carrinho')  # Redireciona para visualizar o carrinho

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
    pedido_id = request.session.get('pedido_id')
    pedido = Pedido.objects.get(id=pedido_id)
    itens = pedido.itens.all()

    if request.method == 'POST':
        for item in itens:
            form = ArquivoImpressaoForm(request.POST, request.FILES)
            if form.is_valid():
                arquivo_impressao = form.save(commit=False)
                arquivo_impressao.usuario = request.user
                arquivo_impressao.nome_item = item.nome  # Adicionar o nome do item ao arquivo
                arquivo_impressao.save()
        return redirect('home')

    form_item_pairs = [(ArquivoImpressaoForm(), item) for item in itens]

    return render(request, 'produtos/success.html', {
        'form_item_pairs': form_item_pairs,
        'pedido': pedido,
        'itens': itens
    })


def cancel(request):
    # Se você tiver o produto_id armazenado em algum lugar (por exemplo, na sessão):
    produto_id = request.session.get('produto_id') 
    if produto_id:
        return redirect('produto_detalhe', produto_id=produto_id) 
    else:
        # Se não tiver o produto_id, redirecionar para a página inicial ou outra página apropriada
        return redirect('home') 



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Use o backend apropriado para logar o usuário
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')  # Redirecionar para a página inicial ou outra página
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = 'sua_chave_secreta_do_webhook'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'status': 'invalid signature'}, status=400)

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Fulfill the purchase...
    elif event['type'] == 'payment_method.attached':
        payment_method = event['data']['object']
        # Handle the event...

    return JsonResponse({'status': 'success'}, status=200)

def adicionar_ao_carrinho(request, produto_id):
    if request.method == 'POST':
        produto = stripe.Product.retrieve(produto_id)
        default_price_id = produto['default_price']
        preco = stripe.Price.retrieve(default_price_id)
        preco_total = preco['unit_amount'] / 100  # Convertendo centavos para reais

        quantidade = int(request.POST.get('quantidade', 1))
        altura = float(request.POST.get('altura', 0)) / 100  # Converter para metros
        largura = float(request.POST.get('largura', 0)) / 100  # Converter para metros

        if altura > 0 and largura > 0:
            preco_total = preco_total * altura * largura * quantidade

        carrinho = request.session.get('carrinho', {})
        carrinho[produto_id] = {
            'nome': produto['name'],
            'preco': preco_total,
            'imagem': produto['images'][0] if produto['images'] else None,
            'quantidade': quantidade,
        }
        request.session['carrinho'] = carrinho
        return redirect('ver_carrinho')
    return redirect('home')


def remover_do_carrinho(request, produto_id):
    carrinho = request.session.get('carrinho', {})
    if produto_id in carrinho:
        del carrinho[produto_id]
    request.session['carrinho'] = carrinho
    return redirect('ver_carrinho')

def ver_carrinho(request):
    
    if not request.user.is_authenticated:
        request.session['next'] = request.path
        return redirect('login')
    
    carrinho = request.session.get('carrinho', {})
    return render(request, 'produtos/ver_carrinho.html', {'carrinho': carrinho})



@login_required(login_url='login')
def finalizar_compra(request):
    # Lógica para limpar o carrinho ou finalizar a compra
    request.session['carrinho'] = {}
    return redirect('compra_sucesso')


