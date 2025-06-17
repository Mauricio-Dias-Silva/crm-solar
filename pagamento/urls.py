from django.urls import path
from . import views

app_name = 'pagamento'

urlpatterns = [
    path('criar-checkout-session/', views.criar_checkout_session, name='criar_checkout_session'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('pagamento/sucesso/', views.compra_sucesso, name='compra_sucesso'), 
    path('pagamento/cancelado/', views.pagamento_cancelado, name='pagamento_cancelado'),
]


  