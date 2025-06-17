# pagamento/views.py

from django.views.decorators.http import require_POST
import stripe # Já está no final, mas pode ir aqui também para clareza
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST # <<< AGORA ESTÁ IMPORTADO!
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse # Adicione HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone # Para timezone.now()
from produtos.models import Produto, Pedido, Item # Se precisar do Produto, Pedido, Item

stripe.api_key = settings.STRIPE_SECRET_KEY


# pagamento/views.py

# ... (imports) ...

# pagamento/views.py

# ... (outros imports) ...

@require_POST
def criar_checkout_session(request):
    print("\n--- INÍCIO: criar_checkout_session ---")
    carrinho = request.session.get('carrinho', {})
    print(f"DEBUG: Carrinho recebido: {carrinho}")

    if not carrinho:
        messages.error(request, "Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.")
        print("ERRO DEBUG: Carrinho vazio. Redirecionando para ver_carrinho.")
        return redirect('produtos:ver_carrinho')

    line_items = []
    total_pedido_calculado = 0.0

    customer_email = None 
    customer_name = None

    # 1. Obtenção e Validação do Email e Nome do Cliente
    if request.user.is_authenticated:
        customer_email = request.user.email
        customer_name = request.user.get_full_name() or request.user.username
        print(f"DEBUG: Cliente autenticado - Email: {customer_email}, Nome: {customer_name}")
    else:
        customer_email = request.POST.get('email')
        customer_name = request.POST.get('nome_convidado', 'Convidado')
        
        if not customer_email or "@" not in customer_email or "." not in customer_email:
            messages.error(request, "Por favor, insira um e-mail válido para continuar como convidado.")
            print(f"ERRO DEBUG: Email do convidado inválido/ausente: '{customer_email}'. Redirecionando para ver_carrinho.")
            return redirect('produtos:ver_carrinho')
        print(f"DEBUG: Cliente convidado - Email: {customer_email}, Nome: {customer_name}")
    
    print(f"DEBUG: Cliente final para Stripe - Email: {customer_email}, Nome: {customer_name}")

    # 2. Processar Itens do Carrinho para o Stripe
    for item_key, item_data in carrinho.items():
        try:
            # Validação rigorosa dos dados do item na sessão.
            # Essas chaves DEVEM estar presentes no dicionário de cada item no seu request.session['carrinho']
            required_keys = ['produto_id', 'nome', 'preco_unitario', 'quantidade', 'subtotal', 'imagem', 'description']
            if not all(k in item_data for k in required_keys):
                missing_keys = [k for k in required_keys if k not in item_data]
                messages.error(request, f"Erro: Item '{item_data.get('nome', 'desconhecido')}' no carrinho está incompleto (faltam: {', '.join(missing_keys)}). Não pode ser processado.")
                print(f"ERRO DEBUG: Item incompleto no carrinho. Faltam chaves: {missing_keys}. Item data: {item_data}. Redirecionando.")
                return redirect('produtos:ver_carrinho') # REDIRECIONA SE HÁ DADOS INCOMPLETOS

            preco_em_centavos = int(item_data['preco_unitario'] * 100)
            quantidade_item = item_data['quantidade']
            item_description = item_data['description']
            item_images = [item_data['imagem']] if item_data['imagem'] else []

            # Stripe exige pelo menos 'name' ou 'description' para product_data.
            # Se 'description' estiver vazia E 'images' estiver vazia, use 'name'.
            if not item_description and not item_images:
                item_description = item_data['nome'] 
            # O Stripe também pode rejeitar URLs de imagem que não são acessíveis publicamente.

            print(f"DEBUG: Processando item para Stripe: {item_data['nome']}, Preço: {preco_em_centavos}, Qtd: {quantidade_item}, Imagens: {item_images}")

            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': item_data['nome'],
                        'description': item_description,
                        'images': item_images,
                    },
                    'unit_amount': preco_em_centavos,
                },
                'quantity': quantidade_item,
            })
            total_pedido_calculado += item_data['subtotal']

        except Exception as e: # Captura KeyErrors e outros erros aqui
            print(f"ERRO DEBUG: Erro inesperado ao processar um item do carrinho: {e}. Item data: {item_data}. Redirecionando.")
            messages.error(request, f"Ocorreu um erro ao processar um item do carrinho: {e}")
            return redirect('produtos:ver_carrinho')

    if not line_items:
        print("ERRO DEBUG: line_items está vazio após o loop. Redirecionando.")
        messages.error(request, "Seu carrinho não contém produtos válidos para finalizar a compra.")
        return redirect('produtos:ver_carrinho')

    # 3. Criar ou Obter Cliente Stripe
    customer_stripe_id = None
    try:
        clientes = stripe.Customer.list(email=customer_email, limit=1)
        if clientes.data:
            customer = clientes.data[0]
            customer_stripe_id = customer.id
            print(f"DEBUG: Cliente Stripe existente: {customer_stripe_id}")
        else:
            customer = stripe.Customer.create(email=customer_email, name=customer_name)
            customer_stripe_id = customer.id
            print(f"DEBUG: Novo cliente Stripe criado: {customer_stripe_id}")
    except stripe.error.StripeError as e:
        print(f"ERRO DEBUG Stripe ao gerenciar cliente: {e}. Redirecionando.")
        messages.error(request, f"Erro ao gerenciar cliente Stripe: {e.user_message}")
        return redirect('produtos:ver_carrinho')
    except Exception as e:
        print(f"ERRO DEBUG Geral ao gerenciar cliente: {e}. Redirecionando.")
        messages.error(request, f"Ocorreu um erro ao gerenciar cliente Stripe: {e}")
        return redirect('produtos:ver_carrinho')

    # 4. Criar Sessão de Checkout Stripe
    checkout_session = None # Inicializa para garantir que 'checkout_session' seja sempre definido
    try:
        print(f"DEBUG: Tentando criar Stripe checkout session com {len(line_items)} itens.")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer=customer_stripe_id,
            success_url = request.build_absolute_uri(reverse('pagamento:compra_sucesso')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url = request.build_absolute_uri(reverse('pagamento:pagamento_cancelado'))

        )
        print(f"DEBUG: Sessão de checkout Stripe criada com sucesso: {checkout_session.id}")

    except stripe.error.StripeError as e:
        print(f"ERRO DEBUG Stripe ao criar sessão de checkout: {e}. Redirecionando.")
        messages.error(request, f"Erro ao criar sessão de checkout: {e.user_message}")
        return redirect('produtos:ver_carrinho')
    except Exception as e:
        print(f"ERRO DEBUG Geral ao criar sessão de checkout: {e}. Redirecionando.")
        messages.error(request, f"Ocorreu um erro inesperado ao criar a sessão de checkout: {e}")
        return redirect('produtos:ver_carrinho')

    # 5. Salvar Pedido no Modelo Django (ANTES do redirecionamento para o Stripe)
    # Esta parte só executa se a sessão do Stripe foi criada com sucesso
    try:
        if not checkout_session: # Validação extra: se checkout_session não foi criado (ex: por erro na linha 4)
            messages.error(request, "Erro interno: A sessão de checkout não foi criada. Tente novamente.")
            print("ERRO DEBUG: checkout_session é None antes de tentar salvar o pedido Django.")
            return redirect('produtos:ver_carrinho')

        pedido = Pedido.objects.create(
            stripe_id=checkout_session.id,
            usuario=request.user if request.user.is_authenticated else None,
            email_cliente=customer_email, # Garanta que customer_email está definido
            total=total_pedido_calculado,
            status='pendente'
        )
        for item_key, item_data in carrinho.items():
            # AQUI: O produto_id_original deve existir em item_data
            Item.objects.create(
                pedido=pedido,
                produto_id_original=item_data['produto_id'], # Assegure-se que 'produto_id' está no item_data
                nome=item_data['nome'],
                preco_unitario=item_data['preco_unitario'],
                quantidade=item_data['quantidade'],
                subtotal=item_data['subtotal']
            )
        request.session['pedido_em_criacao_id'] = pedido.id 
        print(f"DEBUG: Pedido Django criado com ID: {pedido.id}")
    except Exception as e:
        print(f"ERRO DEBUG ao salvar pedido Django: {e}. Redirecionando.")
        messages.error(request, f"Erro ao salvar o pedido no banco de dados: {e}")
        return redirect('produtos:ver_carrinho')

    # 6. Redirecionar para o Stripe Checkout
    print(f"DEBUG: Redirecionando para Stripe URL: {checkout_session.url}")
    print("--- FIM: criar_checkout_session ---")
    return redirect(checkout_session.url, code=303)


