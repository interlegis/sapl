# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0012_auto_20160120_1237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expedientemateria',
            name='observacao',
            field=models.TextField(verbose_name='Ementa', blank=True),
        ),
        migrations.AlterField(
            model_name='expedientemateria',
            name='resultado',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='expedientesessao',
            name='conteudo',
            field=models.TextField(verbose_name='Conteúdo do expediente', blank=True),
        ),
        migrations.AlterField(
            model_name='orador',
            name='url_discurso',
            field=models.CharField(verbose_name='URL Vídeo', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='oradorexpediente',
            name='url_discurso',
            field=models.CharField(verbose_name='URL Vídeo', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='ordemdia',
            name='observacao',
            field=models.TextField(verbose_name='Ementa', blank=True),
        ),
        migrations.AlterField(
            model_name='ordemdia',
            name='resultado',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='registrovotacao',
            name='observacao',
            field=models.TextField(verbose_name='Observações', blank=True),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='hora_fim',
            field=models.CharField(verbose_name='Horário (hh:mm)', max_length=5, blank=True),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='url_audio',
            field=models.CharField(verbose_name='URL Arquivo Áudio (Formatos MP3 / AAC)', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='url_video',
            field=models.CharField(verbose_name='URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)', max_length=150, blank=True),
        ),
    ]
