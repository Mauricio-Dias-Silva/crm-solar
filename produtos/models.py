from django.db import models
from django.contrib.auth.models import User

class CarouselImage(models.Model):
    image = models.ImageField(upload_to='carousel/')
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title or "Carousel Image"



class ArquivoImpressao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to='arquivos/')
    nome_item = models.CharField(max_length=100)  # Adicionar campo para nome do item
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nome_item} - {self.arquivo.name}'



from django.db import models
from django.contrib.auth.models import User # Certifique-se que User está importado

class Pedido(models.Model):
    stripe_id = models.CharField(max_length=255, unique=True, verbose_name="ID da Sessão Stripe")
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, # Se o usuário for deletado, o pedido não é deletado.
        null=True,                # Permite que o campo seja nulo (para convidados).
        blank=True,               # Permite que o campo seja vazio no formulário.
        verbose_name="Usuário"
    )
    email_cliente = models.CharField(max_length=255, blank=True, null=True, verbose_name="Email do Cliente") # Para convidados
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado Em")
    data_pagamento = models.DateTimeField(null=True, blank=True, verbose_name="Data do Pagamento") # Para registrar quando foi pago

    # Opções de Status do Pedido
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('processando', 'Processando'),
        ('enviado', 'Enviado'),
        ('cancelado', 'Cancelado'),
        ('reembolsado', 'Reembolsado'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status do Pedido"
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-criado_em'] # Ordena os pedidos mais novos primeiro

    def __str__(self):
        return f'Pedido {self.id} de {self.email_cliente or self.usuario.username}'

from django.db import models
# (Não precisa importar User aqui se já importou em Pedido e ambos estão no mesmo models.py)

class Item(models.Model):
    pedido = models.ForeignKey(
        'Pedido', # Usa string para referenciar o modelo Pedido se ele estiver no mesmo arquivo
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Pedido Relacionado"
    )
    # ID do produto no Stripe, para referência
    stripe_product_id = models.CharField(max_length=255, verbose_name="ID Produto Stripe")
    nome = models.CharField(max_length=255, verbose_name="Nome do Item") # Aumentei o max_length para nomes longos
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário") # Preço do item no momento da compra
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal do Item") # Preço unitário * quantidade

    # Se você ainda tiver o conceito de altura/largura, pode adicionar aqui:
    # altura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Altura (cm)")
    # largura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Largura (cm)")

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    def __str__(self):
        return f'{self.quantidade}x {self.nome} (Pedido: {self.pedido.id})'