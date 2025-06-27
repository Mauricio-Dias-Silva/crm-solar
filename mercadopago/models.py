# # pagamentos_mp/models.py
# from django.db import models

# # IMPORTANTE: Importe o modelo Pedido do seu APP DE LOJA explicitamente
# # Substitua 'nome_do_seu_app_de_loja' pelo nome real do seu app de pedidos/loja
# from pagamento.models import PedidoMP as PedidoOriginalDaLoja


# class PedidoMP(models.Model): # RENOMEADO para evitar conflito com PedidoOriginalDaLoja
#     """
#     Este modelo representa o pedido do ponto de vista do Mercado Pago,
#     associado a um pedido original da sua loja.
#     """
#     id_mercado_pago = models.CharField(max_length=255, unique=True, null=True, blank=True)
#     status = models.CharField(max_length=50, default='pendente') # Status do pagamento MP
#     valor = models.DecimalField(max_digits=10, decimal_places=2)
#     data_criacao = models.DateTimeField(auto_now_add=True)

#     # Adicione a chave estrangeira para o seu Pedido original da loja
#     pedido_original = models.ForeignKey(PedidoOriginalDaLoja, on_delete=models.CASCADE,
#                                         related_name='pagamentos_mp')
#     # O related_name permite acessar os pagamentos_mp a partir de um objeto PedidoOriginalDaLoja

#     def __str__(self):
#         return f"Pagamento MP - ID: {self.id_mercado_pago} - Status: {self.status}"

# # Se você precisar de uma classe Pagamento separada para detalhes do pagamento em si
# # (além do status do "pedido" do MP)
# class TransacaoPagamentoMP(models.Model): # Exemplo de nome mais específico
#     """
#     Este modelo pode armazenar detalhes mais específicos da transação do Mercado Pago,
#     se você não quiser poluir o PedidoMP.
#     """
#     pedido_mp = models.ForeignKey(PedidoMP, on_delete=models.CASCADE, related_name='transacoes')
#     tipo_pagamento = models.CharField(max_length=50) # Ex: 'credit_card', 'boleto'
#     valor_liquido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     data_pagamento = models.DateTimeField(null=True, blank=True)
#     # ... outros campos relevantes da transação real do MP

#     def __str__(self):
#         return f"Transação MP para Pedido {self.pedido_mp.id} - Tipo: {self.tipo_pagamento}"