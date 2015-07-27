# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpedienteMateria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_ordem', models.DateField(verbose_name='Data da Sessão')),
                ('observacao', models.TextField(blank=True, verbose_name='Ementa', null=True)),
                ('numero_ordem', models.IntegerField(verbose_name='Nº Ordem')),
                ('resultado', models.TextField(blank=True, null=True)),
                ('tipo_votacao', models.IntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], verbose_name='Tipo de votação')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Matéria do Expediente',
                'verbose_name_plural': 'Matérias do Expediente',
            },
        ),
        migrations.CreateModel(
            name='ExpedienteSessao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('conteudo', models.TextField(blank=True, verbose_name='Conteúdo do expediente', null=True)),
            ],
            options={
                'verbose_name': 'Expediente de Sessão Plenaria',
                'verbose_name_plural': 'Expedientes de Sessão Plenaria',
            },
        ),
        migrations.CreateModel(
            name='IntegranteMesa',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('cargo', models.ForeignKey(to='parlamentares.CargoMesa')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Participação em Mesa de Sessão Plenaria',
                'verbose_name_plural': 'Participações em Mesas de Sessão Plenaria',
            },
        ),
        migrations.CreateModel(
            name='Orador',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero_ordem', models.IntegerField(verbose_name='Ordem de pronunciamento')),
                ('url_discurso', models.CharField(max_length=150, blank=True, verbose_name='URL Vídeo', null=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name': 'Orador das Explicações Pessoais',
                'verbose_name_plural': 'Oradores das Explicações Pessoais',
            },
        ),
        migrations.CreateModel(
            name='OradorExpediente',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero_ordem', models.IntegerField(verbose_name='Ordem de pronunciamento')),
                ('url_discurso', models.CharField(max_length=150, blank=True, verbose_name='URL Vídeo', null=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name': 'Orador do Expediente',
                'verbose_name_plural': 'Oradores do Expediente',
            },
        ),
        migrations.CreateModel(
            name='OrdemDia',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_ordem', models.DateField(verbose_name='Data da Sessão')),
                ('observacao', models.TextField(blank=True, verbose_name='Ementa', null=True)),
                ('numero_ordem', models.IntegerField(verbose_name='Nº Ordem')),
                ('resultado', models.TextField(blank=True, null=True)),
                ('tipo_votacao', models.IntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], verbose_name='Tipo de votação')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Matéria da Ordem do Dia',
                'verbose_name_plural': 'Matérias da Ordem do Dia',
            },
        ),
        migrations.CreateModel(
            name='PresencaOrdemDia',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_ordem', models.DateField()),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Presença da Ordem do Dia',
                'verbose_name_plural': 'Presenças da Ordem do Dia',
            },
        ),
        migrations.CreateModel(
            name='RegistroVotacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero_votos_sim', models.IntegerField(verbose_name='Sim')),
                ('numero_votos_nao', models.IntegerField(verbose_name='Não')),
                ('numero_abstencoes', models.IntegerField(verbose_name='Abstenções')),
                ('observacao', models.TextField(blank=True, verbose_name='Observações', null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('ordem', models.ForeignKey(to='sessao.OrdemDia')),
            ],
            options={
                'verbose_name': 'Votação',
                'verbose_name_plural': 'Votações',
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenaria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('cod_andamento_sessao', models.IntegerField(blank=True, null=True)),
                ('tipo_expediente', models.CharField(max_length=10)),
                ('data_inicio', models.DateField(verbose_name='Abertura')),
                ('dia', models.CharField(max_length=15)),
                ('hora_inicio', models.CharField(max_length=5, verbose_name='Horário')),
                ('hora_fim', models.CharField(max_length=5, blank=True, verbose_name='Horário', null=True)),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('data_fim', models.DateField(blank=True, verbose_name='Encerramento', null=True)),
                ('url_audio', models.CharField(max_length=150, blank=True, verbose_name='URL Arquivo Áudio (Formatos MP3 / AAC)', null=True)),
                ('url_video', models.CharField(max_length=150, blank=True, verbose_name='URL Arquivo Vídeo (Formatos MP4 / FLV / WebM)', null=True)),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura', verbose_name='Legislatura')),
                ('sessao_legislativa', models.ForeignKey(to='parlamentares.SessaoLegislativa', verbose_name='Sessão Legislativa')),
            ],
            options={
                'verbose_name': 'Sessão Plenária',
                'verbose_name_plural': 'Sessões Plenárias',
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenariaPresenca',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_sessao', models.DateField(blank=True, null=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('sessao_plen', models.ForeignKey(to='sessao.SessaoPlenaria')),
            ],
            options={
                'verbose_name': 'Presença em Sessão Plenária',
                'verbose_name_plural': 'Presenças em Sessões Plenárias',
            },
        ),
        migrations.CreateModel(
            name='TipoExpediente',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Tipo de Expediente',
                'verbose_name_plural': 'Tipos de Expediente',
            },
        ),
        migrations.CreateModel(
            name='TipoResultadoVotacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Tipo')),
            ],
            options={
                'verbose_name': 'Tipo de Resultado de Votação',
                'verbose_name_plural': 'Tipos de Resultado de Votação',
            },
        ),
        migrations.CreateModel(
            name='TipoSessaoPlenaria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=30, verbose_name='Tipo')),
                ('quorum_minimo', models.IntegerField(verbose_name='Quórum mínimo')),
            ],
            options={
                'verbose_name': 'Tipo de Sessão Plenária',
                'verbose_name_plural': 'Tipos de Sessão Plenária',
            },
        ),
        migrations.CreateModel(
            name='VotoParlamentar',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('voto', models.CharField(max_length=10)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('votacao', models.ForeignKey(to='sessao.RegistroVotacao')),
            ],
            options={
                'verbose_name': 'Registro de Votação de Parlamentar',
                'verbose_name_plural': 'Registros de Votações de Parlamentares',
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
