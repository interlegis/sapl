# Generated by Django 2.2.28 on 2022-10-19 23:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comissoes', '0028_auto_20220807_2257'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reuniao',
            options={'ordering': ('-data', '-nome'), 'verbose_name': 'Reunião de Comissão', 'verbose_name_plural': 'Reuniões de Comissão'},
        ),
    ]
