from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ArquivoImpressao

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class ArquivoImpressaoForm(forms.ModelForm):
    class Meta:
        model = ArquivoImpressao
        fields = ['arquivo']

    def save(self, commit=True, *args, **kwargs):
        instance = super().save(commit=False)
        if 'usuario' in kwargs:
            instance.usuario = kwargs['usuario']
        if commit:
            instance.save()
        return instance


