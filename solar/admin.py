from django.contrib import admin
from .models import Cliente, Projeto

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'telefone', 'id_acesso')
    search_fields = ('nome', 'email', 'id_acesso')
    readonly_fields = ('senha_acesso',)
    fields = (
        'nome',
        'email',
        'telefone',
        'endereco',
        'cnpj',
        'cpf',
        'id_acesso',
        'senha_acesso',  # hash só para visualização (readonly)
    )

    def save_model(self, request, obj, form, change):
        """
        Se o campo senha_acesso tiver um valor claro (não hashado),
        ele será hashado corretamente.
        """
        if 'senha_acesso' in form.changed_data:
            raw_password = form.cleaned_data['senha_acesso']
            obj.set_senha_acesso(raw_password)
        super().save_model(request, obj, form, change)

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'status', 'data_inicio', 'data_fim')
    list_filter = ('status',)
    search_fields = ('nome', 'cliente__nome')
