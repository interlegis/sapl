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
                ('descricao', models.CharField(max_length=50, verbose_name='Cargo na Mesa')),
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
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('numero_votos', models.IntegerField(null=True, verbose_name='N\xba Votos Recebidos', blank=True)),
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
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('sexo', models.CharField(max_length=1, verbose_name='Sexo', choices=[(b'F', 'Feminino'), (b'M', 'Masculino')])),
                ('data_nascimento', models.DateField(null=True, verbose_name='Data Nascimento', blank=True)),
                ('cpf', models.CharField(max_length=14, null=True, verbose_name='CPF', blank=True)),
                ('rg', models.CharField(max_length=15, null=True, verbose_name='RG', blank=True)),
                ('titulo_eleitor', models.CharField(max_length=15, null=True, verbose_name='N\xba T\xedtulo Eleitor', blank=True)),
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
                ('data', models.DateField(verbose_name='Data Filia\xe7\xe3o')),
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
            name='Mandato',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_causa_fim_mandato', models.IntegerField(null=True, blank=True)),
                ('data_fim_mandato', models.DateField(null=True, verbose_name='Fim do Mandato', blank=True)),
                ('votos_recebidos', models.IntegerField(null=True, verbose_name='Votos Recebidos', blank=True)),
                ('data_expedicao_diploma', models.DateField(null=True, verbose_name='Expedi\xe7\xe3o do Diploma', blank=True)),
                ('observacao', models.TextField(null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('coligacao', models.ForeignKey(verbose_name='Coliga\xe7\xe3o', blank=True, to='parlamentares.Coligacao', null=True)),
                ('legislatura', models.ForeignKey(verbose_name='Legislatura', to='parlamentares.Legislatura')),
            ],
            options={
                'verbose_name': 'Mandato',
                'verbose_name_plural': 'Mandatos',
            },
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50, null=True, blank=True)),
                ('uf', models.CharField(blank=True, max_length=2, null=True, choices=[(b'AC', 'Acre'), (b'AL', 'Alagoas'), (b'AP', 'Amap\xe1'), (b'AM', 'Amazonas'), (b'BA', 'Bahia'), (b'CE', 'Cear\xe1'), (b'DF', 'Distrito Federal'), (b'ES', 'Esp\xedrito Santo'), (b'GO', 'Goi\xe1s'), (b'MA', 'Maranh\xe3o'), (b'MT', 'Mato Grosso'), (b'MS', 'Mato Grosso do Sul'), (b'MG', 'Minas Gerais'), (b'PR', 'Paran\xe1'), (b'PB', 'Para\xedba'), (b'PA', 'Par\xe1'), (b'PE', 'Pernambuco'), (b'PI', 'Piau\xed'), (b'RJ', 'Rio de Janeiro'), (b'RN', 'Rio Grande do Norte'), (b'RS', 'Rio Grande do Sul'), (b'RO', 'Rond\xf4nia'), (b'RR', 'Roraima'), (b'SC', 'Santa Catarina'), (b'SE', 'Sergipe'), (b'SP', 'S\xe3o Paulo'), (b'TO', 'Tocantins'), (b'EX', 'Exterior')])),
                ('regiao', models.CharField(blank=True, max_length=2, null=True, choices=[(b'CO', 'Centro-Oeste'), (b'NE', 'Nordeste'), (b'NO', 'Norte'), (b'SE', 'Sudeste'), (b'SL', 'Sul'), (b'EX', 'Exterior')])),
            ],
            options={
                'verbose_name': 'Munic\xedpio',
                'verbose_name_plural': 'Munic\xedpios',
            },
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao', models.CharField(max_length=50, verbose_name='N\xedvel de Instru\xe7\xe3o')),
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
                ('sexo', models.CharField(max_length=1, verbose_name='Sexo', choices=[(b'F', 'Feminino'), (b'M', 'Masculino')])),
                ('data_nascimento', models.DateField(null=True, verbose_name='Data Nascimento', blank=True)),
                ('cpf', models.CharField(max_length=14, null=True, verbose_name='C.P.F', blank=True)),
                ('rg', models.CharField(max_length=15, null=True, verbose_name='R.G.', blank=True)),
                ('titulo_eleitor', models.CharField(max_length=15, null=True, verbose_name='T\xedtulo de Eleitor', blank=True)),
                ('cod_casa', models.IntegerField()),
                ('numero_gab_parlamentar', models.CharField(max_length=10, null=True, verbose_name='N\xba Gabinete', blank=True)),
                ('telefone', models.CharField(max_length=50, null=True, verbose_name='Telefone', blank=True)),
                ('fax', models.CharField(max_length=50, null=True, verbose_name='Fax', blank=True)),
                ('endereco_residencia', models.CharField(max_length=100, null=True, verbose_name='Endere\xe7o Residencial', blank=True)),
                ('cep_residencia', models.CharField(max_length=9, null=True, verbose_name='CEP', blank=True)),
                ('telefone_residencia', models.CharField(max_length=50, null=True, verbose_name='Telefone Residencial', blank=True)),
                ('fax_residencia', models.CharField(max_length=50, null=True, verbose_name='Fax Residencial', blank=True)),
                ('endereco_web', models.CharField(max_length=100, null=True, verbose_name='HomePage', blank=True)),
                ('profissao', models.CharField(max_length=50, null=True, verbose_name='Profiss\xe3o', blank=True)),
                ('email', models.CharField(max_length=100, null=True, verbose_name='Correio Eletr\xf4nico', blank=True)),
                ('locais_atuacao', models.CharField(max_length=100, null=True, verbose_name='Locais de Atua\xe7\xe3o', blank=True)),
                ('ativo', models.BooleanField(verbose_name='Ativo na Casa?')),
                ('biografia', models.TextField(null=True, verbose_name='Biografia', blank=True)),
                ('unidade_deliberativa', models.BooleanField()),
                ('municipio_residencia', models.ForeignKey(verbose_name='Munic\xedpio', blank=True, to='parlamentares.Municipio', null=True)),
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
                ('sigla', models.CharField(max_length=9, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
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
                ('tipo', models.CharField(max_length=1, verbose_name='Tipo', choices=[(b'O', 'Ordin\xe1ria'), (b'E', 'Extraordin\xe1ria')])),
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
                ('descricao', models.CharField(max_length=50, verbose_name='Situa\xe7\xe3o Militar')),
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
                ('descricao', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o')),
                ('afastamento', models.BooleanField(verbose_name='Indicador')),
                ('fim_mandato', models.BooleanField(verbose_name='Indicador')),
                ('dispositivo', models.CharField(max_length=50, null=True, verbose_name='Dispositivo', blank=True)),
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
                ('descricao', models.CharField(max_length=50)),
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
            name='tipo',
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
