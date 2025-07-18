from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # path('', views.home_view, name='home'), # Remova ou comente se crm:home é a única home
    path('criar-site/', views.create_site_view, name='create_site'),
    path('meus-sites/', views.my_sites_view, name='my_sites'),
    path('editar-site/<int:project_id>/', views.edit_site_view, name='edit_site'),
    path('preview-site/<int:project_id>/', views.preview_site_ajax, name='preview_site_ajax'),
    path('download-site/<int:project_id>/', views.download_site_view, name='download_site'),
    path('publicar-site/<int:project_id>/', views.publish_site_view, name='publish_site'),
    path('publicado/<int:project_id>/', views.view_published_site, name='view_published_site'),
    # path('contato/', views.contact_view, name='contact'), # Remova ou comente esta linha
]