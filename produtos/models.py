# produtos/models.py

from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User # Para ArquivoImpressao e Pedido
from django.conf import settings # Para ForeignKey de User em Pedido

# === SEUS MODELOS EXISTENTES ===

class CarouselImage(models.Model):
    image = models.ImageField(upload_to='carousel/')
    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title or "Carousel Image"


class Pedido(models.Model):
    stripe_id = models.CharField(max_length=255, unique=True, verbose_name="ID da Sessão Stripe")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Usar settings.AUTH_USER_MODEL é mais seguro
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário"
    )
    email_cliente = models.CharField(max_length=255, blank=True, null=True, verbose_name="Email do Cliente")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado Em")
    data_pagamento = models.DateTimeField(null=True, blank=True, verbose_name="Data do Pagamento")

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
        ordering = ['-criado_em']

    def __str__(self):
        return f'Pedido {self.id} de {self.email_cliente or (self.usuario.username if self.usuario else "Convidado")}'



class Item(models.Model):
    pedido = models.ForeignKey(
        'Pedido',
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Pedido Relacionado"
    )
    # ID do produto no Stripe, para referência
    stripe_product_id = models.CharField(max_length=255, verbose_name="ID Produto Stripe")
    
    # <<< AQUI ESTÁ A CORREÇÃO: ADICIONE ESTE CAMPO >>>
    produto_id_original = models.IntegerField(
        verbose_name="ID do Produto Original (Django)", 
        null=True, 
        blank=True
    )
    # Use IntegerField para IDs de PK do Django. 
    # null=True, blank=True permite que o campo seja nulo/vazio.

    nome = models.CharField(max_length=255, verbose_name="Nome do Item")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário")
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal do Item")

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    def __str__(self):
        return f'{self.quantidade}x {self.nome} (Pedido: {self.pedido.id})'

# ... (outros modelos) ...


# === SEU MODELO PRODUTO ATUALIZADO ===

class Produto(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome do Produto")
    description = models.TextField(blank=True, verbose_name="Descrição")
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    
    # REMOVEMOS O JSONField 'images' AQUI

    categoria_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID da Categoria (URL-friendly)")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Slug (URL Amigável)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado Em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    stock = models.IntegerField(default=0, verbose_name="Estoque")
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="SKU (Código do Produto)")

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Produto.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def categoria_exibicao(self):
        if self.categoria_id:
            return self.categoria_id.replace('_', ' ').title()
        return "Sem Categoria"

# === NOVO MODELO PARA IMAGENS DE PRODUTO ===

class ProdutoImage(models.Model):
    # Foreign Key para o Produto. related_name='images' permite acessar produto.images.all()
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='produtos/') # Onde as imagens dos produtos serão salvas
    alt_text = models.CharField(max_length=255, blank=True, null=True, verbose_name="Texto Alternativo")
    is_main = models.BooleanField(default=False, verbose_name="Imagem Principal")

    class Meta:
        verbose_name = "Imagem do Produto"
        verbose_name_plural = "Imagens do Produto"
        ordering = ['-is_main', 'id'] # Garante que a principal apareça primeiro

    def __str__(self):
        return f"Imagem para {self.produto.name} ({self.id})"