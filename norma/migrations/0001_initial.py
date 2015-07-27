# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssuntoNorma',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('assunto', models.CharField(max_length=50, verbose_name='Assunto')),
                ('descricao', models.CharField(max_length=250, blank=True, verbose_name='Descrição', null=True)),
            ],
            options={
                'verbose_name': 'Assunto de Norma',
                'verbose_name_plural': 'Assuntos de Norma',
            },
        ),
        migrations.CreateModel(
            name='LegislacaoCitada',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('disposicoes', models.CharField(max_length=15, blank=True, verbose_name='Disposição', null=True)),
                ('parte', models.CharField(max_length=8, blank=True, verbose_name='Parte', null=True)),
                ('livro', models.CharField(max_length=7, blank=True, verbose_name='Livro', null=True)),
                ('titulo', models.CharField(max_length=7, blank=True, verbose_name='Título', null=True)),
                ('capitulo', models.CharField(max_length=7, blank=True, verbose_name='Capítulo', null=True)),
                ('secao', models.CharField(max_length=7, blank=True, verbose_name='Seção', null=True)),
                ('subsecao', models.CharField(max_length=7, blank=True, verbose_name='Subseção', null=True)),
                ('artigo', models.CharField(max_length=4, blank=True, verbose_name='Artigo', null=True)),
                ('paragrafo', models.CharField(max_length=3, blank=True, verbose_name='Parágrafo', null=True)),
                ('inciso', models.CharField(max_length=10, blank=True, verbose_name='Inciso', null=True)),
                ('alinea', models.CharField(max_length=3, blank=True, verbose_name='Alínea', null=True)),
                ('item', models.CharField(max_length=3, blank=True, verbose_name='Item', null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Matéria Legislativa',
                'verbose_name_plural': 'Matérias Legislativas',
            },
        ),
        migrations.CreateModel(
            name='NormaJuridica',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('esfera_federacao', models.CharField(max_length=1, choices=[('E', 'Estadual'), ('F', 'Federal'), ('M', 'Municipal')], verbose_name='Esfera Federação')),
                ('data', models.DateField(blank=True, verbose_name='Data', null=True)),
                ('data_publicacao', models.DateField(blank=True, verbose_name='Data Publicação', null=True)),
                ('veiculo_publicacao', models.CharField(max_length=30, blank=True, verbose_name='Veículo Publicação', null=True)),
                ('pagina_inicio_publicacao', models.IntegerField(blank=True, verbose_name='Pg. Início', null=True)),
                ('pagina_fim_publicacao', models.IntegerField(blank=True, verbose_name='Pg. Fim', null=True)),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('indexacao', models.TextField(blank=True, verbose_name='Indexação', null=True)),
                ('observacao', models.TextField(blank=True, verbose_name='Observação', null=True)),
                ('complemento', models.NullBooleanField(verbose_name='Complementar ?')),
                ('data_vigencia', models.DateField(blank=True, null=True)),
                ('timestamp', models.DateTimeField()),
                ('assunto', models.ForeignKey(to='norma.AssuntoNorma')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Norma Jurídica',
                'verbose_name_plural': 'Normas Jurídicas',
            },
        ),
        migrations.CreateModel(
            name='TipoNormaJuridica',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('equivalente_lexml', models.CharField(max_length=50, choices=[('constituicao', 'constituicao'), ('ementa.constitucional', 'ementa.constitucional'), ('lei.complementar', 'lei.complementar'), ('lei.delegada', 'lei.delegada'), ('lei', 'lei'), ('decreto.lei', 'decreto.lei'), ('medida.provisoria', 'medida.provisoria'), ('decreto', 'decreto'), ('lei.organica', 'lei.organica'), ('emenda.lei.organica', 'emenda.lei.organica'), ('decreto.legislativo', 'decreto.legislativo'), ('resolucao', 'resolucao'), ('regimento.interno', 'regimento.interno')], blank=True, verbose_name='Equivalente LexML', null=True)),
                ('sigla', models.CharField(max_length=3, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo de Norma Jurídica',
                'verbose_name_plural': 'Tipos de Norma Jurídica',
            },
        ),
        migrations.CreateModel(
            name='VinculoNormaJuridica',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('tipo_vinculo', models.CharField(max_length=1, choices=[('A', 'Altera a norma'), ('R', 'Revoga a norma'), ('P', 'Revoga parcialmente a norma'), ('T', 'Revoga por consolidação a norma'), ('C', 'Norma correlata'), ('I', 'Suspende a execução da norma'), ('G', 'Regulamenta a norma')], blank=True, null=True)),
                ('norma_referente', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
                ('norma_referida', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
            ],
            options={
                'verbose_name': 'Vínculo entre Normas Jurídicas',
                'verbose_name_plural': 'Vínculos entre Normas Jurídicas',
            },
        ),
        migrations.AddField(
            model_name='normajuridica',
            name='tipo',
            field=models.ForeignKey(to='norma.TipoNormaJuridica', verbose_name='Tipo'),
        ),
        migrations.AddField(
            model_name='legislacaocitada',
            name='norma',
            field=models.ForeignKey(to='norma.NormaJuridica'),
        ),
    ]
