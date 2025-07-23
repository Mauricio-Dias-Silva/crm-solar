# core/models.py
from django.db import models
from django.contrib.auth.models import User

# IMPORTAR O MODELO CLIENTE DO SEU APP SOLAR
# Ajuste o 'solar.models' se o seu app de clientes tiver outro nome
try:
    from solar.models import Cliente 
except ImportError:
    # Fallback para caso o modelo Cliente não exista (ex: em um projeto de teste sem o CRM)
    # Isso é apenas para evitar erros durante o makemigrations em um projeto simples.
    class Cliente(models.Model):
        nome = models.CharField(max_length=255)
        # Adicione outros campos necessários aqui se precisar para evitar erros
        def __str__(self):
            return self.nome


class SiteProject(models.Model):
    # O usuário que criou o projeto do site
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gaya_site_projects')
    
    # Opcional: Linka o SiteProject a um cliente específico do seu CRM
    # Se o cliente for excluído, este campo será SET_NULL.
    cliente_associado = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='site_projects' 
    )

    name = models.CharField(max_length=255, default="Novo Site")
    original_prompt = models.TextField() # O prompt que o usuário usou para gerar
    base_html_code = models.TextField() # O HTML gerado pela IA (com ou sem atributos editáveis)
    content_data = models.JSONField(default=dict) # Dados preenchidos pelo usuário (chave:placeholder, valor:conteudo)
    final_html_code = models.TextField(blank=True, null=True) # O HTML final após injetar content_data
    published_url = models.URLField(max_length=500, blank=True, null=True) # URL onde o site está publicado
    created_at = models.DateTimeField(auto_now_add=True) # Data de criação
    updated_at = models.DateTimeField(auto_now=True) # Data da última atualização

    def __str__(self):
        return f"{self.name} (Usuário: {self.user.username})"

    class Meta:
        ordering = ['-created_at'] # Ordena os sites pelo mais recente primeiro