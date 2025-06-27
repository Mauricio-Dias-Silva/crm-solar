# meu_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('iniciar/', views.iniciar_pagamento, name='iniciar_pagamento'),
    path('sucesso/', views.pagamento_sucesso, name='pagamento_sucesso'),
    path('falha/', views.pagamento_falha, name='pagamento_falha'),
    path('pendente/', views.pagamento_pendente, name='pagamento_pendente'),
    path('webhook/', views.webhook_mercado_pago, name='webhook_mercado_pago'), # Nova URL
]