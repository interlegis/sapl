# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0001_initial'),
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpedienteMateria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_ordem', models.DateField(verbose_name='Data da Sessão')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Ementa')),
                ('numero_ordem', models.IntegerField(verbose_name='Nº Ordem')),
                ('resultado', models.TextField(blank=True, null=True)),
                ('tipo_votacao', models.IntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], verbose_name='Tipo de votação')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name_plural': 'Matérias do Expediente',
                'verbose_name': 'Matéria do Expediente',
            },
        ),
        migrations.CreateModel(
            name='ExpedienteSessao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('conteudo', models.TextField(blank=True, null=True, verbose_name='Conteúdo do expediente')),
            ],
            options={
                'verbose_name_plural': 'Expedientes de Sessão Plenaria',
                'verbose_name': 'Expediente de Sessão Plenaria',
            },
        ),
        migrations.CreateModel(
            name='IntegranteMesa',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('cargo', models.ForeignKey(to='parlamentares.CargoMesa')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name_plural': 'Participações em Mesas de Sessão Plenaria',
                'verbose_name': 'Participação em Mesa de Sessão Plenaria',
            },
        ),
        migrations.CreateModel(
            name='Orador',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero_ordem', models.IntegerField(verbose_name='Ordem de pronunciamento')),
                ('url_discurso', models.CharField(blank=True, max_length=150, null=True, verbose_name='URL Vídeo')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name_plural': 'Oradores das Explicações Pessoais',
                'verbose_name': 'Orador das Explicações Pessoais',
            },
        ),
        migrations.CreateModel(
            name='OradorExpediente',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero_ordem', models.IntegerField(verbose_name='Ordem de pronunciamento')),
                ('url_discurso', models.CharField(blank=True, max_length=150, null=True, verbose_name='URL Vídeo')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name_plural': 'Oradores do Expediente',
                'verbose_name': 'Orador do Expediente',
            },
        ),
        migrations.CreateModel(
            name='OrdemDia',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_ordem', models.DateField(verbose_name='Data da Sessão')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Ementa')),
                ('numero_ordem', models.IntegerField(verbose_name='Nº Ordem')),
                ('resultado', models.TextField(blank=True, null=True)),
                ('tipo_votacao', models.IntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], verbose_name='Tipo de votação')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name_plural': 'Matérias da Ordem do Dia',
                'verbose_name': 'Matéria da Ordem do Dia',
            },
        ),
        migrations.CreateModel(
            name='PresencaOrdemDia',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_ordem', models.DateField()),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name_plural': 'Presenças da Ordem do Dia',
                'verbose_name': 'Presença da Ordem do Dia',
            },
        ),
        migrations.CreateModel(
            name='RegistroVotacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero_votos_sim', models.IntegerField(verbose_name='Sim')),
                ('numero_votos_nao', models.IntegerField(verbose_name='Não')),
                ('numero_abstencoes', models.IntegerField(verbose_name='Abstenções')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('ordem', models.ForeignKey(to='sessao.OrdemDia')),
            ],
            options={
                'verbose_name_plural': 'Votações',
                'verbose_name': 'Votação',
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenaria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('cod_andamento_sessao', models.IntegerField(blank=True, null=True)),
                ('tipo_expediente', models.CharField(max_length=10)),
                ('data_inicio', models.DateField(verbose_name='Abertura')),
                ('dia', models.CharField(max_length=15)),
                ('hora_inicio', models.CharField(max_length=5, verbose_name='Horário')),
                ('hora_fim', models.CharField(blank=True, max_length=5, null=True, verbose_name='Horário')),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('data_fim', models.DateField(blank=True, null=True, verbose_name='Encerramento')),
                ('url_audio', models.CharField(blank=True, max_length=150, null=True, verbose_name='URL Arquivo Áudio (Formatos MP3 / AAC)')),
                ('url_video', models.CharField(blank=True, max_length=150, null=True, verbose_name='URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)')),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura', verbose_name='Legislatura')),
                ('sessao_legislativa', models.ForeignKey(to='parlamentares.SessaoLegislativa', verbose_name='Sessão Legislativa')),
            ],
            options={
                'verbose_name_plural': 'Sessões Plenárias',
                'verbose_name': 'Sessão Plenária',
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenariaPresenca',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_sessao', models.DateField(blank=True, null=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('sessao_plen', models.ForeignKey(to='sessao.SessaoPlenaria')),
            ],
            options={
                'verbose_name_plural': 'Presenças em Sessões Plenárias',
                'verbose_name': 'Presença em Sessão Plenária',
            },
        ),
        migrations.CreateModel(
            name='TipoExpediente',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=100, verbose_name='Tipo')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Expediente',
                'verbose_name': 'Tipo de Expediente',
            },
        ),
        migrations.CreateModel(
            name='TipoResultadoVotacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=100, verbose_name='Tipo')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Resultado de Votação',
                'verbose_name': 'Tipo de Resultado de Votação',
            },
        ),
        migrations.CreateModel(
            name='TipoSessaoPlenaria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=30, verbose_name='Tipo')),
                ('quorum_minimo', models.IntegerField(verbose_name='Quórum mínimo')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Sessão Plenária',
                'verbose_name': 'Tipo de Sessão Plenária',
            },
        ),
        migrations.CreateModel(
            name='VotoParlamentar',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('voto', models.CharField(max_length=10)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('votacao', models.ForeignKey(to='sessao.RegistroVotacao')),
            ],
            options={
                'verbose_name_plural': 'Registros de Votações de Parlamentares',
                'verbose_name': 'Registro de Votação de Parlamentar',
            },
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='tipo',
            field=models.ForeignKey(to='sessao.TipoSessaoPlenaria', verbose_name='Tipo'),
        ),
        migrations.AddField(
            model_name='registrovotacao',
            name='tipo_resultado_votacao',
            field=models.ForeignKey(to='sessao.TipoResultadoVotacao', verbose_name='Resultado da Votação'),
        ),
        migrations.AddField(
            model_name='presencaordemdia',
            name='sessao_plenaria',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='ordemdia',
            name='sessao_plenaria',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='oradorexpediente',
            name='sessao_plenaria',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='orador',
            name='sessao_plenaria',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='integrantemesa',
            name='sessao_plenaria',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='expedientesessao',
            name='sessao_plenaria',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='expedientesessao',
            name='tipo',
            field=models.ForeignKey(to='sessao.TipoExpediente'),
        ),
        migrations.AddField(
            model_name='expedientemateria',
            name='sessao_plenaria',
            field=models.ForeignKey(to='sessao.SessaoPlenaria'),
        ),
    ]
