from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telefone = forms.CharField(max_length=20, required=False)
    cpf = forms.CharField(max_length=14, required=False, label="CPF")
    rua = forms.CharField(max_length=200, required=False, label="Rua")
    numero = forms.CharField(max_length=20, required=False, label="Número")
    cep = forms.CharField(max_length=10, required=False, label="CEP")
    cidade = forms.CharField(max_length=100, required=False, label="Cidade")
    estado = forms.CharField(max_length=2, required=False, label="UF (Estado)")
    possui_whatsapp = forms.BooleanField(
        required=False,
        label="Possui WhatsApp?",
        widget=forms.CheckboxInput()
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "telefone",
            "cpf",
            "rua",
            "numero",
            "cep",
            "cidade",
            "estado",
            "possui_whatsapp",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()

            # Criação automática do Cliente no app solar
            try:
                from solar.models import Cliente
                nome_completo = f"{user.first_name} {user.last_name}".strip() or user.username
                id_acesso = get_random_string(length=12)
                senha_acesso = get_random_string(length=8)

                cliente = Cliente.objects.create(
                    nome=nome_completo,
                    email=user.email,
                    telefone=self.cleaned_data.get("telefone"),
                    cpf=self.cleaned_data.get("cpf", ""),
                    possui_whatsapp=self.cleaned_data.get("possui_whatsapp", False),
                    rua=self.cleaned_data.get("rua", ""),
                    numero=self.cleaned_data.get("numero", ""),
                    cep=self.cleaned_data.get("cep", ""),
                    cidade=self.cleaned_data.get("cidade", ""),
                    estado=self.cleaned_data.get("estado", ""),
                    id_acesso=id_acesso,
                )
                cliente.set_senha_acesso(senha_acesso)
                cliente.save()

            except Exception as e:
                print(f"[ERRO AO CRIAR CLIENTE NO SOLAR] {e}")

        return user
