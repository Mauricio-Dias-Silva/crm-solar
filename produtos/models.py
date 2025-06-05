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



class Pedido(models.Model):
    stripe_id = models.CharField(max_length=255, unique=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pedido {self.id} de {self.usuario.username}'

class Item(models.Model):
    nome = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField()
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')

    def __str__(self):
        return self.nome

