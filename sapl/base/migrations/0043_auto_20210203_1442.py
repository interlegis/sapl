# Generated by Django 2.2.13 on 2021-02-03 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0042_auto_20201013_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='appconfig',
            name='google_recaptcha_secret_key',
            field=models.CharField(default='', max_length=256, verbose_name='Chave privada gerada pelo Google Recaptcha'),
        ),
        migrations.AddField(
            model_name='appconfig',
            name='google_recaptcha_site_key',
            field=models.CharField(default='', max_length=256, verbose_name='Chave pública gerada pelo Google Recaptcha'),
        ),
    ]
