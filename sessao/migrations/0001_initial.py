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
                ('data_ordem', models.DateField()),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('numero_ordem', models.IntegerField()),
                ('txt_resultado', models.TextField(null=True, blank=True)),
                ('tipo_votacao', models.IntegerField()),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='ExpedienteSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('txt_expediente', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='MesaSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cargo', models.ForeignKey(to='parlamentares.CargoMesa')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('sessao_leg', models.ForeignKey(to='parlamentares.SessaoLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='Oradores',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_ordem', models.IntegerField()),
                ('url_discurso', models.CharField(max_length=150, null=True, blank=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
        ),
        migrations.CreateModel(
            name='OradoresExpediente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_ordem', models.IntegerField()),
                ('url_discurso', models.CharField(max_length=150, null=True, blank=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
        ),
        migrations.CreateModel(
            name='OrdemDia',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_ordem', models.DateField()),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('numero_ordem', models.IntegerField()),
                ('txt_resultado', models.TextField(null=True, blank=True)),
                ('tipo_votacao', models.IntegerField()),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='OrdemDiaPresenca',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_ordem', models.DateField()),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
        ),
        migrations.CreateModel(
            name='RegistroVotacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_votos_sim', models.IntegerField()),
                ('numero_votos_nao', models.IntegerField()),
                ('numero_abstencao', models.IntegerField()),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('ordem', models.ForeignKey(to='sessao.OrdemDia')),
            ],
        ),
        migrations.CreateModel(
            name='RegistroVotacaoParlamentar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vot_parlamentar', models.CharField(max_length=10)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('votacao', models.ForeignKey(to='sessao.RegistroVotacao')),
            ],
        ),
        migrations.CreateModel(
            name='SessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cod_andamento_sessao', models.IntegerField(null=True, blank=True)),
                ('tipo_expediente', models.CharField(max_length=10)),
                ('data_inicio_sessao', models.DateField()),
                ('dia_sessao', models.CharField(max_length=15)),
                ('hr_inicio_sessao', models.CharField(max_length=5)),
                ('hr_fim_sessao', models.CharField(max_length=5, null=True, blank=True)),
                ('numero_sessao_plen', models.IntegerField()),
                ('data_fim_sessao', models.DateField(null=True, blank=True)),
                ('url_audio', models.CharField(max_length=150, null=True, blank=True)),
                ('url_video', models.CharField(max_length=150, null=True, blank=True)),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura')),
                ('sessao_leg', models.ForeignKey(to='parlamentares.SessaoLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='SessaoPlenariaPresenca',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_sessao', models.DateField(null=True, blank=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
                ('sessao_plen', models.ForeignKey(to='sessao.SessaoPlenaria')),
            ],
        ),
        migrations.CreateModel(
            name='TipoExpediente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_expediente', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TipoResultadoVotacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_resultado', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TipoSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_sessao', models.CharField(max_length=30)),
                ('numero_minimo', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='tipo',
            field=models.ForeignKey(to='sessao.TipoSessaoPlenaria'),
        ),
        migrations.AddField(
            model_name='registrovotacao',
            name='tipo_resultado_votacao',
            field=models.ForeignKey(to='sessao.TipoResultadoVotacao'),
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
            name='expediente',
            field=models.ForeignKey(to='sessao.TipoExpediente'),
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
