# Generated by Django 5.2 on 2025-04-22 23:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0006_cliente_bairro_cliente_canal_comunicacao_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cliente',
            name='cargo_responsavel',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='cpf_responsavel',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='forma_pagamento',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='historico_compras',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='interesses',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='nome_responsavel',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='ramo_atividade',
        ),
    ]
