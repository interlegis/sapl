# Generated by Django 2.2.28 on 2023-05-29 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0041_parlamentar_telefone_celular'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parlamentar',
            name='telefone_celular',
            field=models.CharField(blank=True, max_length=50, verbose_name='Telefone Celular'),
        ),
    ]
