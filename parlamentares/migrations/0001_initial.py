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
                ('nome', models.CharField(max_length=50, verbose_name='Cargo na Mesa')),
                ('unico', models.BooleanField(verbose_name='Cargo \xdanico')),
            ],
            options={
                'verbose_name': 'Cargo na Mesa',
                'verbose_name_plural': 'Cargos na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Coligacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_coligacao', models.CharField(max_length=50, verbose_name='Nome')),
                ('numero_votos_coligacao', models.IntegerField(null=True, verbose_name='N\xba Votos Recebidos', blank=True)),
            ],
            options={
                'verbose_name': 'Coliga\xe7\xe3o',
                'verbose_name_plural': 'Coliga\xe7\xf5es',
            },
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
            options={
                'verbose_name': 'Ocupa\xe7\xe3o de cargo na Mesa',
                'verbose_name_plural': 'Ocupa\xe7\xf5es de cargo na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Dependente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_dependente', models.CharField(max_length=50, verbose_name='Nome')),
                ('sexo', models.CharField(max_length=1, verbose_name='Sexo')),
                ('data_nascimento', models.DateField(null=True, verbose_name='Data Nascimento', blank=True)),
                ('numero_cpf', models.CharField(max_length=14, null=True, verbose_name='CPF', blank=True)),
                ('numero_rg', models.CharField(max_length=15, null=True, verbose_name='RG', blank=True)),
                ('numero_tit_eleitor', models.CharField(max_length=15, null=True, verbose_name='N\xba T\xedtulo Eleitor', blank=True)),
            ],
            options={
                'verbose_name': 'Dependente',
                'verbose_name_plural': 'Dependentes',
            },
        ),
        migrations.CreateModel(
            name='Filiacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_filiacao', models.DateField(verbose_name='Data Filia\xe7\xe3o')),
                ('data_desfiliacao', models.DateField(null=True, verbose_name='Data Desfilia\xe7\xe3o', blank=True)),
            ],
            options={
                'verbose_name': 'Filia\xe7\xe3o',
                'verbose_name_plural': 'Filia\xe7\xf5es',
            },
        ),
        migrations.CreateModel(
            name='Legislatura',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_inicio', models.DateField(verbose_name='Data In\xedcio')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_eleicao', models.DateField(verbose_name='Data Elei\xe7\xe3o')),
            ],
            options={
                'verbose_name': 'Legislatura',
                'verbose_name_plural': 'Legislaturas',
            },
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
            options={
                'verbose_name': 'Munic\xedpio',
                'verbose_name_plural': 'Munic\xedpios',
            },
        ),
        migrations.CreateModel(
            name='Mandato',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_causa_fim_mandato', models.IntegerField(null=True, blank=True)),
                ('data_fim_mandato', models.DateField(null=True, verbose_name='Fim do Mandato', blank=True)),
                ('numero_votos_recebidos', models.IntegerField(null=True, verbose_name='Votos Recebidos', blank=True)),
                ('data_expedicao_diploma', models.DateField(null=True, verbose_name='Expedi\xe7\xe3o do Diploma', blank=True)),
                ('txt_observacao', models.TextField(null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('coligacao', models.ForeignKey(verbose_name='Coliga\xe7\xe3o', blank=True, to='parlamentares.Coligacao', null=True)),
                ('legislatura', models.ForeignKey(verbose_name='Legislatura', to='parlamentares.Legislatura')),
            ],
            options={
                'verbose_name': 'Mandato',
                'verbose_name_plural': 'Mandatos',
            },
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nivel_instrucao', models.CharField(max_length=50, verbose_name='N\xedvel de Instru\xe7\xe3o')),
            ],
            options={
                'verbose_name': 'N\xedvel Instru\xe7\xe3o',
                'verbose_name_plural': 'N\xedveis Instru\xe7\xe3o',
            },
        ),
        migrations.CreateModel(
            name='Parlamentar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_completo', models.CharField(max_length=50, verbose_name='Nome Completo')),
                ('nome_parlamentar', models.CharField(max_length=50, null=True, verbose_name='Nome Parlamentar', blank=True)),
                ('sexo', models.CharField(max_length=1, verbose_name='Sexo')),
                ('data_nascimento', models.DateField(null=True, verbose_name='Data Nascimento', blank=True)),
                ('numero_cpf', models.CharField(max_length=14, null=True, verbose_name='C.P.F', blank=True)),
                ('numero_rg', models.CharField(max_length=15, null=True, verbose_name='R.G.', blank=True)),
                ('numero_tit_eleitor', models.CharField(max_length=15, null=True, verbose_name='T\xedtulo de Eleitor', blank=True)),
                ('cod_casa', models.IntegerField()),
                ('numero_gab_parlamentar', models.CharField(max_length=10, null=True, verbose_name='N\xba Gabinete', blank=True)),
                ('numero_tel_parlamentar', models.CharField(max_length=50, null=True, verbose_name='Telefone', blank=True)),
                ('numero_fax_parlamentar', models.CharField(max_length=50, null=True, verbose_name='Fax', blank=True)),
                ('endereco_residencial', models.CharField(max_length=100, null=True, verbose_name='Endere\xe7o Residencial', blank=True)),
                ('numero_cep_resid', models.CharField(max_length=9, null=True, verbose_name='CEP', blank=True)),
                ('numero_tel_resid', models.CharField(max_length=50, null=True, verbose_name='Telefone Residencial', blank=True)),
                ('numero_fax_resid', models.CharField(max_length=50, null=True, verbose_name='Fax Residencial', blank=True)),
                ('endereco_web', models.CharField(max_length=100, null=True, verbose_name='HomePage', blank=True)),
                ('nome_profissao', models.CharField(max_length=50, null=True, verbose_name='Profiss\xe3o', blank=True)),
                ('endereco_email', models.CharField(max_length=100, null=True, verbose_name='Correio Eletr\xf4nico', blank=True)),
                ('descricao_local_atuacao', models.CharField(max_length=100, null=True, verbose_name='Locais de Atua\xe7\xe3o', blank=True)),
                ('ativo', models.BooleanField(verbose_name='Ativo na Casa?')),
                ('txt_biografia', models.TextField(null=True, verbose_name='Biografia', blank=True)),
                ('unid_deliberativa', models.BooleanField()),
                ('localidade_resid', models.ForeignKey(verbose_name='Munic\xedpio', blank=True, to='parlamentares.Localidade', null=True)),
                ('nivel_instrucao', models.ForeignKey(verbose_name='N\xedvel Instru\xe7\xe3o', blank=True, to='parlamentares.NivelInstrucao', null=True)),
            ],
            options={
                'verbose_name': 'Parlamentar',
                'verbose_name_plural': 'Parlamentares',
            },
        ),
        migrations.CreateModel(
            name='Partido',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_partido', models.CharField(max_length=9, verbose_name='Sigla')),
                ('nome_partido', models.CharField(max_length=50, verbose_name='Nome')),
                ('data_criacao', models.DateField(null=True, verbose_name='Data Cria\xe7\xe3o', blank=True)),
                ('data_extincao', models.DateField(null=True, verbose_name='Data Extin\xe7\xe3o', blank=True)),
            ],
            options={
                'verbose_name': 'Partido',
                'verbose_name_plural': 'Partidos',
            },
        ),
        migrations.CreateModel(
            name='SessaoLegislativa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero', models.IntegerField(verbose_name='N\xfamero')),
                ('tipo', models.CharField(max_length=1, verbose_name='Tipo')),
                ('data_inicio', models.DateField(verbose_name='Data In\xedcio')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_inicio_intervalo', models.DateField(null=True, verbose_name='In\xedcio Intervalo', blank=True)),
                ('data_fim_intervalo', models.DateField(null=True, verbose_name='Fim Intervalo', blank=True)),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura')),
            ],
            options={
                'verbose_name': 'Sess\xe3o Legislativa',
                'verbose_name_plural': 'Sess\xf5es Legislativas',
            },
        ),
        migrations.CreateModel(
            name='SituacaoMilitar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_tipo_situacao', models.CharField(max_length=50, verbose_name='Situa\xe7\xe3o Militar')),
            ],
            options={
                'verbose_name': 'Tipo Situa\xe7\xe3o Militar',
                'verbose_name_plural': 'Tipos Situa\xe7\xf5es Militares',
            },
        ),
        migrations.CreateModel(
            name='TipoAfastamento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_afastamento', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o')),
                ('afastamento', models.BooleanField(verbose_name='Indicador')),
                ('fim_mandato', models.BooleanField(verbose_name='Indicador')),
                ('descricao_dispositivo', models.CharField(max_length=50, null=True, verbose_name='Dispositivo', blank=True)),
            ],
            options={
                'verbose_name': 'Tipo de Afastamento',
                'verbose_name_plural': 'Tipos de Afastamento',
            },
        ),
        migrations.CreateModel(
            name='TipoDependente',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_tipo_dependente', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Tipo de Dependente',
                'verbose_name_plural': 'Tipos de Dependente',
            },
        ),
        migrations.AddField(
            model_name='parlamentar',
            name='situacao_militar',
            field=models.ForeignKey(verbose_name='Situa\xe7\xe3o Militar', blank=True, to='parlamentares.SituacaoMilitar', null=True),
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
            field=models.ForeignKey(verbose_name='Partido', to='parlamentares.Partido'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='tipo_dependente',
            field=models.ForeignKey(verbose_name='Tipo', to='parlamentares.TipoDependente'),
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
            field=models.ForeignKey(verbose_name='Legislatura', to='parlamentares.Legislatura'),
        ),
    ]
