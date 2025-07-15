# produtos/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'produtos'

urlpatterns = [
    # URLs Gerais e de Navegação
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'), # Se search for buscar nos produtos locais

    # URLs de Produtos e Categorias
    path('produto/<int:produto_id>/', views.produto_detalhe, name='produto_detalhe'), # Usa int:produto_id e nome 'produto_detalhe'
    path('categoria/<slug:categoria_slug>/', views.produtos_por_categoria, name='produtos_por_categoria'),
    path('produto/<int:produto_id>/frete/', views.calcular_frete, name='calcular_frete'),
    path('lista/', views.lista_produtos, name='lista_produtos'),
    # URLs de Autenticação (Django Auth Views)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='produtos:home'), name='logout'), # next_page com namespace
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('search/', views.search, name='search'),
    path('register/', views.register, name='register'), # Sua view de registro

    # URLs de Políticas e Termos
    path('politica-de-privacidade/', views.politica_privacidade, name='politica_privacidade'),
    path('termos-de-servico/', views.termos_de_servico, name='termos_de_servico'),

    # URLs de Carrinho
    path('ver_carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('adicionar_ao_carrinho/<int:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('remover_do_carrinho/<int:produto_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
    path('calcular_frete_carrinho/', views.calcular_frete_carrinho, name='calcular_frete_carrinho'),
    path('adicionar/', views.adicionar_produto, name='adicionar_produto'), # <-- This line is crucial!


    path('adicionar/', views.adicionar_produto, name='adicionar_produto'),
    path('<int:produto_id>/modificar/', views.modificar_produto, name='modificar_produto'),
    path('<int:produto_id>/excluir/', views.excluir_produto, name='excluir_produto'), # <--- Adicione esta URL (se ainda não tiver)


    # OLD/REMOVIDAS (COMENTADAS, CASO PRECISE LEMBRAR)
    # path('finalizar_compra/', views.finalizar_compra, name='finalizar_compra'), # Esta view foi incorporada em criar_checkout_session
    # path('compra_sucesso/', views.success, name='compra_sucesso'), # Movido para app pagamento
    # path('success/', views.success, name='success'), # Removido (duplicado)
    # path('cancel/', views.cancel, name='cancel'), # Movido para app pagamento
    # path('criar-checkout-session/', views.criar_checkout_session, name='criar_checkout_session'), # Movido para app pagamento
    # path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'), # Movido para app pagamento
]
