# Generated by Django 5.2 on 2025-04-23 01:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0007_remove_cliente_cargo_responsavel_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cliente',
            name='bairro',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='canal_comunicacao',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='cep',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='cidade',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='complemento',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='data_nascimento',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='estado',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='numero',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='observacoes',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='sexo',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='tipo_cliente',
        ),
    ]
