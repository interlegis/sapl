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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Cargo na Mesa')),
                ('unico', models.BooleanField(verbose_name='Cargo Único')),
            ],
            options={
                'verbose_name': 'Cargo na Mesa',
                'verbose_name_plural': 'Cargos na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Coligacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('numero_votos', models.IntegerField(blank=True, verbose_name='Nº Votos Recebidos', null=True)),
            ],
            options={
                'verbose_name': 'Coligação',
                'verbose_name_plural': 'Coligações',
            },
        ),
        migrations.CreateModel(
            name='ComposicaoColigacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('coligacao', models.ForeignKey(to='parlamentares.Coligacao')),
            ],
            options={
                'verbose_name': 'Composição Coligação',
                'verbose_name_plural': 'Composição Coligações',
            },
        ),
        migrations.CreateModel(
            name='ComposicaoMesa',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('cargo', models.ForeignKey(to='parlamentares.CargoMesa')),
            ],
            options={
                'verbose_name': 'Ocupação de cargo na Mesa',
                'verbose_name_plural': 'Ocupações de cargo na Mesa',
            },
        ),
        migrations.CreateModel(
            name='Dependente',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('sexo', models.CharField(max_length=1, choices=[('F', 'Feminino'), ('M', 'Masculino')], verbose_name='Sexo')),
                ('data_nascimento', models.DateField(blank=True, verbose_name='Data Nascimento', null=True)),
                ('cpf', models.CharField(max_length=14, blank=True, verbose_name='CPF', null=True)),
                ('rg', models.CharField(max_length=15, blank=True, verbose_name='RG', null=True)),
                ('titulo_eleitor', models.CharField(max_length=15, blank=True, verbose_name='Nº Título Eleitor', null=True)),
            ],
            options={
                'verbose_name': 'Dependente',
                'verbose_name_plural': 'Dependentes',
            },
        ),
        migrations.CreateModel(
            name='Filiacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data', models.DateField(verbose_name='Data Filiação')),
                ('data_desfiliacao', models.DateField(blank=True, verbose_name='Data Desfiliação', null=True)),
            ],
            options={
                'verbose_name': 'Filiação',
                'verbose_name_plural': 'Filiações',
            },
        ),
        migrations.CreateModel(
            name='Legislatura',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_eleicao', models.DateField(verbose_name='Data Eleição')),
            ],
            options={
                'verbose_name': 'Legislatura',
                'verbose_name_plural': 'Legislaturas',
            },
        ),
        migrations.CreateModel(
            name='Mandato',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('tipo_causa_fim_mandato', models.IntegerField(blank=True, null=True)),
                ('data_fim_mandato', models.DateField(blank=True, verbose_name='Fim do Mandato', null=True)),
                ('votos_recebidos', models.IntegerField(blank=True, verbose_name='Votos Recebidos', null=True)),
                ('data_expedicao_diploma', models.DateField(blank=True, verbose_name='Expedição do Diploma', null=True)),
                ('observacao', models.TextField(blank=True, verbose_name='Observação', null=True)),
                ('coligacao', models.ForeignKey(to='parlamentares.Coligacao', blank=True, null=True, verbose_name='Coligação')),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura', verbose_name='Legislatura')),
            ],
            options={
                'verbose_name': 'Mandato',
                'verbose_name_plural': 'Mandatos',
            },
        ),
        migrations.CreateModel(
            name='Municipio',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, blank=True, null=True)),
                ('uf', models.CharField(max_length=2, choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PR', 'Paraná'), ('PB', 'Paraíba'), ('PA', 'Pará'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'), ('EX', 'Exterior')], blank=True, null=True)),
                ('regiao', models.CharField(max_length=2, choices=[('CO', 'Centro-Oeste'), ('NE', 'Nordeste'), ('NO', 'Norte'), ('SE', 'Sudeste'), ('SL', 'Sul'), ('EX', 'Exterior')], blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Município',
                'verbose_name_plural': 'Municípios',
            },
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Nível de Instrução')),
            ],
            options={
                'verbose_name': 'Nível Instrução',
                'verbose_name_plural': 'Níveis Instrução',
            },
        ),
        migrations.CreateModel(
            name='Parlamentar',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome_completo', models.CharField(max_length=50, verbose_name='Nome Completo')),
                ('nome_parlamentar', models.CharField(max_length=50, blank=True, verbose_name='Nome Parlamentar', null=True)),
                ('sexo', models.CharField(max_length=1, choices=[('F', 'Feminino'), ('M', 'Masculino')], verbose_name='Sexo')),
                ('data_nascimento', models.DateField(blank=True, verbose_name='Data Nascimento', null=True)),
                ('cpf', models.CharField(max_length=14, blank=True, verbose_name='C.P.F', null=True)),
                ('rg', models.CharField(max_length=15, blank=True, verbose_name='R.G.', null=True)),
                ('titulo_eleitor', models.CharField(max_length=15, blank=True, verbose_name='Título de Eleitor', null=True)),
                ('cod_casa', models.IntegerField()),
                ('numero_gab_parlamentar', models.CharField(max_length=10, blank=True, verbose_name='Nº Gabinete', null=True)),
                ('telefone', models.CharField(max_length=50, blank=True, verbose_name='Telefone', null=True)),
                ('fax', models.CharField(max_length=50, blank=True, verbose_name='Fax', null=True)),
                ('endereco_residencia', models.CharField(max_length=100, blank=True, verbose_name='Endereço Residencial', null=True)),
                ('cep_residencia', models.CharField(max_length=9, blank=True, verbose_name='CEP', null=True)),
                ('telefone_residencia', models.CharField(max_length=50, blank=True, verbose_name='Telefone Residencial', null=True)),
                ('fax_residencia', models.CharField(max_length=50, blank=True, verbose_name='Fax Residencial', null=True)),
                ('endereco_web', models.CharField(max_length=100, blank=True, verbose_name='HomePage', null=True)),
                ('profissao', models.CharField(max_length=50, blank=True, verbose_name='Profissão', null=True)),
                ('email', models.CharField(max_length=100, blank=True, verbose_name='Correio Eletrônico', null=True)),
                ('locais_atuacao', models.CharField(max_length=100, blank=True, verbose_name='Locais de Atuação', null=True)),
                ('ativo', models.BooleanField(verbose_name='Ativo na Casa?')),
                ('biografia', models.TextField(blank=True, verbose_name='Biografia', null=True)),
                ('unidade_deliberativa', models.BooleanField()),
                ('municipio_residencia', models.ForeignKey(to='parlamentares.Municipio', blank=True, null=True, verbose_name='Município')),
                ('nivel_instrucao', models.ForeignKey(to='parlamentares.NivelInstrucao', blank=True, null=True, verbose_name='Nível Instrução')),
            ],
            options={
                'verbose_name': 'Parlamentar',
                'verbose_name_plural': 'Parlamentares',
            },
        ),
        migrations.CreateModel(
            name='Partido',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('sigla', models.CharField(max_length=9, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('data_criacao', models.DateField(blank=True, verbose_name='Data Criação', null=True)),
                ('data_extincao', models.DateField(blank=True, verbose_name='Data Extinção', null=True)),
            ],
            options={
                'verbose_name': 'Partido',
                'verbose_name_plural': 'Partidos',
            },
        ),
        migrations.CreateModel(
            name='SessaoLegislativa',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('tipo', models.CharField(max_length=1, choices=[('O', 'Ordinária'), ('E', 'Extraordinária')], verbose_name='Tipo')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('data_inicio_intervalo', models.DateField(blank=True, verbose_name='Início Intervalo', null=True)),
                ('data_fim_intervalo', models.DateField(blank=True, verbose_name='Fim Intervalo', null=True)),
                ('legislatura', models.ForeignKey(to='parlamentares.Legislatura')),
            ],
            options={
                'verbose_name': 'Sessão Legislativa',
                'verbose_name_plural': 'Sessões Legislativas',
            },
        ),
        migrations.CreateModel(
            name='SituacaoMilitar',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Situação Militar')),
            ],
            options={
                'verbose_name': 'Tipo Situação Militar',
                'verbose_name_plural': 'Tipos Situações Militares',
            },
        ),
        migrations.CreateModel(
            name='TipoAfastamento',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
                ('afastamento', models.BooleanField(verbose_name='Indicador')),
                ('fim_mandato', models.BooleanField(verbose_name='Indicador')),
                ('dispositivo', models.CharField(max_length=50, blank=True, verbose_name='Dispositivo', null=True)),
            ],
            options={
                'verbose_name': 'Tipo de Afastamento',
                'verbose_name_plural': 'Tipos de Afastamento',
            },
        ),
        migrations.CreateModel(
            name='TipoDependente',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
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
            field=models.ForeignKey(to='parlamentares.SituacaoMilitar', blank=True, null=True, verbose_name='Situação Militar'),
        ),
        migrations.AddField(
            model_name='mandato',
            name='parlamentar',
            field=models.ForeignKey(to='parlamentares.Parlamentar'),
        ),
        migrations.AddField(
            model_name='mandato',
            name='tipo_afastamento',
            field=models.ForeignKey(to='parlamentares.TipoAfastamento', blank=True, null=True),
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
