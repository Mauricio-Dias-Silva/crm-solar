import re
from django.core.exceptions import ValidationError
from django.db import models

# Função para validar o CNPJ
def validar_cnpj(cnpj):
    cnpj_pattern = re.compile(r'^\d{14}$')  # Verifica se o CNPJ tem 14 dígitos numéricos
    if not cnpj_pattern.match(cnpj):
        raise ValidationError("CNPJ inválido. O campo CNPJ deve conter exatamente 14 dígitos numéricos.")
    return cnpj

# Função para validar o telefone
def validar_telefone(telefone):
    telefone_pattern = re.compile(r'^\d{10,11}$')  # Telefone com 10 ou 11 dígitos
    if not telefone_pattern.match(telefone):
        raise ValidationError("Telefone inválido. O campo Telefone deve conter entre 10 e 11 dígitos numéricos.")
    return telefone

# Função para validar o CPF (caso precise adicionar essa validação)
def validar_cpf(cpf):
    cpf_pattern = re.compile(r'^\d{11}$')  # Verifica se o CPF tem 11 dígitos numéricos
    if not cpf_pattern.match(cpf):
        raise ValidationError("CPF inválido. O campo CPF deve conter exatamente 11 dígitos numéricos.")
    return cpf

class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, validators=[validar_telefone])  # Validação do telefone
    endereco = models.TextField()
    cnpj = models.CharField(max_length=18, unique=True, null=True, blank=True, validators=[validar_cnpj])  # Validação do CNPJ
    cpf = models.CharField(max_length=11, null=True, blank=True, validators=[validar_cpf])  # Validação do CPF
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Projeto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)  # Adicione este campo se necessário
    status = models.CharField(max_length=50, choices=[('Em andamento', 'Em andamento'), ('Concluído', 'Concluído')])  # Adicione este campo se necessário
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)

    def __str__(self):
        return self.nome
