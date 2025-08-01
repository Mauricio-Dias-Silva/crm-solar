# Generated by Django 5.2.4 on 2025-07-14 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0006_item_produto_id_original_delete_arquivoimpressao'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegiaoFrete',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefixo_cep', models.CharField(max_length=3, unique=True, verbose_name='Prefixo do CEP')),
                ('cidade', models.CharField(max_length=100)),
                ('valor_frete', models.DecimalField(decimal_places=2, max_digits=7)),
                ('prazo_entrega', models.PositiveIntegerField(verbose_name='Prazo (dias úteis)')),
            ],
        ),
    ]
