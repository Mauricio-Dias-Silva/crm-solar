# solar/urls.py
from django.urls import path, include 
from . import views
from django.shortcuts import redirect 

app_name = 'crm' 

urlpatterns = [
    # Página inicial do CRM
    path('', views.home, name='home'),

    path('login_cliente/', views.login_cliente, name='login_cliente'),
    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/cadastrar/', views.cadastrar_cliente, name='cadastrar_cliente'),
    path('clientes/<int:pk>/', views.detalhe_cliente, name='detalhe_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/excluir/', views.excluir_cliente, name='excluir_cliente'),

    # Usuários (Gestão de usuários por administradores, NÃO autenticação de login/registro)
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/novo/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/resetar_senha/', views.resetar_senha_usuario, name='resetar_senha_usuario'), # Esta view precisa ser cuidadosamente implementada para não conflitar
    path('usuarios/<int:usuario_id>/excluir/', views.excluir_usuario, name='excluir_usuario'),

    # Projetos
    path('projetos/', views.lista_projetos, name='lista_projetos'),
    path('projetos/cadastrar/', views.cadastrar_projeto, name='cadastrar_projeto'),
    path('projetos/<int:pk>/', views.detalhe_projeto, name='detalhe_projeto'),
    path('projetos/<int:pk>/cadastrar_etapa/', views.cadastrar_etapa, name='cadastrar_etapa'),
    path('projetos/dashboard/', views.dashboard_projetos, name='dashboard_projetos'),
    path('projetos/<int:pk>/editar/', views.editar_projeto, name='editar_projeto'),
    path('projetos/<int:pk>/excluir/', views.excluir_projeto, name='excluir_projeto'),
    path('projetos/<int:projeto_id>/upload_documento/', views.upload_documento_projeto, name='upload_documento_projeto'),
    path('projetos/<int:projeto_id>/excluir_documento/<int:doc_id>/', views.excluir_documento_projeto, name='excluir_documento_projeto'),

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
    path('financeiro/dashboard/', views.dashboard_financeiro, name='dashboard_financeiro'),

    # Área do Cliente (Sem login/logout próprios, usa allauth)
    path('progresso/', lambda request: redirect('crm:painel_cliente')), 
    path('progresso/', lambda request: redirect('crm:painel_cliente'), name='progresso'),
    path('cliente/painel/', views.painel_cliente, name='painel_cliente'),
   
] 