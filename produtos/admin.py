# produtos/admin.py
from django.contrib import admin
from .models import Produto, CarouselImage, Pedido, Item, ProdutoImage


# Novo: Inline para ProdutoImage
class ProdutoImageInline(admin.TabularInline):
    model = ProdutoImage
    extra = 1
    fields = ('image', 'alt_text', 'is_main')

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('name', 'preco', 'categoria_id', 'is_active', 'stock', 'created_at')
    list_filter = ('categoria_id', 'is_active')
    search_fields = ('name', 'description', 'sku')
    
    # AQUI ESTÁ A CORREÇÃO: Remova 'images' desta lista.
    fields = ('name', 'slug', 'description', 'preco', 'categoria_id', 'is_active', 'stock', 'sku')
    
    readonly_fields = ('created_at', 'updated_at')
    
    # Adicione ESTA LINHA para incluir o inline das imagens
    inlines = [ProdutoImageInline]

# ... (Seus outros registros de admin) ...

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'image') # Atualizado para mostrar o título e a imagem
    list_filter = ('is_active',)
    search_fields = ('title', 'description')

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'email_cliente', 'total', 'status', 'criado_em', 'data_pagamento')
    list_filter = ('status', 'criado_em')
    search_fields = ('id', 'email_cliente', 'stripe_id')
    readonly_fields = ('criado_em', 'data_pagamento', 'stripe_id') # Estes são preenchidos automaticamente/pelo Stripe

class ItemPedidoInline(admin.TabularInline): # Para ver os itens dentro do pedido
    model = Item
    extra = 0 # Não adiciona campos extras vazios por padrão
    readonly_fields = ('nome', 'preco_unitario', 'quantidade', 'subtotal', 'stripe_product_id')
    # Se quiser permitir edição de quantidade ou remoção aqui, remova de readonly_fields

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pedido', 'quantidade', 'preco_unitario', 'subtotal')
    list_filter = ('pedido__status',) # Filtra por status do pedido pai
    search_fields = ('nome', 'pedido__id')
