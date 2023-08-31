# Generated by Django 2.2.28 on 2023-08-29 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0057_appconfig_google_analytics_id_metrica'),
    ]

    operations = [
        migrations.AddField(
            model_name='appconfig',
            name='ordem_sequencia_regimental',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Ordem da Matéria pela Sequência Regimental?'),
        ),
    ]
