# energia_solar/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # <--- Necessário
from django.conf.urls.static import static # <--- Necessário

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('produtos.urls')),
    path('crm/', include('solar.urls')),
    path('accounts/', include('allauth.urls')),
]

# 👇 ESTE BLOCO DEVE ESTAR AQUI NO SEU urls.py PRINCIPAL
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Se você tem arquivos de mídia (imagens de produtos, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)