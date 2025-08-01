# Generated by Django 5.2.4 on 2025-07-10 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='siteproject',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='siteproject',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='siteproject',
            name='published_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
