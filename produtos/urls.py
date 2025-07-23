# produtos/urls.py
from django.urls import path
from . import views
# Remova: from django.contrib.auth import views as auth_views - Não precisamos dela aqui.

app_name = 'produtos'

urlpatterns = [
    # URLs Gerais e de Navegação
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'), # Mantenha apenas uma ocorrência de search

    # URLs de Produtos e Categorias
    path('produto/<int:produto_id>/', views.produto_detalhe, name='produto_detalhe'),
    path('categoria/<slug:categoria_slug>/', views.produtos_por_categoria, name='produtos_por_categoria'),
    path('produto/<int:produto_id>/frete/', views.calcular_frete, name='calcular_frete'),
    path('lista/', views.lista_produtos, name='lista_produtos'),
    
    # URLs de Gestão de Produto (Adicionar, Modificar, Excluir)
    path('adicionar/', views.adicionar_produto, name='adicionar_produto'), 
    path('<int:produto_id>/modificar/', views.modificar_produto, name='modificar_produto'),
    path('<int:produto_id>/excluir/', views.excluir_produto, name='excluir_produto'),

    # URLs de Carrinho
    path('ver_carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('adicionar_ao_carrinho/<int:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('remover_do_carrinho/<int:produto_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
    path('calcular_frete_carrinho/', views.calcular_frete_carrinho, name='calcular_frete_carrinho'),

    
    path('politica-de-privacidade/', views.politica_privacidade, name='politica_privacidade'),
    path('termos-de-servico/', views.termos_de_servico, name='termos_de_servico'), # <--- ESTA LINHA

]