# Generated by Django 2.2.28 on 2022-09-19 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0052_auto_20220914_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appconfig',
            name='sapl_as_sapn',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Utilizar SAPL apenas como SAPL-Normas?'),
        ),
    ]
