from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

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

    # Logout (opcional, usando view padrão do Django)
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
