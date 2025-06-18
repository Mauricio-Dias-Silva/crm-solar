# meu_app/views.py
from django.shortcuts import render, redirect
import mercadopago # Exemplo: SDK do Mercado Pago


def pagina_pagamento(request):
    # Lógica para criar a preferência de pagamento com Mercado Pago
    # Exemplo (simplificado):
    # sdk = mercadopago.SDK("SEU_ACCESS_TOKEN")
    # preference = sdk.preference().create({"items": [{"title": "Produto", "quantity": 1, "unit_price": 100}]})
    # init_point = preference["response"]["init_point"]
    # return redirect(init_point) # Redireciona para o Mercado Pago

    context = {'mensagem': 'Esta é a página de pagamento.'}
    return render(request, 'meu_app/pagamento.html', context)


def iniciar_pagamento(request):
    # Lógica para criar a preferência de pagamento (como no exemplo anterior)
    sdk = mercadopago.SDK("SEU_ACCESS_TOKEN")
    preference_data = {
        "items": [{"title": "Serviço X", "quantity": 1, "unit_price": 250.00}],
        "back_urls": {
            "success": "https://seuapp.com/pagar/sucesso/",
            "failure": "https://seuapp.com/pagar/falha/",
            "pending": "https://seuapp.com/pagar/pendente/"
        },
        "auto_return": "approved_only"
    }
    preference_response = sdk.preference().create(preference_data)
    init_point = None
    if preference_response["status"] == 201: # 201 Created
        init_point = preference_response["response"]["init_point"]
        # Você pode optar por redirecionar diretamente ou mostrar a página intermediária
        # return redirect(init_point)

    context = {
        'valor_total': 250.00, # Exemplo
        'init_point': init_point,
    }
    return render(request, 'meu_app/pagina_pagamento.html', context)

# Views para as URLs de retorno (sucesso, falha, pendente)
def pagamento_sucesso(request):
    return render(request, 'meu_app/pagamento_sucesso.html')

def pagamento_falha(request):
    return render(request, 'meu_app/pagamento_falha.html')

def pagamento_pendente(request):
    return render(request, 'meu_app/pagamento_pendente.html')

# meu_app/views.py (exemplo)
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt # Importante: Webhooks são POST externos, então desabilite o CSRF para este endpoint
def webhook_mercado_pago(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic') # Ex: 'payment' ou 'merchant_order'
            resource_id = data.get('id') # ID do pagamento ou da ordem
            logger.info(f"Webhook recebido - Topic: {topic}, ID: {resource_id}")

            if topic == 'payment':
                # Aqui você chamaria a API do Mercado Pago para buscar os detalhes do pagamento
                # sdk = mercadopago.SDK("SEU_ACCESS_TOKEN")
                # payment_info = sdk.payment().get(resource_id)
                # if payment_info["status"] == 200:
                #     status_pagamento = payment_info["response"]["status"]
                #     # Atualize o status do seu modelo Pedido no banco de dados
                #     pedido = Pedido.objects.get(id_mercado_pago=resource_id)
                #     pedido.status = status_pagamento
                #     pedido.save()
                #     logger.info(f"Pagamento {resource_id} atualizado para status: {status_pagamento}")

            # Retorne 200 OK para o Mercado Pago, indicando que você recebeu a notificação
            return HttpResponse(status=200)
        except json.JSONDecodeError:
            logger.error("Erro ao decodificar JSON do webhook.")
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f"Erro no webhook: {e}")
            return HttpResponse(status=500)
    return HttpResponse(status=405) # Método não permitido para GET