# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CargoMesa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50)),
                ('unico', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Coligacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_coligacao', models.CharField(max_length=50)),
                ('numero_votos_coligacao', models.IntegerField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ComposicaoColigacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('coligacao', models.ForeignKey(to='parlamentares.Coligacao')),
            ],
        ),
        migrations.CreateModel(
            name='ComposicaoMesa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cargo', models.ForeignKey(to='parlamentares.CargoMesa')),
            ],
        ),
        migrations.CreateModel(
            name='Dependente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_dependente', models.CharField(max_length=50)),
                ('sexo', models.CharField(max_length=1)),
                ('data_nascimento', models.DateField(null=True, blank=True)),
                ('numero_cpf', models.CharField(max_length=14, null=True, blank=True)),
                ('numero_rg', models.CharField(max_length=15, null=True, blank=True)),
                ('numero_tit_eleitor', models.CharField(max_length=15, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Filiacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_filiacao', models.DateField()),
                ('data_desfiliacao', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Legislatura',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_inicio', models.DateField()),
                ('data_fim', models.DateField()),
                ('data_eleicao', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Localidade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_localidade', models.CharField(max_length=50, null=True, blank=True)),
                ('nome_localidade_pesq', models.CharField(max_length=50, null=True, blank=True)),
                ('tipo_localidade', models.CharField(max_length=1, null=True, blank=True)),
                ('sigla_uf', models.CharField(max_length=2, null=True, blank=True)),
                ('sigla_regiao', models.CharField(max_length=2, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Mandato',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_causa_fim_mandato', models.IntegerField(null=True, blank=True)),
                ('data_fim_mandato', models.DateField(null=True, blank=True)),
                ('numero_votos_recebidos', models.IntegerField(null=True, blank=True)),
                ('data_expedicao_diploma', models.DateField(null=True, blank=True)),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('coligacao', models.ForeignKey(blank=True, to='parlamentares.Coligacao', null=True)),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura')),
            ],
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nivel_instrucao', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Parlamentar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_completo', models.CharField(max_length=50)),
                ('nome_parlamentar', models.CharField(max_length=50, null=True, blank=True)),
                ('sexo', models.CharField(max_length=1)),
                ('data_nascimento', models.DateField(null=True, blank=True)),
                ('numero_cpf', models.CharField(max_length=14, null=True, blank=True)),
                ('numero_rg', models.CharField(max_length=15, null=True, blank=True)),
                ('numero_tit_eleitor', models.CharField(max_length=15, null=True, blank=True)),
                ('cod_casa', models.IntegerField()),
                ('numero_gab_parlamentar', models.CharField(max_length=10, null=True, blank=True)),
                ('numero_tel_parlamentar', models.CharField(max_length=50, null=True, blank=True)),
                ('numero_fax_parlamentar', models.CharField(max_length=50, null=True, blank=True)),
                ('endereco_residencial', models.CharField(max_length=100, null=True, blank=True)),
                ('numero_cep_resid', models.CharField(max_length=9, null=True, blank=True)),
                ('numero_tel_resid', models.CharField(max_length=50, null=True, blank=True)),
                ('numero_fax_resid', models.CharField(max_length=50, null=True, blank=True)),
                ('endereco_web', models.CharField(max_length=100, null=True, blank=True)),
                ('nome_profissao', models.CharField(max_length=50, null=True, blank=True)),
                ('endereco_email', models.CharField(max_length=100, null=True, blank=True)),
                ('descricao_local_atuacao', models.CharField(max_length=100, null=True, blank=True)),
                ('ativo', models.BooleanField()),
                ('txt_biografia', models.TextField(null=True, blank=True)),
                ('unid_deliberativa', models.BooleanField()),
                ('localidade_resid', models.ForeignKey(blank=True, to='parlamentares.Localidade', null=True)),
                ('nivel_instrucao', models.ForeignKey(blank=True, to='parlamentares.NivelInstrucao', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Partido',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_partido', models.CharField(max_length=9)),
                ('nome_partido', models.CharField(max_length=50)),
                ('data_criacao', models.DateField(null=True, blank=True)),
                ('data_extincao', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SessaoLegislativa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero', models.IntegerField()),
                ('tipo', models.CharField(max_length=1)),
                ('data_inicio', models.DateField()),
                ('data_fim', models.DateField()),
                ('data_inicio_intervalo', models.DateField(null=True, blank=True)),
                ('data_fim_intervalo', models.DateField(null=True, blank=True)),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura')),
            ],
        ),
        migrations.CreateModel(
            name='SituacaoMilitar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_tipo_situacao', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='TipoAfastamento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_afastamento', models.CharField(max_length=50)),
                ('afastamento', models.BooleanField()),
                ('fim_mandato', models.BooleanField()),
                ('descricao_dispositivo', models.CharField(max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TipoDependente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_tipo_dependente', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='parlamentar',
            name='situacao_militar',
            field=models.ForeignKey(blank=True, to='parlamentares.SituacaoMilitar', null=True),
        ),
        migrations.AddField(
            model_name='mandato',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='mandato',
            name='tipo_afastamento',
            field=models.ForeignKey(blank=True, to='parlamentares.TipoAfastamento', null=True),
        ),
        migrations.AddField(
            model_name='filiacao',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='filiacao',
            name='partido',
            field=models.ForeignKey(to='parlamentares.Partido'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='tipo_dependente',
            field=models.ForeignKey(to='parlamentares.TipoDependente'),
        ),
        migrations.AddField(
            model_name='composicaomesa',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='composicaomesa',
            name='sessao_legislativa',
            field=models.ForeignKey(to='parlamentares.SessaoLegislativa'),
        ),
        migrations.AddField(
            model_name='composicaocoligacao',
            name='partido',
            field=models.ForeignKey(to='parlamentares.Partido'),
        ),
        migrations.AddField(
            model_name='coligacao',
            name='legislatura',
            field=models.ForeignKey(to='parlamentares.Legislatura'),
        ),
    ]
