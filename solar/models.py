import re
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

def validar_cnpj(cnpj):
    cnpj_pattern = re.compile(r'^\d{14}$')
    if not cnpj_pattern.match(cnpj):
        raise ValidationError("CNPJ inválido. O campo CNPJ deve conter exatamente 14 dígitos numéricos.")
    return cnpj

def validar_telefone(telefone):
    telefone_pattern = re.compile(r'^\d{10,11}$')
    if not telefone_pattern.match(telefone):
        raise ValidationError("Telefone inválido. O campo Telefone deve conter entre 10 e 11 dígitos numéricos.")
    return telefone

def validar_cpf(cpf):
    cpf_pattern = re.compile(r'^\d{11}$')
    if not cpf_pattern.match(cpf):
        raise ValidationError("CPF inválido. O campo CPF deve conter exatamente 11 dígitos numéricos.")
    return cpf

class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, validators=[validar_telefone])
    endereco = models.TextField()
    cnpj = models.CharField(max_length=18, unique=True, null=True, blank=True, validators=[validar_cnpj])
    cpf = models.CharField(max_length=11, null=True, blank=True, validators=[validar_cpf])
    data_cadastro = models.DateTimeField(auto_now_add=True)

    id_acesso = models.CharField(max_length=20, unique=True, null=True, blank=True)
    senha_acesso = models.CharField(max_length=128, null=True, blank=True)

    def set_senha_acesso(self, senha_plana):
        self.senha_acesso = make_password(senha_plana)

    def verificar_senha_acesso(self, senha):
        return check_password(senha, self.senha_acesso)

    def __str__(self):
        return self.nome

class Projeto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[('Em andamento', 'Em andamento'), ('Concluído', 'Concluído')])
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

class Etapa(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='etapas')
    nome = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return f'{self.nome} ({self.projeto.nome})'

class Material(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    unidade_medida = models.CharField(max_length=20, choices=[
        ('un', 'Unidade'),
        ('m', 'Metro'),
        ('kg', 'Quilo'),
        ('l', 'Litro')
    ])
    quantidade_estoque = models.DecimalField(max_digits=10, decimal_places=2)
    fabricante = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nome

class Fornecedor(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18, validators=[validar_cnpj])
    telefone = models.CharField(max_length=20, validators=[validar_telefone])
    email = models.EmailField(blank=True)
    endereco = models.TextField(blank=True)

    def __str__(self):
        return self.nome

class LancamentoFinanceiro(models.Model):
    TIPOS = [
        ('recebimento', 'Recebimento'),
        ('pagamento', 'Pagamento'),
    ]
    STATUS = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
    ]

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='lancamentos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS)

    def __str__(self):
        return f'{self.tipo.title()} - {self.valor} ({self.projeto.nome})'
