from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.shortcuts import redirect

urlpatterns = [
    # Login
    path('login/', views.login_view, name='login'),

    # Página inicial
    path('', views.home, name='home'),

    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/cadastrar/', views.cadastrar_cliente, name='cadastrar_cliente'),
    path('clientes/<int:pk>/', views.detalhe_cliente, name='detalhe_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/excluir/', views.excluir_cliente, name='excluir_cliente'),

    # Projetos
    path('projetos/', views.lista_projetos, name='lista_projetos'),
    path('projetos/cadastrar/', views.cadastrar_projeto, name='cadastrar_projeto'),
    path('projetos/<int:pk>/', views.detalhe_projeto, name='detalhe_projeto'),
    path('projetos/<int:pk>/cadastrar_etapa/', views.cadastrar_etapa, name='cadastrar_etapa'),
    path('projetos/dashboard/', views.dashboard_projetos, name='dashboard_projetos'),
    
    # Materiais
    path('materiais/', views.lista_materiais, name='lista_materiais'),
    path('materiais/cadastrar/', views.cadastrar_material, name='cadastrar_material'),
    path('materiais/<int:pk>/editar/', views.editar_material, name='editar_material'),


    # Fornecedores
    path('fornecedores/', views.lista_fornecedores, name='lista_fornecedores'),
    path('fornecedores/cadastrar/', views.cadastrar_fornecedor, name='cadastrar_fornecedor'),
    path('fornecedores/<int:pk>/editar/', views.editar_fornecedor, name='editar_fornecedor'),

    # Financeiro
    path('financeiro/', views.lista_financeiro, name='lista_financeiro'),
    path('financeiro/cadastrar/', views.cadastrar_lancamento, name='cadastrar_lancamento'),

    #Dashboard Financeiro
    path('financeiro/dashboard/', views.dashboard_financeiro, name='dashboard_financeiro'),

    # Área do Cliente
    path('progresso/', lambda request: redirect('login_cliente')),  # redireciona se acessar apenas /cliente/
    path('progresso/login/', views.login_cliente, name='login_cliente'),
    path('progresso/logout/', views.logout_cliente, name='logout_cliente'),
    path('progresso/painel/', views.painel_cliente, name='painel_cliente'),

    # Logout (opcional, usando view padrão do Django)
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
