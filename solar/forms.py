from django import forms
from .models import Cliente, Projeto, Etapa, Material, Fornecedor, LancamentoFinanceiro, DocumentoProjeto, Usuario
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm

class ClienteForm(forms.ModelForm):
    senha_acesso_plano = forms.CharField(
        label='Senha de Acesso',
        widget=forms.PasswordInput,
        required=False,
        help_text="Preencha apenas se desejar definir ou alterar a senha."
    )
    cpf = forms.CharField(
        label='CPF',
        required=False,
        max_length=14,
    )
    cnpj = forms.CharField(
        label='CNPJ',
        required=False,
        max_length=18,
    )

    class Meta:
        model = Cliente
        fields = [
            'nome', 'email', 'telefone', 'endereco',
            'cnpj', 'cpf',
            'id_acesso', 'senha_acesso_plano',
            'possui_whatsapp'
        ]

    def clean(self):
        cleaned_data = super().clean()
        cpf = cleaned_data.get('cpf')
        cnpj = cleaned_data.get('cnpj')
        if cpf:
            cleaned_data['cpf'] = cpf.replace('.', '').replace('-', '').replace(' ', '')
            self.data = self.data.copy()
            self.data['cpf'] = cleaned_data['cpf']
        if cnpj:
            cleaned_data['cnpj'] = cnpj.replace('.', '').replace('/', '').replace('-', '').replace(' ', '')
            self.data = self.data.copy()
            self.data['cnpj'] = cleaned_data['cnpj']

        id_acesso = cleaned_data.get('id_acesso')
        senha = cleaned_data.get('senha_acesso_plano')

        if id_acesso and not senha and not self.instance.pk:
            raise ValidationError("Para novo cliente, o campo 'Senha de Acesso' é obrigatório.")

        if not cleaned_data.get('cpf') and not cleaned_data.get('cnpj'):
            raise ValidationError("Preencha CPF ou CNPJ.")

        return cleaned_data

    def save(self, commit=True):
        cliente = super().save(commit=False)
        senha = self.cleaned_data.get('senha_acesso_plano')

        if senha:
            cliente.set_senha_acesso(senha)

        if commit:
            cliente.save()
        return cliente

# ---------------------- CRUD DE USUÁRIOS ----------------------

class UsuarioCreateForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2'
        )

class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = (
            'username', 'first_name', 'last_name', 'email'
        )

# Para reset de senha use SetPasswordForm padrão do Django

# --------------------------------------------------------------

class ProjetoForm(forms.ModelForm):
    data_inicio = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'})
    )
    data_fim = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'}),
        required=False
    )

    class Meta:
        model = Projeto
        fields = '__all__'

class DocumentoProjetoForm(forms.ModelForm):
    class Meta:
        model = DocumentoProjeto
        fields = ['nome', 'arquivo', 'visivel_cliente']

class EtapaForm(forms.ModelForm):
    data_inicio = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'})
    )
    data_fim = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'}),
        required=False
    )

    class Meta:
        model = Etapa
        exclude = ['projeto']

class MaterialForm(forms.ModelForm):
    garantia_ate = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'}),
        required=False
    )
    data_entrada = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'}),
        required=False
    )

    class Meta:
        model = Material
        fields = '__all__'

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = '__all__'

class LancamentoFinanceiroForm(forms.ModelForm):
    data = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa', 'type': 'text'})
    )

    class Meta:
        model = LancamentoFinanceiro
        fields = '__all__'
