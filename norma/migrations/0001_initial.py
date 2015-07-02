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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_assunto', models.CharField(max_length=50, verbose_name='Assunto')),
                ('descricao_estendida', models.CharField(max_length=250, null=True, verbose_name='Descri\xe7\xe3o', blank=True)),
            ],
            options={
                'verbose_name': 'Assunto de Norma',
                'verbose_name_plural': 'Assuntos de Norma',
            },
        ),
        migrations.CreateModel(
            name='LegislacaoCitada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_disposicoes', models.CharField(max_length=15, null=True, verbose_name='Disposi\xe7\xe3o', blank=True)),
                ('descricao_parte', models.CharField(max_length=8, null=True, verbose_name='Parte', blank=True)),
                ('descricao_livro', models.CharField(max_length=7, null=True, verbose_name='Livro', blank=True)),
                ('descricao_titulo', models.CharField(max_length=7, null=True, verbose_name='T\xedtulo', blank=True)),
                ('descricao_capitulo', models.CharField(max_length=7, null=True, verbose_name='Cap\xedtulo', blank=True)),
                ('descricao_secao', models.CharField(max_length=7, null=True, verbose_name='Se\xe7\xe3o', blank=True)),
                ('descricao_subsecao', models.CharField(max_length=7, null=True, verbose_name='Subse\xe7\xe3o', blank=True)),
                ('descricao_artigo', models.CharField(max_length=4, null=True, verbose_name='Artigo', blank=True)),
                ('descricao_paragrafo', models.CharField(max_length=3, null=True, verbose_name='Par\xe1grafo', blank=True)),
                ('descricao_inciso', models.CharField(max_length=10, null=True, verbose_name='Inciso', blank=True)),
                ('descricao_alinea', models.CharField(max_length=3, null=True, verbose_name='Al\xednea', blank=True)),
                ('descricao_item', models.CharField(max_length=3, null=True, verbose_name='Item', blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Mat\xe9ria Legislativa',
                'verbose_name_plural': 'Mat\xe9rias Legislativas',
            },
        ),
        migrations.CreateModel(
            name='NormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_norma', models.IntegerField(verbose_name='N\xfamero')),
                ('ano_norma', models.SmallIntegerField(verbose_name='Ano')),
                ('tipo_esfera_federacao', models.CharField(max_length=1, verbose_name='Esfera Federa\xe7\xe3o')),
                ('data_norma', models.DateField(null=True, verbose_name='Data', blank=True)),
                ('data_publicacao', models.DateField(null=True, verbose_name='Data Publica\xe7\xe3o', blank=True)),
                ('descricao_veiculo_publicacao', models.CharField(max_length=30, null=True, verbose_name='Ve\xedculo Publica\xe7\xe3o', blank=True)),
                ('numero_pag_inicio_publ', models.IntegerField(null=True, verbose_name='Pg. In\xedcio', blank=True)),
                ('numero_pag_fim_publ', models.IntegerField(null=True, verbose_name='Pg. Fim', blank=True)),
                ('txt_ementa', models.TextField(verbose_name='Ementa')),
                ('txt_indexacao', models.TextField(null=True, verbose_name='Indexa\xe7\xe3o', blank=True)),
                ('txt_observacao', models.TextField(null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('complemento', models.NullBooleanField(verbose_name='Complementar ?')),
                ('data_vigencia', models.DateField(null=True, blank=True)),
                ('timestamp', models.DateTimeField()),
                ('assunto', models.ForeignKey(to='norma.AssuntoNorma')),
                ('materia', models.ForeignKey(blank=True, to='materia.MateriaLegislativa', null=True)),
            ],
            options={
                'verbose_name': 'Norma Jur\xeddica',
                'verbose_name_plural': 'Normas Jur\xeddicas',
            },
        ),
        migrations.CreateModel(
            name='TipoNormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('voc_lexml', models.CharField(max_length=50, null=True, verbose_name='Equivalente LexML', blank=True)),
                ('sigla_tipo_norma', models.CharField(max_length=3, verbose_name='Sigla')),
                ('descricao_tipo_norma', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o')),
            ],
            options={
                'verbose_name': 'Tipo de Norma Jur\xeddica',
                'verbose_name_plural': 'Tipos de Norma Jur\xeddica',
            },
        ),
        migrations.CreateModel(
            name='VinculoNormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_vinculo', models.CharField(max_length=1, null=True, blank=True)),
                ('norma_referente', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
                ('norma_referida', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
            ],
            options={
                'verbose_name': 'V\xednculo entre Normas Jur\xeddicas',
                'verbose_name_plural': 'V\xednculos entre Normas Jur\xeddicas',
            },
        ),
        migrations.AddField(
            model_name='normajuridica',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo', to='norma.TipoNormaJuridica'),
        ),
        migrations.AddField(
            model_name='legislacaocitada',
            name='norma',
            field=models.ForeignKey(to='norma.NormaJuridica'),
        ),
    ]
