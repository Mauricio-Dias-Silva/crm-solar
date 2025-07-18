from django.contrib import admin
from .models import SiteProject

@admin.register(SiteProject)
class SiteProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'published_url')
    search_fields = ('name', 'user__username', 'original_prompt')
    list_filter = ('created_at',)