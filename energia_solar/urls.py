# energia_solar/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <--- Necessário
from django.conf.urls.static import static # <--- Necessário
from solar import views as crm_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('produtos.urls', namespace='produtos')),
    path('crm/', include('solar.urls', namespace='crm')),
    path('pagamento/', include('pagamento.urls', namespace='pagamento')),
    path('accounts/', include('allauth.urls')),
    path('core/', include('core.urls', namespace='core')),
    path('redirecionamento-login/', crm_views.redirecionamento_pos_login, name='redirecionamento_pos_login'),
   
]

# 👇 ESTE BLOCO DEVE ESTAR AQUI NO SEU urls.py PRINCIPAL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Se você tem arquivos de mídia (imagens de produtos, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
