from django.contrib import admin
from django.http import HttpResponse, HttpResponseNotFound
from .models import ArquivoImpressao, CarouselImage
import os
import mimetypes

def download_arquivo(modeladmin, request, queryset):
    if queryset.count() == 1:
        arquivo = queryset.first()
        filepath = arquivo.arquivo.path
        
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                mime_type, _ = mimetypes.guess_type(filepath)
                response = HttpResponse(f, content_type=mime_type)
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(filepath)}'
                return response
        else:
            return HttpResponseNotFound('Arquivo não encontrado.')
    else:
        return HttpResponse('Por favor, selecione apenas um arquivo para baixar de cada vez.')

download_arquivo.short_description = "Download Arquivo Selecionado"

@admin.register(ArquivoImpressao)
class ArquivoImpressaoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'arquivo', 'criado_em']
    actions = [download_arquivo]


admin.site.register(CarouselImage)

