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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True, related_name='cliente_profile')
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, validators=[validar_telefone])
    
    # Novo formato de endereço
    rua = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True)

    cnpj = models.CharField(max_length=18, unique=True, null=True, blank=True, validators=[validar_cnpj])
    cpf = models.CharField(max_length=11, unique=True, null=True, blank=True, validators=[validar_cpf])
    possui_whatsapp = models.BooleanField(default=False)

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
    descricao = models.TextField(blank=True, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
        ('Em andamento', 'Em andamento'), 
        ('Concluído', 'Concluído'),
        ('Aguardando aprovação', 'Aguardando aprovação'),
        ('Cancelado', 'Cancelado'),
    ])
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    endereco_instalacao = models.TextField(blank=True, null=True)
    potencia_kwp = models.DecimalField('Potência (kWp)', max_digits=6, decimal_places=2, null=True, blank=True)
    quantidade_modulos = models.PositiveIntegerField('Quantidade de Módulos', null=True, blank=True)
    inversor = models.CharField('Modelo do Inversor', max_length=100, blank=True, null=True)
    fornecedor = models.ForeignKey('Fornecedor', on_delete=models.SET_NULL, null=True, blank=True)
    valor_total = models.DecimalField('Valor Total (R$)', max_digits=12, decimal_places=2, null=True, blank=True)
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nome

class DocumentoProjeto(models.Model):
    projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE, related_name='documentos')
    nome = models.CharField('Nome do Documento', max_length=200)
    arquivo = models.FileField('Arquivo', upload_to='projetos/%Y/%m/%d/')
    data_upload = models.DateTimeField(auto_now_add=True)
    visivel_cliente = models.BooleanField('Visível para o cliente?', default=False)

    def __str__(self):
        return f'{self.nome} ({self.projeto.nome})'
    
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
    codigo = models.CharField(max_length=50, blank=True, null=True)
    fabricante = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=50, blank=True, null=True)
    numero_serie = models.CharField(max_length=50, blank=True, null=True)
    unidade_medida = models.CharField(max_length=20)
    quantidade_estoque = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    localizacao = models.CharField(max_length=100, blank=True, null=True)
    preco_compra = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    garantia_ate = models.DateField(blank=True, null=True)
    data_entrada = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    
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

# =============== MODELOS DE USUÁRIO, DEPARTAMENTO, MENU =================

from django.contrib.auth.models import AbstractUser, Group, Permission

class Departamento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nome

class MenuPermissao(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    rota = models.CharField(max_length=100, help_text="Exemplo: /clientes/ ou nome da URL Django")
    def __str__(self):
        return self.nome

class Usuario(AbstractUser):
    departamento = models.ForeignKey('Departamento', on_delete=models.SET_NULL, null=True, blank=True)
    permissoes_menu = models.ManyToManyField('MenuPermissao', blank=True)

    # Estes campos mantêm compatibilidade com grupos/permissões Django Admin
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="usuario_set",  # nome único
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="usuario_set",  # nome único
        related_query_name="usuario",
    )

    def __str__(self):
        return self.get_full_name() or self.username