# A view stripe_webhook (CORRIGIDA E MELHORADA para lidar com Pedidos Django)
@csrf_exempt
@require_POST # Webhooks sempre são POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET 

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'status': 'invalid signature'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error'}, status=500)

    # Lidar com os tipos de evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        checkout_session_id = session.id
        
        try:
            pedido = Pedido.objects.get(stripe_id=checkout_session_id)

            if pedido.status == 'pendente':
                pedido.status = 'pago'
                pedido.data_pagamento = timezone.now()
                pedido.save()
            else:
                # Caso o webhook seja acionado mais de uma vez ou o pedido já esteja processado
                pass 

        except Pedido.DoesNotExist:
            # Isso pode acontecer se o pedido não foi salvo no DB antes de ir para o Stripe
            # ou se houver um erro de sincronização.
            # Aqui você pode tentar criar um novo pedido com base na sessão do Stripe.
            pass
        except Exception as e:
            # Erro interno ao processar o webhook
            return JsonResponse({'status': f'error processing event: {e}'}, status=500)

    # Adicione tratamento para outros eventos do Stripe que você queira gerenciar
    elif event['type'] == 'payment_intent.succeeded':
        # Geralmente já coberto por checkout.session.completed se você usa Checkout Sessions
        pass
    
    elif event['type'] == 'payment_intent.payment_failed':
        # Lógica para atualizar o status do pedido para 'falhou'
        # Você precisaria do payment_intent.id e um campo correspondente no seu modelo Pedido
        pass
    
    return JsonResponse({'status': 'success'}, status=200)

