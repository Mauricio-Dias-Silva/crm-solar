# Generated by Django 5.2.2 on 2025-06-13 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0002_alter_item_options_alter_pedido_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Produto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('preco', models.DecimalField(decimal_places=2, max_digits=10)),
                ('images', models.JSONField(blank=True, null=True)),
                ('categoria_id', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='carouselimage',
            name='description',
        ),
        migrations.RemoveField(
            model_name='carouselimage',
            name='title',
        ),
        migrations.AlterField(
            model_name='carouselimage',
            name='image',
            field=models.ImageField(upload_to='carousel_images/'),
        ),
    ]
