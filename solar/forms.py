from django import forms
from .models import Cliente, Projeto, Etapa, Material, Fornecedor, LancamentoFinanceiro
from django.core.exceptions import ValidationError

class ClienteForm(forms.ModelForm):
    senha_acesso_plano = forms.CharField(
        label='Senha de Acesso',
        widget=forms.PasswordInput,
        required=False,
        help_text="Preencha apenas se desejar definir ou alterar a senha."
    )

    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone', 'endereco', 'cnpj', 'cpf', 'id_acesso', 'senha_acesso_plano']

    def clean(self):
        cleaned_data = super().clean()
        id_acesso = cleaned_data.get('id_acesso')
        senha = cleaned_data.get('senha_acesso_plano')

        if id_acesso and not senha and not self.instance.pk:
            raise ValidationError("Para novo cliente, o campo 'Senha de Acesso' é obrigatório.")

    def save(self, commit=True):
        cliente = super().save(commit=False)
        senha = self.cleaned_data.get('senha_acesso_plano')

        if senha:
            cliente.set_senha_acesso(senha)

        if commit:
            cliente.save()
        return cliente

class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = '__all__'

class EtapaForm(forms.ModelForm):
    class Meta:
        model = Etapa
        fields = '__all__'

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = '__all__'

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = '__all__'

class LancamentoFinanceiroForm(forms.ModelForm):
    class Meta:
        model = LancamentoFinanceiro
        fields = '__all__'
