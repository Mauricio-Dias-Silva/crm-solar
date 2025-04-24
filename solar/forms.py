from django import forms
from .models import Projeto, Cliente
from django.core.exceptions import ValidationError

class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['nome', 'descricao', 'data_inicio', 'data_fim', 'status', 'cliente']

    def __init__(self, *args, **kwargs):
        super(ProjetoForm, self).__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all()  # Personaliza a lista de clientes

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'cnpj', 'endereco', 'telefone']
        error_messages = {
            'nome': {'required': 'O nome do cliente é obrigatório.'},
            'cnpj': {'required': 'O CNPJ é obrigatório.'},
            'endereco': {'required': 'O endereço é obrigatório.'},
            'telefone': {'required': 'O telefone é obrigatório.'},
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data['cnpj']
        if len(cnpj) != 14:
            raise ValidationError("CNPJ inválido. O CNPJ deve ter 14 dígitos.")
        return cnpj