# --- VIEWS DE SUCESSO/CANCELAMENTO PÓS-PAGAMENTO ---

def compra_sucesso(request): # Renomeado de 'success' para 'compra_sucesso'
    session_id = request.GET.get('session_id')

    if not session_id:
        messages.error(request, "ID da sessão de checkout não encontrado. Sua compra pode não ter sido concluída.")
        return redirect('produtos:home')

    try:
        pedido = get_object_or_404(Pedido, stripe_id=session_id)
        itens = pedido.itens.all() # Acessa os itens relacionados a este pedido

        # Limpar o carrinho do usuário - APENAS SE o pedido foi pago e você confia nisso
        if 'carrinho' in request.session:
            del request.session['carrinho']
            request.session.modified = True
            messages.success(request, "Seu carrinho foi limpo com sucesso!")
        
        # A atualização do status do pedido é preferencialmente feita no webhook para robustez.
        # Mas você pode ter uma validação extra aqui se quiser.
        if pedido.status == 'pendente':
            # Isso é um fallback. O webhook é a principal fonte de verdade.
            pedido.status = 'pago'
            pedido.data_pagamento = timezone.now()
            pedido.save()
            messages.info(request, "Status do pedido atualizado (fallback da view de sucesso).")

        messages.success(request, f"Sua compra (Pedido #{pedido.id}) foi realizada com sucesso! Um e-mail de confirmação será enviado.")
        return render(request, 'pagamento/compra_sucesso.html', {
            'pedido': pedido,
            'itens': itens,
        })

    except Pedido.DoesNotExist:
        messages.error(request, f"Pedido correspondente ao ID da sessão '{session_id}' não encontrado no nosso sistema.")
        return redirect('produtos:home')
    except Exception as e:
        messages.error(request, f"Ocorreu um erro inesperado ao processar sua compra: {e}")
        return redirect('produtos:home')


def pagamento_cancelado(request): # Renomeado de 'cancel' para 'pagamento_cancelado'
    messages.info(request, "Seu pagamento foi cancelado. Você pode tentar novamente.")
    return render(request, 'pagamento/pagamento_cancelado.html') # Assegure-se de que este template existe