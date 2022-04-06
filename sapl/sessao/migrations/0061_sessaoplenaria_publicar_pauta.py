# Generated by Django 2.2.24 on 2022-04-05 16:07

from django.db import migrations, models

from sapl.utils import YES_NO_CHOICES


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0060_auto_20220224_1245'),
    ]

    operations = [
        migrations.AddField(
            model_name='sessaoplenaria',
            name='publicar_pauta',
            field=models.BooleanField(blank=True, default=False, null=True, choices=YES_NO_CHOICES, verbose_name='Publicar Pauta?'),
        ),
    ]