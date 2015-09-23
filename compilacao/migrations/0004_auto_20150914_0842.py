# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0003_auto_20150911_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_pai',
            field=models.ForeignKey(to='compilacao.Dispositivo', verbose_name='Dispositivo Pai', blank=True, related_name='dispositivos_filhos_set', null=True, default=None),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='norma',
            field=models.ForeignKey(related_name='dispositivos_set', to='norma.NormaJuridica', verbose_name='Norma Jurídica'),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='norma_publicada',
            field=models.ForeignKey(to='norma.NormaJuridica', verbose_name='Norma Jurídica Publicada', blank=True, related_name='dispositivos_alterados_pela_norma_set', null=True, default=None),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='tipo_dispositivo',
            field=models.ForeignKey(related_name='dispositivos_do_tipo_set', to='compilacao.TipoDispositivo', verbose_name='Tipo do Dispositivo'),
        ),
    ]
