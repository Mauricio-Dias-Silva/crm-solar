
from django.views.decorators.http import require_POST
import stripe 
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone 
from produtos.models import Produto, Pedido, Item 

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
def criar_checkout_session(request):
    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        messages.error(request, "Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.")
        return redirect('produtos:ver_carrinho')

    line_items = []
    total_pedido_calculado = 0.0

    customer_email = None 
    customer_name = None

    if request.user.is_authenticated:
        customer_email = request.user.email
        customer_name = request.user.get_full_name() or request.user.username
    else:
        customer_email = request.POST.get('email')
        customer_name = request.POST.get('nome_convidado', 'Convidado')
        if not customer_email or "@" not in customer_email or "." not in customer_email:
            messages.error(request, "Por favor, insira um e-mail válido para continuar como convidado.")
            return redirect('produtos:ver_carrinho')

    for item_data in carrinho.values():
        try:
            required_keys = ['produto_id', 'nome', 'preco_unitario', 'quantidade', 'subtotal', 'imagem', 'description']
            if not all(k in item_data for k in required_keys):
                missing_keys = [k for k in required_keys if k not in item_data]
                messages.error(request, f"Erro: Item '{item_data.get('nome', 'desconhecido')}' no carrinho está incompleto (faltam: {', '.join(missing_keys)}).")
                return redirect('produtos:ver_carrinho')

            image_url = request.build_absolute_uri(item_data['imagem']) if item_data['imagem'] else ''
            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'unit_amount': int(item_data['preco_unitario'] * 100),
                    'product_data': {
                        'name': item_data['nome'],
                        'images': [image_url] if image_url else [],
                    },
                },
                'quantity': item_data['quantidade'],
            })
            total_pedido_calculado += item_data['subtotal']

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao processar um item do carrinho: {e}")
            return redirect('produtos:ver_carrinho')

    # ✅ Adiciona frete, se houver
    valor_frete = request.session.get('valor_frete')
    if valor_frete:
        try:
            line_items.append({
                'price_data': {
                    'currency': 'brl',
                    'unit_amount': int(float(valor_frete) * 100),
                    'product_data': {
                        'name': 'Frete',
                    },
                },
                'quantity': 1,
            })
            total_pedido_calculado += float(valor_frete)
        except Exception as e:
            messages.warning(request, f"Erro ao adicionar o frete ao Stripe: {e}")

    if not line_items:
        messages.error(request, "Seu carrinho não contém produtos válidos.")
        return redirect('produtos:ver_carrinho')

    try:
        clientes = stripe.Customer.list(email=customer_email, limit=1)
        if clientes.data:
            customer_stripe_id = clientes.data[0].id
        else:
            customer = stripe.Customer.create(email=customer_email, name=customer_name)
            customer_stripe_id = customer.id
    except Exception as e:
        messages.error(request, f"Erro ao criar/recuperar cliente Stripe: {e}")
        return redirect('produtos:ver_carrinho')

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer=customer_stripe_id,
            success_url=request.build_absolute_uri(reverse('pagamento:compra_sucesso')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('pagamento:pagamento_cancelado')),
        )
    except Exception as e:
        messages.error(request, f"Erro ao criar sessão de checkout: {e}")
        return redirect('produtos:ver_carrinho')

    try:
        pedido = Pedido.objects.create(
            stripe_id=checkout_session.id,
            usuario=request.user if request.user.is_authenticated else None,
            email_cliente=customer_email,
            total=total_pedido_calculado,
            status='pendente'
        )
        for item_data in carrinho.values():
            Item.objects.create(
                pedido=pedido,
                produto_id_original=item_data['produto_id'],
                nome=item_data['nome'],
                preco_unitario=item_data['preco_unitario'],
                quantidade=item_data['quantidade'],
                subtotal=item_data['subtotal']
            )
        request.session['pedido_em_criacao_id'] = pedido.id
    except Exception as e:
        messages.error(request, f"Erro ao salvar o pedido: {e}")
        return redirect('produtos:ver_carrinho')

    return redirect(checkout_session.url, code=303)

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
       
            pass
        except Exception as e:
           
            return JsonResponse({'status': f'error processing event: {e}'}, status=500)

    elif event['type'] == 'payment_intent.succeeded':
        
        pass
    
    elif event['type'] == 'payment_intent.payment_failed':
        pass
    
    return JsonResponse({'status': 'success'}, status=200)



def compra_sucesso(request): 
    session_id = request.GET.get('session_id')

    if not session_id:
        messages.error(request, "ID da sessão de checkout não encontrado. Sua compra pode não ter sido concluída.")
        return redirect('produtos:home')

    try:
        pedido = get_object_or_404(Pedido, stripe_id=session_id)
        itens = pedido.itens.all() 

        if 'carrinho' in request.session:
            del request.session['carrinho']
            request.session.modified = True
 
      
        if pedido.status == 'pendente':
          
            pedido.status = 'pago'
            pedido.data_pagamento = timezone.now()
            pedido.save()
        

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


def pagamento_cancelado(request): 
    messages.info(request, "Seu pagamento foi cancelado. Você pode tentar novamente.")
    return render(request, 'pagamento/pagamento_cancelado.html') 