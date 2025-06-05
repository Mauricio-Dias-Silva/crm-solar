from django.test import TestCase, Client
from django.urls import reverse
from produtos.models import Produto
from django.core.files.uploadedfile import SimpleUploadedFile

class ProdutoDetalheViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.produto_metro_quadrado = Produto.objects.create(
            nome="Produto por Metro Quadrado",
            preco=10.00,
            tipo="metro_quadrado",
            imagem=SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg"),
        )
        self.produto_unitario = Produto.objects.create(
            nome="Produto Unitário",
            preco=5.00,
            tipo="unitario",
            imagem=SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg"),

        )


    def test_produto_detalhe_metro_quadrado(self):
        response = self.client.get(reverse('produto_detalhe', args=[self.produto_metro_quadrado.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'produtos/produto_detalhe.html')
        self.assertContains(response, "Produto por Metro Quadrado")
        self.assertContains(response, "Altura (em centímetros)")
        self.assertContains(response, "Largura (em centímetros)")


    def test_produto_detalhe_unitario(self):
        response = self.client.get(reverse('produto_detalhe', args=[self.produto_unitario.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'produtos/produto_detalhe.html')
        self.assertContains(response, "Produto Unitário")
        self.assertNotContains(response, "Altura (em centímetros)")
        self.assertNotContains(response, "Largura (em centímetros)")


    def test_calcular_preco_js_metro_quadrado(self):
        # This test only checks that the template renders the javascript correctly.
        # It doesn't execute the Javascript.  True JS testing would require a different approach (e.g., Selenium).
        response = self.client.get(reverse('produto_detalhe', args=[self.produto_metro_quadrado.id]))
        self.assertContains(response, "function calcularPreco()")
        self.assertContains(response, "alturaM * larguraM * precoUnitario * quantidade")


    def test_adicionar_ao_carrinho_metro_quadrado(self):
        data = {'altura': '100', 'largura': '200', 'quantidade': '1'}
        response = self.client.post(reverse('adicionar_ao_carrinho', args=[self.produto_metro_quadrado.id]), data=data)
        # Check redirect.  302 is the standard redirect code. You might also consider following the redirect with client.follow.
        self.assertEqual(response.status_code, 302)


    def test_adicionar_ao_carrinho_unitario(self):
        data = {'quantidade': '2'}  # Just quantity needed for unitario products
        response = self.client.post(reverse('adicionar_ao_carrinho', args=[self.produto_unitario.id]), data=data)
        self.assertEqual(response.status_code, 302)



