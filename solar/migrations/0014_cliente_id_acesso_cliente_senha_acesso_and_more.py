# Generated by Django 5.2.1 on 2025-05-29 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solar', '0013_acessocliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='id_acesso',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='cliente',
            name='senha_acesso',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.DeleteModel(
            name='AcessoCliente',
        ),
    ]
