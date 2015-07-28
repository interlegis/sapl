# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssuntoNorma',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('assunto', models.CharField(max_length=50, verbose_name='Assunto')),
                ('descricao', models.CharField(blank=True, max_length=250, null=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name_plural': 'Assuntos de Norma',
                'verbose_name': 'Assunto de Norma',
            },
        ),
        migrations.CreateModel(
            name='LegislacaoCitada',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('disposicoes', models.CharField(blank=True, max_length=15, null=True, verbose_name='Disposição')),
                ('parte', models.CharField(blank=True, max_length=8, null=True, verbose_name='Parte')),
                ('livro', models.CharField(blank=True, max_length=7, null=True, verbose_name='Livro')),
                ('titulo', models.CharField(blank=True, max_length=7, null=True, verbose_name='Título')),
                ('capitulo', models.CharField(blank=True, max_length=7, null=True, verbose_name='Capítulo')),
                ('secao', models.CharField(blank=True, max_length=7, null=True, verbose_name='Seção')),
                ('subsecao', models.CharField(blank=True, max_length=7, null=True, verbose_name='Subseção')),
                ('artigo', models.CharField(blank=True, max_length=4, null=True, verbose_name='Artigo')),
                ('paragrafo', models.CharField(blank=True, max_length=3, null=True, verbose_name='Parágrafo')),
                ('inciso', models.CharField(blank=True, max_length=10, null=True, verbose_name='Inciso')),
                ('alinea', models.CharField(blank=True, max_length=3, null=True, verbose_name='Alínea')),
                ('item', models.CharField(blank=True, max_length=3, null=True, verbose_name='Item')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name_plural': 'Matérias Legislativas',
                'verbose_name': 'Matéria Legislativa',
            },
        ),
        migrations.CreateModel(
            name='NormaJuridica',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('esfera_federacao', models.CharField(choices=[('E', 'Estadual'), ('F', 'Federal'), ('M', 'Municipal')], max_length=1, verbose_name='Esfera Federação')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('data_publicacao', models.DateField(blank=True, null=True, verbose_name='Data Publicação')),
                ('veiculo_publicacao', models.CharField(blank=True, max_length=30, null=True, verbose_name='Veículo Publicação')),
                ('pagina_inicio_publicacao', models.IntegerField(blank=True, null=True, verbose_name='Pg. Início')),
                ('pagina_fim_publicacao', models.IntegerField(blank=True, null=True, verbose_name='Pg. Fim')),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('indexacao', models.TextField(blank=True, null=True, verbose_name='Indexação')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Observação')),
                ('complemento', models.NullBooleanField(verbose_name='Complementar ?')),
                ('data_vigencia', models.DateField(blank=True, null=True)),
                ('timestamp', models.DateTimeField()),
                ('assunto', models.ForeignKey(to='norma.AssuntoNorma')),
                ('materia', models.ForeignKey(blank=True, null=True, to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name_plural': 'Normas Jurídicas',
                'verbose_name': 'Norma Jurídica',
            },
        ),
        migrations.CreateModel(
            name='TipoNormaJuridica',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('equivalente_lexml', models.CharField(blank=True, max_length=50, null=True, verbose_name='Equivalente LexML', choices=[('constituicao', 'constituicao'), ('ementa.constitucional', 'ementa.constitucional'), ('lei.complementar', 'lei.complementar'), ('lei.delegada', 'lei.delegada'), ('lei', 'lei'), ('decreto.lei', 'decreto.lei'), ('medida.provisoria', 'medida.provisoria'), ('decreto', 'decreto'), ('lei.organica', 'lei.organica'), ('emenda.lei.organica', 'emenda.lei.organica'), ('decreto.legislativo', 'decreto.legislativo'), ('resolucao', 'resolucao'), ('regimento.interno', 'regimento.interno')])),
                ('sigla', models.CharField(max_length=3, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Norma Jurídica',
                'verbose_name': 'Tipo de Norma Jurídica',
            },
        ),
        migrations.CreateModel(
            name='VinculoNormaJuridica',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('tipo_vinculo', models.CharField(blank=True, max_length=1, null=True, choices=[('A', 'Altera a norma'), ('R', 'Revoga a norma'), ('P', 'Revoga parcialmente a norma'), ('T', 'Revoga por consolidação a norma'), ('C', 'Norma correlata'), ('I', 'Suspende a execução da norma'), ('G', 'Regulamenta a norma')])),
                ('norma_referente', models.ForeignKey(to='norma.NormaJuridica', related_name='+')),
                ('norma_referida', models.ForeignKey(to='norma.NormaJuridica', related_name='+')),
            ],
            options={
                'verbose_name_plural': 'Vínculos entre Normas Jurídicas',
                'verbose_name': 'Vínculo entre Normas Jurídicas',
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
