# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0014_autoria_partido'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autor',
            name='cargo',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='autor',
            name='nome',
            field=models.CharField(verbose_name='Autor', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='autor',
            name='username',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='documentoacessorio',
            name='autor',
            field=models.CharField(verbose_name='Autor', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='documentoacessorio',
            name='ementa',
            field=models.TextField(verbose_name='Ementa', blank=True),
        ),
        migrations.AlterField(
            model_name='documentoacessorio',
            name='indexacao',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='apelido',
            field=models.CharField(verbose_name='Apelido', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='indexacao',
            field=models.TextField(verbose_name='Indexação', blank=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='numero_origem_externa',
            field=models.CharField(verbose_name='Número', max_length=5, blank=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='objeto',
            field=models.CharField(verbose_name='Objeto', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='observacao',
            field=models.TextField(verbose_name='Observação', blank=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='resultado',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='tipo_apresentacao',
            field=models.CharField(blank=True, verbose_name='Tipo de Apresentação', choices=[('O', 'Oral'), ('E', 'Escrita')], max_length=1),
        ),
        migrations.AlterField(
            model_name='numeracao',
            name='data_materia',
            field=models.DateField(verbose_name='Data', blank=True),
        ),
        migrations.AlterField(
            model_name='orgao',
            name='endereco',
            field=models.CharField(verbose_name='Endereço', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='orgao',
            name='telefone',
            field=models.CharField(verbose_name='Telefone', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='parecer',
            name='parecer',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='parecer',
            name='tipo_conclusao',
            field=models.CharField(max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='proposicao',
            name='justificativa_devolucao',
            field=models.CharField(verbose_name='Justificativa da Devolução', max_length=200, blank=True),
        ),
        migrations.AlterField(
            model_name='proposicao',
            name='status',
            field=models.CharField(blank=True, verbose_name='Status Proposição', choices=[('E', 'Enviada'), ('D', 'Devolvida'), ('I', 'Incorporada')], max_length=1),
        ),
        migrations.AlterField(
            model_name='tramitacao',
            name='texto',
            field=models.TextField(verbose_name='Texto da Ação', blank=True),
        ),
        migrations.AlterField(
            model_name='tramitacao',
            name='turno',
            field=models.CharField(blank=True, verbose_name='Turno', choices=[('P', 'Primeiro'), ('S', 'Segundo'), ('Ú', 'Único'), ('L', 'Suplementar'), ('F', 'Final'), ('A', 'Votação única em Regime de Urgência'), ('B', '1ª Votação'), ('C', '2ª e 3ª Votação')], max_length=1),
        ),
    ]
