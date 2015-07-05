# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpedienteMateria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_ordem', models.DateField(verbose_name='Data da Sess\xe3o')),
                ('observacao', models.TextField(null=True, verbose_name='Ementa', blank=True)),
                ('numero_ordem', models.IntegerField(verbose_name='N\xba Ordem')),
                ('resultado', models.TextField(null=True, blank=True)),
                ('tipo_votacao', models.IntegerField(verbose_name='Tipo de vota\xe7\xe3o')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Mat\xe9ria do Expediente',
                'verbose_name_plural': 'Mat\xe9rias do Expediente',
            },
        ),
        migrations.CreateModel(
            name='ExpedienteSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('expediente', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Expediente de Sess\xe3o Plenaria',
                'verbose_name_plural': 'Expedientes de Sess\xe3o Plenaria',
            },
        ),
        migrations.CreateModel(
            name='MesaSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cargo', models.ForeignKey(to='parlamentares.CargoMesa')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('sessao_leg', models.ForeignKey(to='parlamentares.SessaoLegislativa')),
            ],
            options={
                'verbose_name': 'Mesa de Sess\xe3o Plenaria',
                'verbose_name_plural': 'Mesas de Sess\xe3o Plenaria',
            },
        ),
        migrations.CreateModel(
            name='Oradores',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_ordem', models.IntegerField(verbose_name='Ordem de pronunciamento')),
                ('url_discurso', models.CharField(max_length=150, null=True, verbose_name='URL V\xeddeo', blank=True)),
                ('parlamentar', models.ForeignKey(verbose_name='Parlamentar', to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Orador das Explica\xe7\xf5es Pessoais',
                'verbose_name_plural': 'Oradores das Explica\xe7\xf5es Pessoais',
            },
        ),
        migrations.CreateModel(
            name='OradoresExpediente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_ordem', models.IntegerField(verbose_name='Ordem de pronunciamento')),
                ('url_discurso', models.CharField(max_length=150, null=True, verbose_name='URL V\xeddeo', blank=True)),
                ('parlamentar', models.ForeignKey(verbose_name='Parlamentar', to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Orador do Expediente',
                'verbose_name_plural': 'Oradores do Expediente',
            },
        ),
        migrations.CreateModel(
            name='OrdemDia',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_ordem', models.DateField(verbose_name='Data da Sess\xe3o')),
                ('observacao', models.TextField(null=True, verbose_name='Ementa', blank=True)),
                ('numero_ordem', models.IntegerField(verbose_name='N\xba Ordem')),
                ('resultado', models.TextField(null=True, blank=True)),
                ('tipo_votacao', models.IntegerField(verbose_name='Tipo de vota\xe7\xe3o')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Mat\xe9ria da Ordem do Dia',
                'verbose_name_plural': 'Mat\xe9rias da Ordem do Dia',
            },
        ),
        migrations.CreateModel(
            name='OrdemDiaPresenca',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_ordem', models.DateField()),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Presen\xe7a da Ordem do Dia',
                'verbose_name_plural': 'Presen\xe7as da Ordem do Dia',
            },
        ),
        migrations.CreateModel(
            name='RegistroVotacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_votos_sim', models.IntegerField(verbose_name='Sim:')),
                ('numero_votos_nao', models.IntegerField(verbose_name='N\xe3o:')),
                ('numero_abstencao', models.IntegerField(verbose_name='Absten\xe7\xf5es:')),
                ('observacao', models.TextField(null=True, verbose_name='Observa\xe7\xf5es', blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('ordem', models.ForeignKey(to='sessao.OrdemDia')),
            ],
            options={
                'verbose_name': 'Vota\xe7\xe3o',
                'verbose_name_plural': 'Vota\xe7\xf5es',
            },
        ),
        migrations.CreateModel(
            name='RegistroVotacaoParlamentar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vot_parlamentar', models.CharField(max_length=10)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('votacao', models.ForeignKey(to='sessao.RegistroVotacao')),
            ],
            options={
                'verbose_name': 'Registro de Vota\xe7\xe3o de Parlamentar',
                'verbose_name_plural': 'Registros de Vota\xe7\xf5es de Parlamentares',
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cod_andamento_sessao', models.IntegerField(null=True, blank=True)),
                ('tipo_expediente', models.CharField(max_length=10)),
                ('data_inicio_sessao', models.DateField(verbose_name='Abertura')),
                ('dia_sessao', models.CharField(max_length=15)),
                ('hr_inicio_sessao', models.CharField(max_length=5, verbose_name='Hor\xe1rio')),
                ('hr_fim_sessao', models.CharField(max_length=5, null=True, verbose_name='Hor\xe1rio', blank=True)),
                ('numero_sessao_plen', models.IntegerField(verbose_name='N\xfamero')),
                ('data_fim_sessao', models.DateField(null=True, verbose_name='Encerramento', blank=True)),
                ('url_audio', models.CharField(max_length=150, null=True, verbose_name='URL Arquivo \xc1udio (Formatos MP3 / AAC)', blank=True)),
                ('url_video', models.CharField(max_length=150, null=True, verbose_name='URL Arquivo V\xeddeo (Formatos MP4 / FLV / WebM)', blank=True)),
                ('legislatura', models.ForeignKey(verbose_name='Legislatura', to='parlamentares.Legislatura')),
                ('sessao_leg', models.ForeignKey(verbose_name='Sess\xe3o Legislativa', to='parlamentares.SessaoLegislativa')),
            ],
            options={
                'verbose_name': 'Sess\xe3o Plen\xe1ria',
                'verbose_name_plural': 'Sess\xf5es Plen\xe1rias',
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenariaPresenca',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_sessao', models.DateField(null=True, blank=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('sessao_plen', models.ForeignKey(to='sessao.SessaoPlenaria')),
            ],
            options={
                'verbose_name': 'Presen\xe7a em Sess\xe3o Plen\xe1ria',
                'verbose_name_plural': 'Presen\xe7as em Sess\xf5es Plen\xe1rias',
            },
        ),
        migrations.CreateModel(
            name='TipoExpediente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_expediente', models.CharField(max_length=100, verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Tipo de Expediente',
                'verbose_name_plural': 'Tipos de Expediente',
            },
        ),
        migrations.CreateModel(
            name='TipoResultadoVotacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_resultado', models.CharField(max_length=100, verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Tipo de Resultado de Vota\xe7\xe3o',
                'verbose_name_plural': 'Tipos de Resultado de Vota\xe7\xe3o',
            },
        ),
        migrations.CreateModel(
            name='TipoSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_sessao', models.CharField(max_length=30, verbose_name='Tipo')),
                ('numero_minimo', models.IntegerField(verbose_name='Qu\xf3rum m\xednimo')),
            ],
            options={
                'verbose_name': 'Tipo de Sess\xe3o Plen\xe1ria',
                'verbose_name_plural': 'Tipos de Sess\xe3o Plen\xe1ria',
            },
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo', to='sessao.TipoSessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='registrovotacao',
            name='tipo_resultado_votacao',
            field=models.ForeignKey(verbose_name='Resultado da Vota\xe7\xe3o', to='sessao.TipoResultadoVotacao'),
        ),
        migrations.AddField(
            model_name='ordemdiapresenca',
            name='sessao_plen',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='ordemdia',
            name='sessao_plen',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='oradoresexpediente',
            name='sessao_plen',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='oradores',
            name='sessao_plen',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='mesasessaoplenaria',
            name='sessao_plen',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='expedientesessaoplenaria',
            name='sessao_plen',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='expedientemateria',
            name='sessao_plen',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
    ]
