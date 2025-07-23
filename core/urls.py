# core/urls.py
from django.urls import path
from . import views

app_name = 'core' # <--- ADICIONE ESTA LINHA AQUI!

urlpatterns = [
    path('', views.home_view, name='home'), # Página inicial da GayaSites
    path('criar-site/', views.create_site_view, name='create_site'), # Gerar novo site
    path('meus-sites/', views.my_sites_view, name='my_sites'),     # Listar sites criados
    path('editar-site/<int:project_id>/', views.edit_site_view, name='edit_site'), # Editar site específico
    path('preview-site/<int:project_id>/', views.preview_site_ajax, name='preview_site_ajax'), # Pré-visualização via AJAX
    path('download-site/<int:project_id>/', views.download_site_view, name='download_site'), # Baixar HTML
    path('publicar-site/<int:project_id>/', views.publish_site_view, name='publish_site'), # Publicar (em standby Docker)
    path('publicado/<int:project_id>/', views.view_published_site, name='view_published_site'), # Ver site publicado
    path('contato/', views.contact_view, name='contact'),       # Página de contato
]