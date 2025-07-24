# solar/urls.py
from django.urls import path # Não precisamos de include aqui, pois estamos no próprio app
from . import views


app_name = 'solar'

urlpatterns = [
    # Página inicial do CRM (para a equipe)
    # A URL raiz do app CRM (ex: /crm/) levará à home da equipe.
    path('', views.home, name='home'),

    # Clientes (Gestão de clientes para a equipe do CRM)
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/cadastrar/', views.cadastrar_cliente, name='cadastrar_cliente'),
    path('clientes/<int:pk>/', views.detalhe_cliente, name='detalhe_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/excluir/', views.excluir_cliente, name='excluir_cliente'),

    # Usuários (Gestão de usuários internos por administradores)
    # Estas URLs gerenciam o modelo Usuario, que é o User do Django.
    # Elas não são para o fluxo de login/registro/logout do usuário final,
    # que será tratado pelo Allauth.
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/novo/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/resetar_senha/', views.resetar_senha_usuario, name='resetar_senha_usuario'),
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

    # Área do Cliente (Agora que o login/logout é via Allauth)
    # A view 'painel_cliente' será acessada diretamente após o redirecionamento pós-login.
    # Se 'progresso/' é um atalho, mantenha apenas uma delas.
    path('progresso/', views.painel_cliente, name='progresso'), # Redireciona diretamente para painel_cliente
    path('cliente/painel/', views.painel_cliente, name='painel_cliente'),
]