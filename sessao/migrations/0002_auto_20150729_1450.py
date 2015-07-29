# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessaoplenaria',
            name='dia',
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='finalizada',
            field=models.NullBooleanField(verbose_name='Sessão finalizada?', choices=[(True, 'Sim'), (False, 'Não')]),
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='iniciada',
            field=models.NullBooleanField(verbose_name='Sessão iniciada?', choices=[(True, 'Sim'), (False, 'Não')]),
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='upload_ata',
            field=models.FileField(verbose_name='Ata da Sessão', null=True, upload_to='', blank=True),
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='upload_pauta',
            field=models.FileField(verbose_name='Pauta da Sessão', null=True, upload_to='', blank=True),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='hora_fim',
            field=models.CharField(verbose_name='Horário (hh:mm)', null=True, max_length=5, blank=True),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='hora_inicio',
            field=models.CharField(verbose_name='Horário (hh:mm)', max_length=5),
        ),
    ]
