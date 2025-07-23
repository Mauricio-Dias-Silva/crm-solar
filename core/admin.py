# core/admin.py
from django.contrib import admin
from .models import SiteProject

@admin.register(SiteProject)
class SiteProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'cliente_associado', 'created_at', 'published_url')
    search_fields = ('name', 'user__username', 'original_prompt', 'cliente_associado__nome') # Adicionado busca por nome do cliente
    list_filter = ('created_at', 'user', 'cliente_associado') # Adicionado filtro por cliente