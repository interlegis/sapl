# Generated by Django 2.2.13 on 2021-03-03 17:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0033_auto_20210103_1015'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bloco',
            options={'ordering': ('nome',), 'verbose_name': 'Bloco Parlamentar', 'verbose_name_plural': 'Blocos Parlamentares'},
        ),
    ]