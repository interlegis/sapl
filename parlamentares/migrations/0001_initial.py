# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CargoMesa',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Cargo na Mesa')),
                ('unico', models.BooleanField(verbose_name='Cargo Único', choices=[(True, 'Sim'), (False, 'Não')])),
            ],
            options={
                'verbose_name_plural': 'Cargos na Mesa',
                'verbose_name': 'Cargo na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Coligacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('numero_votos', models.IntegerField(blank=True, null=True, verbose_name='Nº Votos Recebidos')),
            ],
            options={
                'verbose_name_plural': 'Coligações',
                'verbose_name': 'Coligação',
            },
        ),
        migrations.CreateModel(
            name='ComposicaoColigacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('coligacao', models.ForeignKey(to='parlamentares.Coligacao')),
            ],
            options={
                'verbose_name_plural': 'Composição Coligações',
                'verbose_name': 'Composição Coligação',
            },
        ),
        migrations.CreateModel(
            name='ComposicaoMesa',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('cargo', models.ForeignKey(to='parlamentares.CargoMesa')),
            ],
            options={
                'verbose_name_plural': 'Ocupações de cargo na Mesa',
                'verbose_name': 'Ocupação de cargo na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Dependente',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('sexo', models.CharField(choices=[('F', 'Feminino'), ('M', 'Masculino')], max_length=1, verbose_name='Sexo')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('cpf', models.CharField(blank=True, max_length=14, null=True, verbose_name='CPF')),
                ('rg', models.CharField(blank=True, max_length=15, null=True, verbose_name='RG')),
                ('titulo_eleitor', models.CharField(blank=True, max_length=15, null=True, verbose_name='Nº Título Eleitor')),
            ],
            options={
                'verbose_name_plural': 'Dependentes',
                'verbose_name': 'Dependente',
            },
        ),
        migrations.CreateModel(
            name='Filiacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data', models.DateField(verbose_name='Data Filiação')),
                ('data_desfiliacao', models.DateField(blank=True, null=True, verbose_name='Data Desfiliação')),
            ],
            options={
                'verbose_name_plural': 'Filiações',
                'verbose_name': 'Filiação',
            },
        ),
        migrations.CreateModel(
            name='Legislatura',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_eleicao', models.DateField(verbose_name='Data Eleição')),
            ],
            options={
                'verbose_name_plural': 'Legislaturas',
                'verbose_name': 'Legislatura',
            },
        ),
        migrations.CreateModel(
            name='Mandato',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('tipo_causa_fim_mandato', models.IntegerField(blank=True, null=True)),
                ('data_fim_mandato', models.DateField(blank=True, null=True, verbose_name='Fim do Mandato')),
                ('votos_recebidos', models.IntegerField(blank=True, null=True, verbose_name='Votos Recebidos')),
                ('data_expedicao_diploma', models.DateField(blank=True, null=True, verbose_name='Expedição do Diploma')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Observação')),
                ('coligacao', models.ForeignKey(blank=True, null=True, to='parlamentares.Coligacao', verbose_name='Coligação')),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura', verbose_name='Legislatura')),
            ],
            options={
                'verbose_name_plural': 'Mandatos',
                'verbose_name': 'Mandato',
            },
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(blank=True, max_length=50, null=True)),
                ('uf', models.CharField(blank=True, max_length=2, null=True, choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PR', 'Paraná'), ('PB', 'Paraíba'), ('PA', 'Pará'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'), ('EX', 'Exterior')])),
                ('regiao', models.CharField(blank=True, max_length=2, null=True, choices=[('CO', 'Centro-Oeste'), ('NE', 'Nordeste'), ('NO', 'Norte'), ('SE', 'Sudeste'), ('SL', 'Sul'), ('EX', 'Exterior')])),
            ],
            options={
                'verbose_name_plural': 'Municípios',
                'verbose_name': 'Município',
            },
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Nível de Instrução')),
            ],
            options={
                'verbose_name_plural': 'Níveis Instrução',
                'verbose_name': 'Nível Instrução',
            },
        ),
        migrations.CreateModel(
            name='Parlamentar',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome_completo', models.CharField(max_length=50, verbose_name='Nome Completo')),
                ('nome_parlamentar', models.CharField(blank=True, max_length=50, null=True, verbose_name='Nome Parlamentar')),
                ('sexo', models.CharField(choices=[('F', 'Feminino'), ('M', 'Masculino')], max_length=1, verbose_name='Sexo')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('cpf', models.CharField(blank=True, max_length=14, null=True, verbose_name='C.P.F')),
                ('rg', models.CharField(blank=True, max_length=15, null=True, verbose_name='R.G.')),
                ('titulo_eleitor', models.CharField(blank=True, max_length=15, null=True, verbose_name='Título de Eleitor')),
                ('cod_casa', models.IntegerField()),
                ('numero_gab_parlamentar', models.CharField(blank=True, max_length=10, null=True, verbose_name='Nº Gabinete')),
                ('telefone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefone')),
                ('fax', models.CharField(blank=True, max_length=50, null=True, verbose_name='Fax')),
                ('endereco_residencia', models.CharField(blank=True, max_length=100, null=True, verbose_name='Endereço Residencial')),
                ('cep_residencia', models.CharField(blank=True, max_length=9, null=True, verbose_name='CEP')),
                ('telefone_residencia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefone Residencial')),
                ('fax_residencia', models.CharField(blank=True, max_length=50, null=True, verbose_name='Fax Residencial')),
                ('endereco_web', models.CharField(blank=True, max_length=100, null=True, verbose_name='HomePage')),
                ('profissao', models.CharField(blank=True, max_length=50, null=True, verbose_name='Profissão')),
                ('email', models.CharField(blank=True, max_length=100, null=True, verbose_name='Correio Eletrônico')),
                ('locais_atuacao', models.CharField(blank=True, max_length=100, null=True, verbose_name='Locais de Atuação')),
                ('ativo', models.BooleanField(verbose_name='Ativo na Casa?')),
                ('biografia', models.TextField(blank=True, null=True, verbose_name='Biografia')),
                ('unidade_deliberativa', models.BooleanField()),
                ('municipio_residencia', models.ForeignKey(blank=True, null=True, to='parlamentares.Municipio', verbose_name='Município')),
                ('nivel_instrucao', models.ForeignKey(blank=True, null=True, to='parlamentares.NivelInstrucao', verbose_name='Nível Instrução')),
            ],
            options={
                'verbose_name_plural': 'Parlamentares',
                'verbose_name': 'Parlamentar',
            },
        ),
        migrations.CreateModel(
            name='Partido',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('sigla', models.CharField(max_length=9, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('data_criacao', models.DateField(blank=True, null=True, verbose_name='Data Criação')),
                ('data_extincao', models.DateField(blank=True, null=True, verbose_name='Data Extinção')),
            ],
            options={
                'verbose_name_plural': 'Partidos',
                'verbose_name': 'Partido',
            },
        ),
        migrations.CreateModel(
            name='SessaoLegislativa',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('tipo', models.CharField(choices=[('O', 'Ordinária'), ('E', 'Extraordinária')], max_length=1, verbose_name='Tipo')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_inicio_intervalo', models.DateField(blank=True, null=True, verbose_name='Início Intervalo')),
                ('data_fim_intervalo', models.DateField(blank=True, null=True, verbose_name='Fim Intervalo')),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura')),
            ],
            options={
                'verbose_name_plural': 'Sessões Legislativas',
                'verbose_name': 'Sessão Legislativa',
            },
        ),
        migrations.CreateModel(
            name='SituacaoMilitar',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Situação Militar')),
            ],
            options={
                'verbose_name_plural': 'Tipos Situações Militares',
                'verbose_name': 'Tipo Situação Militar',
            },
        ),
        migrations.CreateModel(
            name='TipoAfastamento',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
                ('afastamento', models.BooleanField(verbose_name='Indicador')),
                ('fim_mandato', models.BooleanField(verbose_name='Indicador')),
                ('dispositivo', models.CharField(blank=True, max_length=50, null=True, verbose_name='Dispositivo')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Afastamento',
                'verbose_name': 'Tipo de Afastamento',
            },
        ),
        migrations.CreateModel(
            name='TipoDependente',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Tipos de Dependente',
                'verbose_name': 'Tipo de Dependente',
            },
        ),
        migrations.AddField(
            model_name='parlamentar',
            name='situacao_militar',
            field=models.ForeignKey(blank=True, null=True, to='parlamentares.SituacaoMilitar', verbose_name='Situação Militar'),
        ),
        migrations.AddField(
            model_name='mandato',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='mandato',
            name='tipo_afastamento',
            field=models.ForeignKey(blank=True, null=True, to='parlamentares.TipoAfastamento'),
        ),
        migrations.AddField(
            model_name='filiacao',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='filiacao',
            name='partido',
            field=models.ForeignKey(to='parlamentares.Partido', verbose_name='Partido'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='dependente',
            name='tipo',
            field=models.ForeignKey(to='parlamentares.TipoDependente', verbose_name='Tipo'),
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
            field=models.ForeignKey(to='parlamentares.Legislatura', verbose_name='Legislatura'),
        ),
    ]
