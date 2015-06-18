# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CargoComissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50)),
                ('unico', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Comissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_comissao', models.CharField(max_length=60)),
                ('sigla_comissao', models.CharField(max_length=10)),
                ('data_criacao', models.DateField()),
                ('data_extincao', models.DateField(null=True, blank=True)),
                ('nome_apelido_temp', models.CharField(max_length=100, null=True, blank=True)),
                ('data_instalacao_temp', models.DateField(null=True, blank=True)),
                ('data_final_prevista_temp', models.DateField(null=True, blank=True)),
                ('data_prorrogada_temp', models.DateField(null=True, blank=True)),
                ('data_fim_comissao', models.DateField(null=True, blank=True)),
                ('nome_secretario', models.CharField(max_length=30, null=True, blank=True)),
                ('numero_tel_reuniao', models.CharField(max_length=15, null=True, blank=True)),
                ('endereco_secretaria', models.CharField(max_length=100, null=True, blank=True)),
                ('numero_tel_secretaria', models.CharField(max_length=15, null=True, blank=True)),
                ('numero_fax_secretaria', models.CharField(max_length=15, null=True, blank=True)),
                ('descricao_agenda_reuniao', models.CharField(max_length=100, null=True, blank=True)),
                ('local_reuniao', models.CharField(max_length=100, null=True, blank=True)),
                ('txt_finalidade', models.TextField(null=True, blank=True)),
                ('endereco_email', models.CharField(max_length=100, null=True, blank=True)),
                ('unid_deliberativa', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='ComposicaoComissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('titular', models.BooleanField()),
                ('data_designacao', models.DateField()),
                ('data_desligamento', models.DateField(null=True, blank=True)),
                ('descricao_motivo_desligamento', models.CharField(max_length=150, null=True, blank=True)),
                ('obs_composicao', models.CharField(max_length=150, null=True, blank=True)),
                ('cargo', models.ForeignKey(to='comissoes.CargoComissao')),
                ('comissao', models.ForeignKey(to='comissoes.Comissao')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
        ),
        migrations.CreateModel(
            name='PeriodoCompComissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_inicio_periodo', models.DateField()),
                ('data_fim_periodo', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TipoComissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_tipo_comissao', models.CharField(max_length=50)),
                ('sigla_natureza_comissao', models.CharField(max_length=1)),
                ('sigla_tipo_comissao', models.CharField(max_length=10)),
                ('descricao_dispositivo_regimental', models.CharField(max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='composicaocomissao',
            name='periodo_comp',
            field=models.ForeignKey(to='comissoes.PeriodoCompComissao'),
        ),
        migrations.AddField(
            model_name='comissao',
            name='tipo_comissao',
            field=models.ForeignKey(to='comissoes.TipoComissao'),
        ),
    ]
